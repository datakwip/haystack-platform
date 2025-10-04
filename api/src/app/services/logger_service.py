import logging
import pathlib


def logger(fileName=None, console=True, level="INFO", format=None):
    handlers = []
    lev = logging.INFO
    if level in ("TRACE", "CRITICAL"):
        lev = logging.CRITICAL
    if level == "DEBUG":
        lev = logging.DEBUG
    if level == "WARNING":
        lev = logging.WARNING
    if level == "ERROR":
        lev = logging.ERROR

    if console:
        handlers.append(logging.StreamHandler())

    if fileName:
        if not pathlib.Path(fileName).suffix:
            handlers.append(logging.FileHandler("{0}.log".format(fileName)))
        else:
            handlers.append(logging.FileHandler("{0}".format(fileName)))
    lf = (
        "%(asctime)s - %(levelname)s : [%(filename)s.%(funcName)s:%(lineno)d]%(message)s" if not format else str(format)
    )

    logging.basicConfig(format=lf, level=lev, handlers=handlers)

    return logging