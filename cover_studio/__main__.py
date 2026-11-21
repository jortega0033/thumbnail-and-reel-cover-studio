"""Command line entry point: python -m cover_studio --data-dir DIR."""

import argparse
import sqlite3
import sys

from .server import create_server


def _port(text):
    value = int(text)
    if not 0 <= value <= 65535:
        raise argparse.ArgumentTypeError("port must be 0-65535")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(prog="cover_studio")
    parser.add_argument("--data-dir", required=True,
                        help="directory for the SQLite database")
    parser.add_argument("--port", type=_port, default=8765,
                        help="TCP port on 127.0.0.1 (0 picks a free port)")
    args = parser.parse_args(argv)
    try:
        server = create_server(args.data_dir, args.port)
    except (sqlite3.DatabaseError, OSError) as exc:
        print(f"cover_studio: cannot start: {exc}", file=sys.stderr)
        return 2
    print(f"Listening on http://127.0.0.1:{server.server_address[1]}",
          flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
