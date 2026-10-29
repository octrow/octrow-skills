"""``python -m <pkg>.gui`` and the ``<app>-gui`` script; a frozen build starts here too."""

import sys

from .app import main

if __name__ == "__main__":
    sys.exit(main())
