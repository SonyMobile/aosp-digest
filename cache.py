#
# Copyright 2019 Sony Mobile Communications Inc.
# SPDX-License-Identifier: MIT
#
"""
Provides actions over cached responses from Gerrit:
- read/write cached json Gerrit response from/to a gzip file
- adding cache lines
- filtering of cache based on given criteria
"""
import gzip
import json
from os import path


class Cache:
    """
    See file docstring.
    """

    def __init__(self, filename):
        self._filename = filename
        self._data = {}

    def read(self):
        """
        Read a gzip file and unpack into a json object.
        """

        if not path.exists(self._filename):
            self._data = []
        else:
            fcache = gzip.open(self._filename, "rb")
            try:
                self._data = json.load(fcache)
            finally:
                fcache.close()

    def write(self):
        """
        Dump json response from Gerrit into a byte sequence encoded with utf-8
        and archive in a gzip file.
        """

        fcache = gzip.open(self._filename, "wb")
        try:
            fcache.write(
                bytearray(
                    json.dumps(self._data, indent=4, sort_keys=True), encoding="utf-8"
                )
            )
        finally:
            fcache.close()

    # pylint: disable=missing-docstring
    def filter_key(self, key):
        return [x[key] for x in self._data]

    def filter_delta(self, key, delta):
        self._data = [x for x in self._data if x[key] not in delta]

    def filter_threshold(self, key, threshold):
        self._data = [x for x in self._data if x[key] > threshold]

    def filter_predicate(self, predicate):
        self._data = [x for x in self._data if predicate(x)]

    def get_by_predicate(self, predicate):
        return [x for x in self._data if predicate(x)]

    def append(self, change):
        self._data.append(change)
