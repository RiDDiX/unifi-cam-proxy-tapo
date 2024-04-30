import argparse
import asyncio
import logging
import sys
from shutil import which

import coloredlogs
from pyunifiprotect import ProtectApiClient

from unifi.cams import (
    DahuaCam,
    FrigateCam,
    HikvisionCam,
    Reolink,
    ReolinkNVRCam,
    RTSPCam,
    TapoCam,
)
from unifi.core import Core
from unifi.version import __version__

# Define a dictionary to map camera types to their corresponding classes.
CAMS = {
    "amcrest": DahuaCam,
    "dahua": DahuaCam,
    "frigate": FrigateCam,
    "hikvision": HikvisionCam,
    "lorex": DahuaCam,
    "reolink": Reolink,
    "reolink_nvr": ReolinkNVRCam,
    "rtsp": RTSPCam,
    "tapo": TapoCam,
}

def parse_args():
    """Set up and parse command line arguments."""
    parser = argparse.ArgumentParser(description="Unifi Camera Proxy")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--host", "-H", required=True, help="NVR IP address and port")
    parser.add_argument("--nvr-username", help="NVR username")
    parser.add_argument("--nvr-password", help="NVR password")
    parser.add_argument("--cert", "-c", default="client.pem", help="Path to client certificate")
    parser.add_argument("--token", "-t", help="Adoption token")
    parser.add_argument("--mac", "-m", default="AABBCCDDEEFF", help="MAC address of the camera")
    parser.add_argument("--ip", "-i", default="192.168.1.10", help="IP address of the camera")
    parser.add_argument("--name", "-n", default="unifi-cam-proxy", help="Name of the camera")
    parser.add_argument("--model", default="UVC G3", choices=[...], help="Model of the camera")
    parser.add_argument("--fw-version", "-f", default="UVC.S2L.v4.23.8.67.0eba6e3.200526.1046", help="Firmware version")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    subparsers = parser.add_subparsers(title="Camera implementations", dest="impl", required=True)
    for name, impl in CAMS.items():
        subparser = subparsers.add_parser(name)
        impl.add_parser(subparser)

    return parser.parse_args()

async def generate_token(args, logger):
    """Generate an adoption token using the Protect API."""
    try:
        protect = ProtectApiClient(args.host, 443, args.nvr_username, args.nvr_password, verify_ssl=False)
        await protect.update()
        response = await protect.api_request("cameras/manage-payload")
        return response["mgmt"]["token"]
    except Exception:
        logger.exception("Failed to fetch token, please check the documentation.")
        return None
    finally:
        await protect.close_session()

async def run():
    """Initialize and run the camera proxy."""
    args = parse_args()
    camera_class = CAMS[args.impl]
    core_logger = logging.getLogger("Core")
    camera_logger = logging.getLogger(camera_class.__name__)

    logging_level = logging.DEBUG if args.verbose else logging.INFO
    coloredlogs.install(level=logging_level)

    for binary in ["ffmpeg", "nc"]:
        if which(binary) is None:
            core_logger.error(f"{binary} is not installed.")
            sys.exit(1)

    if not args.token:
        args.token = await generate_token(args, core_logger)
        if not args.token:
            core_logger.error("Token acquisition failed.")
            sys.exit(1)

    camera_instance = camera_class(args, camera_logger)
    core_instance = Core(args, camera_instance, core_logger)
    await core_instance.run()

def main():
    """Entry point for the script."""
    asyncio.run(run())

if __name__ == "__main__":
    main()
