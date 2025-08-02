#!/usr/bin/env python3

import argparse
import asyncio
import logging
import sys
from custom_components.network_serial_port.network_serial_process import NetworkSerialPortConfiguration, NetworkSerialProcess  # type: ignore



def on_connection_change():
    print("on_connection_change callback")

async def on_process_lost():
    print("on_process_lost callback.")

parser = argparse.ArgumentParser(description="Network Serial Port Process")
parser.add_argument("serial_url", help="Serial port url")
parser.add_argument("port", type=int, help="TCP port")
parser.add_argument("--baudrate", type=int, default=115200, help="Baudrate")
parser.add_argument(
    "--loglevel",
    choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    default="INFO",
    help="Define loglevel, default is INFO.",
)

args = parser.parse_args()

logging.basicConfig(level=args.loglevel)

config = NetworkSerialPortConfiguration(
    url=args.serial_url,
    baudrate=args.baudrate,
    localport=args.port,
)

async def main():
    process = NetworkSerialProcess(
        config,
        on_connection_change=on_connection_change,
        on_process_lost=on_process_lost,
    )
    started = await process.start()
    if not started:
        print("Failed to start process.")
        sys.exit(1)
    print("Process started. Press Ctrl+C to stop.")
    try:
        while True:
            await asyncio.sleep(1)
            if not process.is_running:
                print("Process is not running anymore, so exit.")
                break
    except KeyboardInterrupt:
        print("Stopping process...")
        await process.stop()

asyncio.run(main())