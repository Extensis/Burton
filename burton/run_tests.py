import logging
import os
import sys

logger = logging.getLogger("extensis.burton.script")
sh = logging.StreamHandler(sys.stdout)
sh.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(sh)

if sys.hexversion < 0x03070000:
    logger.error("Python 3.7 or grater is required to run burton.")
    exit(1)

requirements = ["chardet", "lxml", "coverage", "mock", "nose", "testfixtures"]

try:
    for requirement in requirements:
        print("Importing " + requirement)
        __import__(requirement)

except ImportError:
    import subprocess
    import time

    logger.error("Installing missing dependencies")

    args = ["pip", "install"]
    args.extend(requirements)

    return_code = subprocess.call(args)

    if return_code == 0:
        logger.error("Finished installing dependencies")
        logger.error("Run this script again to run tests")

    else:
        logger.error("Unable to install dependencies")
        logger.error("This is most likely a permissions problem")
        logger.error("Please try running again with administrator privileges")
        logger.error("The exact error(s) are detailed in the output above")

    exit(1)

import nose

sys.path.append('.')
nose.main(exit=True, defaultTest='.', argv=['nosetests', '--all-modules'])
