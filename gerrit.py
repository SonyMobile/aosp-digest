"""
Provides actions over cached responses from Gerrit:
- read/write cached json Gerrit response from/to a gzip file
- format cached structure in an html appropriate for email display
"""
import datetime
import gzip
import json
import os
import re

def write_cache(filename, cache):
    """
    Dump json response from Gerrit into a byte sequence encoded with utf-8
    and archive in a gzip file.
    """

    f = gzip.open(filename, 'wb')
    f.write(bytearray(json.dumps(cache, indent=4, sort_keys=True), encoding='utf-8'))
    f.close()

def read_cache(filename):
    """
    Read a gzip file and unpack into a json object.
    """

    if not os.path.exists(filename):
        cache = []
    else:
        f = gzip.open(filename, 'rb')
        cache = json.load(f)
        f.close()
    return cache

def _filter_cache(cache, filters):
    tree = []
    for (title, func) in filters:
        node = []
        matches = [x for x in cache if func(x)]
        for project in set([x['project'] for x in matches]):
            node.append((project, [x for x in matches if x['project'] == project]))
        tree.append((title, node))
    return tree

def format_css():
    """
    Provide a simple style for formatting cache into html.
    """

    return '''\
<style type="text/css">
    h1 {
        font-weight: normal;
        font-size: 323%;
    }
    h2 {
        font-weight: normal;
        font-size: 162%;
    }
    ul li {
        font-style: italic;
    }
    ul ul {
        margin-bottom: 1em;
    }
    ul ul li {
        font-style: normal;
    }
    .navlist {
        margin: 0px;
        padding: 0px;
        padding-bottom: 0.5em;
    }
    .navlist li {
        display: inline;
        list-style-type: none;
        padding-right: 2em;
    }
    .navlist li.inactive {
        color: #aaaaaa;
    }
    #help {
        display: none;
        background-color: #f0f0f0;
        padding: 1em;
        margin-top: 0.5em;
        margin-bottom: 1em;
        border: 1px solid #e0e0e0;
    }
    #help dt {
        margin-top: 1em;
    }
    #help dd {
        margin-top: 0.2em;
    }
</style>
'''

def format_html(cache, filters):
    """
    Provide a simple html for the body of report. Response from
    Gerrit acquired from the cached json is munged into an html.
    """

    tree = _filter_cache(cache, filters)
    html = ''
    for (title, node) in sorted(tree):
        html += '<h2>%s</h2>\n' % str(title)
        html += '<ul>\n'
        if not node:
            html += '<li>No changes</li>\n'
        else:
            for (project, changes) in sorted(node):
                html += '<li>%s\n' % str(project)
                html += '<ul>\n'
                for change in sorted(changes, key=lambda x: x['number']):
                    def _format_size(chgs):
                        (insertions, deletions) = chgs
                        if insertions > 0 and deletions > 0:
                            out = '(+%d,&nbsp;-%d)' % (insertions, deletions)
                        elif insertions > 0:
                            out = '(+%d)' % insertions
                        elif deletions > 0:
                            out = '(-%d)' % deletions
                        else:
                            out = ''
                        return out
                    number = str(change['number'])
                    size = _format_size(change['size'])
                    author = str(change['author']['name']).replace(' ', '&nbsp;')
                    email = str(change['author']['email'])
                    subject = str(change['subject'])
                    html += '<li>'
                    html += '<a href="http://android-review.googlesource.com/%s">%s</a>' % (number,
                                                                                            number)
                    html += ' %s %s %s &lt;%s&gt;</li>\n' % (subject,
                                                             size,
                                                             author,
                                                             email)
                html += '</ul>\n'
                html += '</li>\n'
        html += '</ul>\n'
    return html

def format_json(cache, filters):
    """
    Utility method used to pretty print cached json to
    a debug log.
    """

    tree = _filter_cache(cache, filters)
    if not tree:
        return json.dumps(dict(), indent=4, sort_keys=True)
    return json.dumps(dict(tree), indent=4, sort_keys=True)

def filter_projects(change, projects):
    return change['project'] in projects

def filter_date_updated(change, date):
    return change['updated'].startswith(date)

def filter_date_updated_today(change):
    return filter_date_updated(change, datetime.datetime.now().strftime('%Y-%m-%d'))

def filter_author_sony(change):
    return re.match(r'.*@sony.*', change['author']['email'])

def filter_date_cached_today(change):
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    return change['cached'].startswith(today)
