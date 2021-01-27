#
# Copyright 2019 Sony Mobile Communications Inc.
# SPDX-License-Identifier: MIT
#
"""
Provides actions over cached responses from Gerrit:
- read/write cached json Gerrit response from/to a gzip file
- format cached structure in an html appropriate for email display
"""
import datetime
import json

import requests


class Gerrit:
    """
    See file docstring.
    """

    def __init__(self, cache, url):
        self._url = url
        self.cache = cache

    def _fetch_chunk(self, cmd):
        def _wash_gerrit_reply(dirty):
            if not dirty.startswith(")]}'\n"):
                raise Exception(f"wash_gerrit_reply: malformed input: {dirty}")
            return dirty[5:]

        headers = {
            "Content-Type": "application/json",
            "Accept-Type": "application/json",
        }
        response = requests.get(self._url + cmd, headers=headers)
        clean = _wash_gerrit_reply(response.text)
        return json.loads(clean)

    def _fetch(self, cmd):
        everything = list()
        offset = 0
        while True:
            if offset > 0:
                chunk = self._fetch_chunk(cmd + "&start=" + str(offset))
            else:
                chunk = self._fetch_chunk(cmd)

            if chunk:
                everything += chunk

            if chunk and "_more_changes" in chunk[-1]:
                offset += len(chunk)
            else:
                break

        return everything

    def update(self):
        """
        Fetch the latest changes from Gerrit and update cache.
        """

        def _fetch_change(data):
            if not data["revisions"]:
                # changes of this type can't even be displayed in the Gerrit web UI:
                # let's just ignore them
                return None

            out = dict()
            out["subject"] = data["subject"]
            out["updated"] = data["updated"]
            out["project"] = data["project"]

            revision_keys = list(data["revisions"].keys())
            latest_revision = data["revisions"][revision_keys[-1]]
            out["message"] = latest_revision["commit"]["message"]
            out["files"] = latest_revision["files"]
            out["project"] = data["project"]
            out["number"] = str(data["_number"])

            out["author"] = dict()
            out["author"]["name"] = latest_revision["commit"]["author"]["name"]
            out["author"]["email"] = latest_revision["commit"]["author"]["email"]

            insertions = 0
            deletions = 0
            for fcl in latest_revision["files"]:
                values = latest_revision["files"][fcl]
                if "lines_inserted" in values:
                    insertions += values["lines_inserted"]
                    if "lines_deleted" in values:
                        deletions += values["lines_deleted"]
            out["size"] = (insertions, deletions)
            return out

        self.cache.read()
        numbers = self.cache.filter_key("number")
        timestamps = self.cache.filter_key("updated")
        mini_cache = dict(zip(numbers, timestamps))
        updated_changes = {}
        # Unauthenticated access, using:
        #   url =  'changes/'
        # will cause quota to trigger for anonymous users. Instead,
        # force authenticate access by prepending 'a':
        url = "a/changes/"
        url += "?q=status:merged"
        url += "+-age:5days+"  # note the '-' for previous 5 days
        url += "branch:master"
        url += "&o=LABELS"
        url += "&o=ALL_REVISIONS"
        url += "&o=ALL_COMMITS"
        url += "&o=ALL_FILES"
        for change in self._fetch(url):
            number = str(change["_number"])
            if number not in mini_cache or mini_cache[number] != change["updated"]:
                updated_changes[number] = change

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f") + "000"
        threshold = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime(
            "%Y-%m-%d"
        )

        self.cache.filter_delta(
            "number", updated_changes
        )  # keep old entries without update ...
        self.cache.filter_threshold(
            "updated", threshold
        )  # ... but remove too old entries
        for number in updated_changes:
            change = _fetch_change(updated_changes[number])
            if change is not None:
                change["cached"] = now
                self.cache.append(change)
        self.cache.write()

    def get_cached_today(self):
        """
        Filter Gerrit cache to only the today's changes.
        """

        def _is_today(change):
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            return change["cached"].startswith(today)

        self.cache.filter_predicate(_is_today)


# def filter_projects(change, projects):
#     return change["project"] in projects


# def filter_date_updated(change, date):
#     return change["updated"].startswith(date)


# def filter_date_updated_today(change):
#     return filter_date_updated(change, datetime.datetime.now().strftime("%Y-%m-%d"))


# def filter_author_domain(change, domain):
#     return re.match(f".*@{domain}.*", change["author"]["email"])


# def filter_date_cached_today(change):
#     today = datetime.datetime.now().strftime("%Y-%m-%d")
#     return change["cached"].startswith(today)
