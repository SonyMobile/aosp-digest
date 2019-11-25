import datetime
import gzip
import json
import os
import re

def write_cache(filename, cache):
    f = gzip.open(filename, 'wb')
    f.write(json.dumps(cache, indent=4, sort_keys=True))
    f.close()

def read_cache(filename):
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
    tree = _filter_cache(cache, filters)
    html = u''
    for (title, node) in sorted(tree):
        html += u'<h2>%s</h2>\n' % unicode(title)
        html += u'<ul>\n'
        if not len(node):
            html += '<li>No changes</li>\n'
        else:
            for (project, changes) in sorted(node):
                html += u'<li>%s\n' % unicode(project)
                html += u'<ul>\n'
                for c in sorted(changes, key=lambda x: x['number']):
                    def _format_size((insertions, deletions)):
                        if insertions > 0 and deletions > 0:
                            out = u'(+%d,&nbsp;-%d)' % (insertions, deletions)
                        elif insertions > 0:
                            out = u'(+%d)' % insertions
                        elif deletions > 0:
                            out = u'(-%d)' % deletions
                        else:
                            out = u''
                        return out
                    number = unicode(c['number'])
                    size = _format_size(c['size'])
                    author = unicode(c['author']['name']).replace(' ', '&nbsp;')
                    email = unicode(c['author']['email'])
                    subject = unicode(c['subject'])
                    html += u'<li><a href="http://android-review.googlesource.com/%s">%s</a> %s %s %s &lt;%s&gt;</li>\n' % (number, number, subject, size, author, email)
                html += u'</ul>\n'
                html += u'</li>\n'
        html += u'</ul>\n'
    return html

def format_json(cache, filters):
    tree = _filter_cache(cache, filters)
    if len(tree) == 0:
        return json.dumps(dict(), indent=4, sort_keys=True)
    return json.dumps(dict(tree), indent=4, sort_keys=True)

def filter_projects(c, projects):
    return c['project'] in projects

def filter_date_updated(c, date):
    return c['updated'].startswith(date)

def filter_date_updated_today(c):
    return filter_date_updated(c, datetime.datetime.now().strftime('%Y-%m-%d'))

def filter_author_sony(c):
    return re.match(r'.*@sony.*', c['author']['email'])

def filter_date_cached_today(c):
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    return c['cached'].startswith(today)
