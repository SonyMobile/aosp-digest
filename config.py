#
# Copyright 2019 Sony Mobile Communications Inc.
# SPDX-License-Identifier: MIT
#
"""
Configuration classes and methods.
Contains only Config class, for the time being.
"""
import yaml


class SmtpConfig:
    """
    Configuration class for email:
    - url = url of the smtp server
    - authentication = True if smtp server requires authentication
    - uname = user name used for authentication on smtp_url
    - from_address = 'From:' email address
    """

    def __init__(self, url, authentication, uname, from_address):
        self.url = url
        self.authentication = authentication
        self.uname = uname
        self.from_address = from_address


class Config:
    """
    Configuration class for runtime parameters:
    - cache = filename of the cache file
    - gerrit = url to the gerrit insance to inspect
    - smtp = SmtpConfig instance
    """

    def __init__(self):
        with open("config.yaml") as fconfig:
            config = yaml.safe_load(fconfig)
            self.cache_filename = config["gerrit"]["cache_filename"]
            self.gerrit_url = config["gerrit"]["url"]
            self.project = config["gerrit"]["project"]
            self.smtp = SmtpConfig(
                config["smtp"]["url"],
                config["smtp"]["authentication"],
                config["smtp"]["uname"],
                config["smtp"]["from"],
            )
