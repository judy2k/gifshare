"""
Allow gifshare to be run as a package with `python -m gifshare <arguments>`
"""

import sys
from . import main

if __name__ == '__main__':
    sys.exit(main())