"""Module entrypoint for `python -m hand_script`."""

import sys

from hand_script.cli import main

if __name__ == "__main__":
    sys.exit(main())
