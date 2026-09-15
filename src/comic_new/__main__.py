"""Module execution entrypoint for python -m comic_new."""

import sys
from comic_new.cli import main

if __name__ == "__main__":
    sys.exit(main())
