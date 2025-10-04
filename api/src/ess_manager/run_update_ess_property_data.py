#!/usr/bin/env python3
import argparse
import datetime
import logging
import db_converter.logger.logger as lg
import urllib3


import db_converter.services.config_service as config_service

import ess_manager.update_ess_property_data as importer

def main():
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    logging.getLogger("urllib3").propagate = False
    urllib3.disable_warnings()

    parser = argparse.ArgumentParser(description="Export data from Rally into CSV file(s)")
    parser.add_argument(
        "-e", "--environment", help="Rally environment, section must exist in configuration file.", default="DEFAULT"
    )
    parser.add_argument(
        "-c",
        "--config",
        help="Configuration file in INI format. See `Rally exporter parameters.md` for details.",
        default="config.ini",
    )
    args = parser.parse_args()
    config = config_service.ConfigService(args.config, args.environment)
    log_time = datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    lg.logger(
        fileName="rally-" + log_time + ".log",
        level=config.log_level,
        format="%(asctime)s\t%(levelname)s\t%(threadName)s" "\t[%(filename)s.%(funcName)s:%(lineno)d]\t%(message)s",
    )
    importerService = importer.EssUpdater(config)
    importerService.update_property()


if __name__ == "__main__":
    main()
