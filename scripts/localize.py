# To commit your changes to vcs, run with the --commit-vcs argument
# localize.py --commit-vcs

# For a list of command-line options, run with --help or -h

import logging
import os
import sys

logger = logging.getLogger("extensis.burton.script")
sh = logging.StreamHandler(sys.stdout)
sh.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(sh)

if sys.hexversion < 0x02070000:
    logger.error("Python 2.7 or grater is required to run burton.")
    exit(1)

root_path = os.getcwd()
if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
    root_path = sys.argv[1]

burton_path = os.path.join(
    os.path.abspath(os.path.dirname(sys.argv[0])), "..", "..", "burton"
)

if not os.path.isdir(burton_path):
    logger.error("The burton repository does not exist at " + burton_path)
    logger.error("Please clone burton to this path.")
    sys.exit(1)

sys.path.insert(0, burton_path)

requirements = ["chardet", "lxml"]

missing_requirements = []

try:
    for requirement in requirements:
        __import__(requirement)

except ImportError:
    import subprocess
    import time

    logger.error("Installing missing dependencies")

    current_dir = os.getcwd()
    os.chdir(root_path)

    return_code = subprocess.call([
        sys.executable,
        "setup.py",
        "install"
    ])

    os.chdir(current_dir)

    if return_code == 0:
        logger.error("Finished installing dependencies")
        logger.error("Run this script again to run localization")

    else:
        logger.error("Unable to install dependencies")
        logger.error("This is most likely a permissions problem")
        logger.error("Please try running again with administrator privileges")
        logger.error("The exact error(s) are detailed in the output above")

    exit(1)

import burton

burton.run()

