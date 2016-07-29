import os
import sys

root_path = os.getcwd()

burton_path = os.path.join(
    os.path.abspath(os.path.dirname(sys.argv[0])), "..", "burton"
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

burton.setup_default_logger()
conf = burton.Config()
if not (conf.parse_command_line_options(sys.argv[0], sys.argv[1:]) and \
   conf.parse_config_file_for_next_platform()):
    exit(0)

should_use_vcs = conf.get(burton.Config.use_vcs)
vcs_class      = burton.vcs.Git()

for filename in os.listdir("."):
    if filename.endswith(".xlf"):
        import_filename = os.path.join("import", filename)
        if os.path.exists(import_filename):
            language = filename.split(".")[0]

            xlf = burton.translation.XLF(
                language,
                conf.get(burton.Config.language_codes)[language],
                conf.get(burton.Config.language_codes)
                    [conf.get(burton.Config.native_language)],
                "Extensis",
                "Extensis Universal Type Client.app",
                "ewood@extensis.com"
            )

            fh = open(filename, "r")
            xlf.read(fh)
            fh.close()

            fh = open(import_filename, "r")
            xlf.read(fh)
            fh.close()

            if should_use_vcs:
                vcs_class.add_file(filename)
                vcs_class.mark_file_for_edit(filename)

            fh = open(filename, "w")
            xlf.write(fh)
            fh.close()
