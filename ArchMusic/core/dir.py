import os
import sys
import subprocess
from os import listdir, mkdir

from ..logging import LOGGER


def dirr():
    subprocess.run(["rm", "-rf", "*.session"])
    subprocess.run(["rm", "-rf", "*.session-journal"])

    if "assets" not in listdir():
        LOGGER(__name__).warning("Assets Folder not Found. Please clone repository again.")
        sys.exit()
    for file in os.listdir():
        if file.endswith(".jpg"):
            os.remove(file)
    for file in os.listdir():
        if file.endswith(".jpeg"):
            os.remove(file)
    if "downloads" not in listdir():
        mkdir("downloads")
    if "cache" not in listdir():
        mkdir("cache")
    LOGGER(__name__).info("Directories Updated.")
