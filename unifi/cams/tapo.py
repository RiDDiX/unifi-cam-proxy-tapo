import argparse
import logging
import subprocess
import tempfile
from pathlib import Path

from aiohttp import web
from pytapo import Tapo
from unifi.cams.base import UnifiCamBase

class TapoCam(UnifiCamBase):
    def __init__(self, args: argparse.Namespace, logger: logging.Logger):
        super().__init__(args, logger)
        self.snapshot_dir = tempfile.mkdtemp()
        self.snapshot_stream = None
        self.stream_sources = {
            "video1": f"{args.rtsp}/stream1",
            "video2": f"{args.rtsp}/stream1",
            "video3": f"{args.rtsp}/stream2"
        }
        self.ptz_enabled = False
        self.initialize_camera(args)

    def initialize_camera(self, args):
        try:
            self.cam = Tapo(args.ip, args.username, args.password)
            self.cam.getMotorCapability()
            self.ptz_enabled = True
        except AttributeError:
            self.logger.info("PTZ not enabled due to insufficient configuration.")
        except Exception as e:
            self.logger.info(f"PTZ not supported: {e}")

    @classmethod
    def add_parser(cls, parser: argparse.ArgumentParser):
        super().add_parser(parser)
        parser.add_argument("--username", "-u", default="admin", help="Camera username, default 'admin'")
        parser.add_argument("--password", "-p", help="Camera password")
        parser.add_argument("--rtsp", required=True, help="RTSP URL for camera stream")
        parser.add_argument("--http-api", type=int, default=0, help="HTTP API port, disabled by default")
        parser.add_argument("--snapshot-url", "-i", type=str, help="URL for fetching snapshots")

    def start_snapshot_stream(self):
        if not self.snapshot_stream or self.snapshot_stream.poll() is not None:
            command = f"ffmpeg -nostdin -y -re -rtsp_transport tcp -i '{self.stream_sources['video3']}' -r 1 -update 1 {self.snapshot_dir}/screen.jpg"
            self.logger.info(f"Starting snapshot stream with command: {command}")
            self.snapshot_stream = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)

    async def get_snapshot(self) -> Path:
        img_file = Path(self.snapshot_dir, "screen.jpg")
        if self.args.snapshot_url:
            await self.fetch_to_file(self.args.snapshot_url, img_file)
        else:
            self.start_snapshot_stream()
        return img_file

    async def change_video_settings(self, options) -> None:
        if self.ptz_enabled:
            movements = {"brightness": (0, 10), "contrast": (10, 0)}
            for setting, (x, y) in movements.items():
                value = int(options[setting])
                if value < 20:
                    self.logger.info(f"Adjusting {setting}: moving.")
                    self.cam.moveMotor(-x, -y)
                elif value > 80:
                    self.logger.info(f"Adjusting {setting}: moving.")
                    self.cam.moveMotor(x, y)

    async def run(self) -> None:
        if self.ptz_enabled:
            self.logger.debug("PTZ enabled")
        if self.args.http_api:
            self.logger.info(f"HTTP API enabled on port {self.args.http_api}")
            app = web.Application()
            app.add_routes([web.get("/start_motion", self.start_motion), web.get("/stop_motion", self.stop_motion)])
            self.runner = web.AppRunner(app)
            await self.runner.setup()
            site = web.TCPSite(self.runner, port=self.args.http_api)
            await site.start()

    async def start_motion(self, request):
        self.logger.debug("Motion start triggered")
        await self.trigger_motion_start()
        return web.Response(text="ok")

    async def stop_motion(self, request):
        self.logger.debug("Motion stop triggered")
        await self.trigger_motion_stop()
        return web.Response(text="ok")

    async def close(self) -> None:
        await super().close()
        if self.runner:
            await self.runner.cleanup()
        if self.snapshot_stream:
            self.snapshot_stream.kill()

    async def get_stream_source(self, stream_index: str) -> str:
        return self.stream_sources[stream_index]
