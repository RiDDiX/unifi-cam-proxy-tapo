import asyncio
import ssl

import backoff
import websockets

class RetryableError(Exception):
    """Custom exception for retryable errors within the websocket connection."""
    pass

class Core:
    """Core class for managing websocket connections and interactions with a camera."""

    def __init__(self, args, camera, logger):
        self.host = args.host
        self.token = args.token
        self.mac = args.mac
        self.logger = logger
        self.camera = camera
        self.ssl_context = self.setup_ssl_context(args.cert)

    def setup_ssl_context(self, cert_path):
        """Configure and return SSL context for secure connections."""
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.load_cert_chain(cert_path, cert_path)
        return context

    async def run(self):
        """Main execution method to manage websocket connection and camera tasks."""
        uri = f"wss://{self.host}:7442/camera/1.0/ws?token={self.token}"
        headers = {"camera-mac": self.mac}

        @backoff.on_predicate(
            backoff.expo,
            lambda retryable: retryable,
            factor=2,
            jitter=None,
            max_value=10,
            logger=self.logger,
        )
        async def connect():
            """Attempt to establish websocket connection and handle errors appropriately."""
            self.logger.info(f"Attempting to connect to {uri}")
            try:
                ws = await websockets.connect(
                    uri,
                    extra_headers=headers,
                    ssl=self.ssl_context,
                    subprotocols=["secure_transfer"],
                )
                return await self.manage_camera_tasks(ws)
            except websockets.exceptions.InvalidStatusCode as e:
                return await self.handle_invalid_status(e)
            except (asyncio.TimeoutError, ConnectionRefusedError) as e:
                self.logger.info(f"Connection error: {str(e)}")
                return True  # Trigger a retry

        await connect()

    async def manage_camera_tasks(self, websocket):
        """Handle camera tasks using the established websocket connection."""
        tasks = [
            asyncio.create_task(self.camera._run(websocket)),
            asyncio.create_task(self.camera.run()),
        ]
        try:
            await asyncio.gather(*tasks)
        except RetryableError:
            self.cancel_tasks(tasks)
            return True  # Trigger a retry
        finally:
            await self.camera.close()

    async def handle_invalid_status(self, exception):
        """Log specific errors based on HTTP status codes and handle retries."""
        if exception.status_code == 403:
            self.logger.error("The provided token is invalid. Please generate a new one and try again.")
        elif exception.status_code == 429:
            return True  # Token is rate-limited; trigger a retry
        raise exception

    def cancel_tasks(self, tasks):
        """Cancel all running tasks."""
        for task in tasks:
            if not task.done():
                task.cancel()

