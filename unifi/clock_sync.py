import argparse
import struct
import sys
import time

from flvlib3.astypes import FLVObject
from flvlib3.primitives import make_ui8, make_ui32
from flvlib3.tags import create_script_tag

def read_bytes(source, num_bytes):
    """Reads a specified number of bytes from the input source."""
    buf = b""
    while len(buf) < num_bytes:
        data = source.read(num_bytes - len(buf))
        if data:
            buf += data
        else:
            break
    return buf

def write(data):
    """Writes data to stdout."""
    sys.stdout.buffer.write(data)

def write_log(data):
    """Writes log messages to stderr."""
    sys.stderr.write(f"{data}\n")

def write_timestamp_trailer(packet_type, timestamp):
    """Writes a custom FLV timestamp trailer to stdout."""
    write(make_ui8(0))  # FLV has no type byte
    trailer_content = bytes([1, 95, 144, 0, 0, 0, 0, 0, 0, 0, 0]) if packet_type == 9 else bytes([0, 43, 17, 0, 0, 0, 0, 0, 0, 0, 0])
    write(trailer_content)
    write(make_ui32(int(timestamp * 1000 * 100)))

def main(args):
    """Main function that processes FLV streams and injects synchronization tags."""
    source = sys.stdin.buffer
    validate_flv_header(source)
    manage_flv_stream(source)

def validate_flv_header(source):
    """Validates and writes the FLV file header."""
    header = read_bytes(source, 3)
    if header != b"FLV":
        raise ValueError("Not a valid FLV file")
    write(header + read_bytes(source, 1))
    read_bytes(source, 1)  # Read and ignore one byte
    write(make_ui8(7))  # Custom bitmask for FLV type
    write(read_bytes(source, 4))
    write(read_bytes(source, 4))  # Tag 0 previous size

def manage_flv_stream(source):
    """Continuously reads and manages FLV packets, injecting synchronization tags."""
    last_sync_time = time.time()
    start_time = time.time()

    while True:
        packet_header = read_bytes(source, 12)
        if len(packet_header) != 12:
            write(packet_header)
            break

        packet_type = packet_header[0]
        payload_size = struct.unpack(">BH", packet_header[1:4])
        payload_size = (payload_size[0] << 16) + payload_size[1]
        current_time = time.time()

        # Condition to inject sync packets every 5 seconds
        if current_time - last_sync_time >= 5:
            last_sync_time = current_time
            inject_sync_tags(current_time, start_time, packet_header)

        # Continue handling the rest of the stream normally
        write(packet_header + read_bytes(source, payload_size))
        write(read_bytes(source, 4))  # Write previous packet size
        write_timestamp_trailer(packet_type == 9, current_time - start_time)

def inject_sync_tags(current_time, start_time, packet_header):
    """Injects synchronization tags into the FLV stream."""
    data = create_sync_data(current_time)
    write(create_script_tag("onClockSync", data, current_time))
    write_timestamp_trailer(False, current_time - start_time)
    write(create_script_tag("onMpma", data, 0))
    write_timestamp_trailer(False, current_time - start_time)
    write(packet_header)

def create_sync_data(current_time):
    """Creates data for synchronization tags."""
    data = FLVObject()
    data["cs"] = {"cur": 1500000, "max": 1500000, "min": 32000}
    data["m"] = {"cur": 750000, "max": 1500000, "min": 750000}
    data["r"] = 0
    data["sp"] = {"cur": 1500000, "max": 1500000, "min": 150000}
    data["t"] = 75000.0
    data["streamClock"] = int(current_time)
    data["streamClockBase"] = 0
    data["wallClock"] = current_time * 1000
    return data

def parse_args():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(description="Injects synchronization data into FLV streams.")
    parser.add_argument(
        "--write-timestamps",
        action="store_true",
        help="Enables writing timestamps between packets."
    )
    return parser.parse_args()

if __name__ == "__main__":
    main(parse_args())
