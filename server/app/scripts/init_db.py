"""Create the SQLite database. --reset drops all tables first (projects, scripts, renders)."""

import argparse

from app.config import get_settings
from app.db import init_db


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="drop all data first")
    args = parser.parse_args()
    init_db(reset=args.reset)
    print(f"Database ready: {get_settings().db_url}")


if __name__ == "__main__":
    main()
