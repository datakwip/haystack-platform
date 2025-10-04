import configparser
import logging

log = logging.getLogger(__name__)

_UNSET = object()


class RawConfigParserExt(configparser.RawConfigParser):
    def __init__(self):
        super().__init__()

    def _convert_to_list(self, value):
        """Return a list value translating from other types if necessary."""
        return sorted([v.strip() for v in value.strip().split(",")])

    def getlist(self, section, option, *, raw=False, vars=None, fallback=_UNSET, **kwargs):
        return self._get_conv(section, option, self._convert_to_list, raw=raw, vars=vars, fallback=fallback, **kwargs)


class ConfigService:
    def __init__(self, file_path, domain):
        config = RawConfigParserExt()
        config.read(file_path)
        domain = str.upper(domain)

        # Required
        self.db_host = config.get(domain, "db_host")
        self.db_port = config.get(domain, "db_port")
        self.db_username = config.get(domain, "db_username")
        self.db_password = config.get(domain, "db_password")
        self.db_name = config.get(domain, "db_name")
        self.db_target_host = config.get(domain, "db_target_host")
        self.db_target_port = config.get(domain, "db_target_port")
        self.db_target_username = config.get(domain, "db_target_username")
        self.db_target_password = config.get(domain, "db_target_password")
        self.db_target_name = config.get(domain, "db_target_name")
        self.file_name = config.get(domain, "file_name")
        self.threads = int(config.get(domain, "threads", fallback="5"))
        self.log_level = config.get(domain, "log_level", fallback="INFO")

    def getDbHost(self):
        return self.db_host

    def getDbUsername(self):
        return self.db_username

    def getDbPort(self):
        return self.db_port

    def getDbPassword(self):
        return self.db_password

    def getDbName(self):
        return self.db_name

    def getTargetDbHost(self):
        return self.db_target_host

    def getTargetDbUsername(self):
        return self.db_target_username

    def getTargetDbPort(self):
        return self.db_target_port

    def getTargetDbPassword(self):
        return self.db_target_password

    def getTargetDbName(self):
        return self.db_target_name


    def getLogLevel(self):
        return self.log_level

    def getFileName(self):
        return self.file_name

    def getThreads(self):
        return self.threads
