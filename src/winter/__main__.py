# Importing main from cli.py. This file contains no logic of its own; it only
# connects "python -m winter" to the main() function we already wrote.
from winter.cli import main

# Python runs this file when you type: python -m winter
# main() returns an exit code (0, 1 or 2). SystemExit hands that number to the
# operating system, so scripts and shells can tell success from failure.
raise SystemExit(main())
