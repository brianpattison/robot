"""Command-line client for the local robotd Unix socket."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import uuid


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--socket", type=Path, default=Path("/run/robotd/robotd.sock"))
    parser.add_argument("--source", default="robotctl")
    sub = parser.add_subparsers(dest="op", required=True)
    sub.add_parser("status")
    sub.add_parser("stop")
    drive = sub.add_parser("drive")
    drive.add_argument("linear_mm_s", type=int)
    drive.add_argument("angular_mrad_s", type=int)
    head = sub.add_parser("head")
    head.add_argument("pan_cdeg", type=int)
    head.add_argument("tilt_cdeg", type=int)
    clear = sub.add_parser("clear-bumper")
    clear.add_argument("zone_mask", type=lambda value: int(value, 0))
    return parser.parse_args()


async def call(args: argparse.Namespace) -> dict:
    reader, writer = await asyncio.open_unix_connection(str(args.socket))
    request = {"id": uuid.uuid4().hex, "op": args.op.replace("-", "_"), "source": args.source}
    for key in ("linear_mm_s", "angular_mrad_s", "pan_cdeg", "tilt_cdeg", "zone_mask"):
        if hasattr(args, key):
            request[key] = getattr(args, key)
    writer.write((json.dumps(request, separators=(",", ":")) + "\n").encode())
    await writer.drain()
    response = json.loads(await reader.readline())
    writer.close()
    await writer.wait_closed()
    return response


def main() -> None:
    response = asyncio.run(call(parse_args()))
    print(json.dumps(response, indent=2, sort_keys=True))
    if not response.get("ok"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
