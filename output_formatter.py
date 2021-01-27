#
# Copyright 2019 Sony Mobile Communications Inc.
# SPDX-License-Identifier: MIT
#
"""
Format cached Gerrit structure in an:
- html appropriate for email display.
- json appropriate for debug
"""
import json


class OutputFormatter:
    """
    See file docstring.
    """

    _CSS = """\
<style type="text/css">
{}
</style>
"""

    _HEADER = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC
    "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html lang="en" xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{} digest</title>
"""

    _BODY_START = """\
</head>
<body>
    <h1>{} Gerrit digest</h1>
"""
    _BODY_END = """\
</body>
</html>
"""

    def __init__(self, cache, project, anchor, css, filters):
        self._project = project
        self._cache = cache
        self._anchor = anchor
        self._css = css
        self._filters = filters

    def _filter_cache(self):
        tree = []
        for (title, predicate) in self._filters:
            node = []
            matches = self._cache.get_by_predicate(predicate)
            for project in {x["project"] for x in matches}:
                node.append((project, [x for x in matches if x["project"] == project]))
            tree.append((title, node))
        return tree

    def _format_body(self):
        tree = self._filter_cache()
        if not tree:
            raise Exception("No content")

        html = ""
        for (title, node) in sorted(tree):
            html += f"<h2>{str(title)}</h2>\n"
            html += "<ul>\n"
            if not node:
                html += "<li>No changes</li>\n"
            else:
                for (project, changes) in sorted(node):
                    html += f"<li>{str(project)}\n"
                    html += "<ul>\n"
                    for change in sorted(changes, key=lambda x: x["number"]):

                        def _format_size(chgs):
                            (insertions, deletions) = chgs
                            if insertions > 0 and deletions > 0:
                                out = f"(+{insertions},&nbsp;-{deletions})"
                            elif insertions > 0:
                                out = f"(+{insertions})"
                            elif deletions > 0:
                                out = f"(-{deletions})"
                            else:
                                out = ""
                            return out

                        number = str(change["number"])
                        size = _format_size(change["size"])
                        author = str(change["author"]["name"]).replace(" ", "&nbsp;")
                        email = str(change["author"]["email"])
                        subject = str(change["subject"])
                        html += "<li>"
                        html += f"<a href='{self._anchor}{number}'>{number}</a>"
                        html += f" {subject} {size} {author} &lt;{email}&gt;</li>\n"
                    html += "</ul>\n"
                    html += "</li>\n"
            html += "</ul>\n"
        return html

    def format_html(self):
        """
        Return a simple html for the body of report. Response from
        Gerrit acquired from the cached json is munged into an html.
        """

        return (
            self._HEADER.format(self._project)
            + self._CSS.format(self._css)
            + self._BODY_START.format(self._project)
            + self._format_body()
            + self._BODY_END
        )

    def format_json(self):
        """
        Return a json representation of underlying cache.
        """

        tree = self._filter_cache()
        if not tree:
            return json.dumps(dict(), indent=4, sort_keys=True)
        return json.dumps(dict(tree), indent=4, sort_keys=True)
