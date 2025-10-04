import logging

logger = logging.getLogger(__name__)


class FileService:
    def __init__(self, basePath):
        self.basePath = basePath



    def readFileLineByLine(self, fileName):
        with open(fileName) as file:
            lines = file.readlines()
        return lines

