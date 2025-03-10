import argparse
import os
import sys

import serial
from serial.tools.list_ports import comports

BAUD = 4800


def make_header(name, size):
    """Makes a 16-byte packet: [SOH][filename(12,padded)][size(2)][chk]"""
    name, ext = os.path.splitext(name)
    packet = bytes((name[:8] + ext[:4]).ljust(12, "\0"), "ascii")
    packet += size.to_bytes(4, "little")
    return packet


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sends a file over the serial port.")
    parser.add_argument("-s", "--serialport")
    parser.add_argument("path", help="path to the file to send")
    args = parser.parse_args()

    port = (
        args.serialport
        if args.serialport
        else next(p for p in comports() if "USB" in p.hwid).device
    )

    with serial.Serial(port, baudrate=BAUD, timeout=1.0, rtscts=True) as serial:
        print("Opened port {}".format(serial.name))

        filesize = os.stat(args.path).st_size

        with open(args.path, "rb") as file:
            print("Sending file '{}' ({} bytes)...".format(args.path, filesize))

            packet = make_header(os.path.basename(args.path), filesize)
            serial.write(bytes(packet))

            totalsent = 0

            while file.peek():
                buf = file.read(255)
                serial.write(buf)
                totalsent += len(buf)
                print(f"{totalsent} ({round(file.tell() / filesize * 100)} %)")
