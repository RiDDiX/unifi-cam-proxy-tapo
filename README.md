[![unifi-cam-proxy Discord](https://img.shields.io/discord/937237037466124330?color=0559C9&label=Discord&logo=discord&logoColor=FFFFFF&style=for-the-badge)](https://discord.gg/Bxk9uGT6MW)

# UniFi Camera Proxy

## About This Project

UniFi Camera Proxy allows the integration of non-Ubiquiti cameras within the UniFi Protect ecosystem. This solution is ideal for incorporating RTSP-enabled cameras, such as Tapo cameras, into the same user interface and mobile application used for other UniFi devices.

### Features

- **Live Streaming**: Stream video feeds live.
- **Full-time Recording**: Capture and store video footage continuously.
- **Motion Detection**: Supports motion detection with compatible cameras.
- **Smart Detections**: Utilize smart detection features with integration of [Frigate](https://github.com/blakeblackshear/frigate).

## Getting Started

To use a Tapo camera with the UniFi Camera Proxy, you need to configure the proxy with specific parameters. Below is an example command that demonstrates how to set up a Tapo camera:

________________________________________
unifi-cam-proxy --verbose --model '{MODEL}' --ip "{IP-CAM}" --host {IP-UNVR} --mac '{MAC}' --cert /client.pem --token '{UNVR-TOKEN}' tapo --username="{RTSP-ADMIN}" --password="{RTSP-PASSWORD}" --rtsp 'rtsp://{RTSP-ADMIN}:{RTSP-PASSWORD}@{IP-CAM}:554' --ffmpeg-args='-c:a copy -c:v copy -bsf:v "h264_metadata=tick_rate=15000/1001"'
________________________________________

```bash
unifi-cam-proxy --verbose --model '{MODEL}' --ip "{IP-CAM}" --host {IP-UNVR} --mac '{MAC}' --cert /client.pem --token '{UNVR-TOKEN}' tapo --username="{RTSP-ADMIN}" --password="{RTSP-PASSWORD}" --rtsp 'rtsp://{RTSP-ADMIN}:{RTSP-PASSWORD}@{IP-CAM}:554' --ffmpeg-args='-c:a copy -c:v copy -bsf:v "h264_metadata=tick_rate=15000/1001"'

Parameters Explained

    --verbose: Enable verbose output for debugging.
    --model: Specify the model of your camera.
    --ip "{IP-CAM}": The IP address of your Tapo camera.
    --host {IP-UNVR}: The IP address of your UniFi Network Video Recorder.
    --mac '{MAC}': The MAC address of your camera.
    --cert: The path to your client certificate.
    --token '{UNVR-TOKEN}': Your UniFi NVR's token.
    --username and --password: Credentials for RTSP access.
    --rtsp: Complete RTSP URL.
    --ffmpeg-args: Additional arguments for FFmpeg processing.

Documentation

For detailed documentation and additional configuration options, visit UniFi Cam Proxy Documentation.
Support and Contributions

If you encounter issues or have suggestions, please join our Discord community. Your feedback is invaluable to the improvement of this project.
Donations

Support the development of UniFi Camera Proxy by donating through GitHub Sponsors. Your support is greatly appreciated!

css


This version provides clear guidance on how to configure the UniFi Camera Proxy for Tapo cameras and organizes the content to enhance readability and accessibility. It introduces a section that briefly describes each parameter used in the command, making it easier for users to understand and adjust the configuration to fit their setup.
