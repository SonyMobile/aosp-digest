#!/usr/bin/env python3
"""
Fetch changes from Gerrit using curl and cache the resulting json in a gzip file.
"""
import datetime
import json
import subprocess

import gerrit

def _curl_chunk(cmd):
    def _wash_gerrit_reply(dirty):
        if not dirty.startswith(b')]}\'\n'):
            raise Exception('wash_gerrit_reply: malformed input: ' + dirty)
        return dirty[5:]

    prefix = 'https://android-review.googlesource.com/'
    url = prefix + cmd
    argv = ['curl',
            '--anyauth', '-n',
            '-H', 'Content-Type: application/json',
            '-H', 'Accept-Type: application/json',
            url]
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = proc.communicate()
    if proc.returncode != 0:
        raise Exception('curl: ' + stderr)
    clean = _wash_gerrit_reply(stdout)
    return json.loads(clean)

def _curl(cmd):
    everything = list()
    offset = 0
    while True:
        if offset > 0:
            chunk = _curl_chunk(cmd + '&start=' + str(offset))
        else:
            chunk = _curl_chunk(cmd)
        if chunk:
            everything += chunk

        if chunk and '_more_changes' in chunk[-1]:
            offset += len(chunk)
        else:
            break
    return everything

def _fetch_list_of_new_changes(cache):
    numbers = [x['number'] for x in cache]
    timestamps = [x['updated'] for x in cache]
    mini_cache = dict(zip(numbers, timestamps))
    updated_changes = {}
    # Unauthenticated access like this will cause quota to trigger for anonymous users
    #   url =  'changes/'
    # Instead, force authenticate access:
    url = 'a/changes/'
    url += '?q=status:merged'
    url += '+-age:5days+' # note the '-' for previous 5 days
    url += 'branch:master'
    url += '&o=LABELS'
    url += '&o=ALL_REVISIONS'
    url += '&o=ALL_COMMITS'
    url += '&o=ALL_FILES'
    for change in _curl(url):
        number = str(change['_number'])
        if number not in mini_cache or mini_cache[number] != change['updated']:
            updated_changes[number] = change

    return updated_changes

def _fetch_change(data):
    if not data['revisions']:
        # changes of this type can't even be displayed in the Gerrit web UI:
        # let's just ignore them
        return None

    out = dict()
    out['subject'] = data['subject']
    out['updated'] = data['updated']
    out['project'] = data['project']

    revision_keys = list(data['revisions'].keys())
    latest_revision = data['revisions'][revision_keys[-1]]
    out['message'] = latest_revision['commit']['message']
    out['files'] = latest_revision['files']
    out['project'] = data['project']
    out['number'] = str(data['_number'])

    out['author'] = dict()
    out['author']['name'] = latest_revision['commit']['author']['name']
    out['author']['email'] = latest_revision['commit']['author']['email']

    insertions = 0
    deletions = 0
    for f in latest_revision['files']:
        values = latest_revision['files'][f]
        if 'lines_inserted' in values:
            insertions += values['lines_inserted']
        if 'lines_deleted' in values:
            deletions += values['lines_deleted']
    out['size'] = (insertions, deletions)

    return out

def main():
    """
    See module docstring.
    """

    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f') + '000'
    threshold = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
    cache_filename = 'cache.gz'
    cache = gerrit.read_cache(cache_filename)
    updated = _fetch_list_of_new_changes(cache)
    cache = [x for x in cache if x['number'] not in updated] # keep old entries without update ...
    cache = [x for x in cache if x['updated'] > threshold] # ... but remove too old entries
    for number in updated:
        change = _fetch_change(updated[number])
        if change is not None:
            change['cached'] = now
            cache.append(change)
    gerrit.write_cache(cache_filename, cache)

if __name__ == '__main__':
    main()
