#!/usr/bin/env python3
#
# Copyright 2019 Sony Mobile Communications Inc.
# SPDX-License-Identifier: MIT
#
"""
Fetch changes from a Gerrit server and cache the resulting json in a gzip file.
"""
from cache import Cache
from config import Config
from gerrit import Gerrit


def main():
    """
    See module docstring.
    """

    conf = Config()
    gerrit = Gerrit(Cache(conf.cache_filename), conf.gerrit_url)
    gerrit.update()


if __name__ == "__main__":
    main()
