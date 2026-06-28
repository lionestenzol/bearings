"""Enable `python -m bearings` to run the CLI (mirrors the console_scripts entry)."""
import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
