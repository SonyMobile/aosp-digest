#!/usr/bin/env python
import datetime
import gerrit
import getopt
import imp
import logging
import os
import subprocess
import sys

class Recipient:
    def __init__(self, email, filters):
        self._email = email
        self._filters = filters

    def _send_email(self, html):
        td = datetime.datetime.now()
        subject = 'AOSP Gerrit digest %s' % td.strftime('%A %d %B %Y')
        argv = ['mutt', '-F', 'muttrc', '-e', 'set content_type=text/html', '-s', subject, self._email]
        proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout, stderr) = proc.communicate(html.encode('utf-8'))
        if proc.returncode != 0:
            raise Exception('failed to send mail: ' + stderr)

    def send_email(self, cache, dry_run):
        if len(self._filters) == 0:
            raise Exception('recipient "%s" has no filters' % self._email)

        contents = gerrit.format_html(cache, self._filters)
        if dry_run:
            logging.info(self._email)
            logging.info(gerrit.format_json(cache, self._filters))
            logging.info(contents)

        if dry_run or len(contents) == 0:
            return

        html = u''

        html += u'<?xml version="1.0" encoding="UTF-8"?>\n'
        html += u'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
        html += u'<html lang="en" xmlns="http://www.w3.org/1999/xhtml">\n'
        html += u'<head>\n'
        html += u'<title>AOSP digest</title>\n'
        html += gerrit.format_css()
        html += u'</head>\n'
        html += u'<body>\n'
        html += contents
        html += u'</body>\n'
        html += u'</html>'

        self._send_email(html)

def main():
    dry_run = False
    users = set()
    logging.basicConfig(format='%(message)s', level=logging.INFO)

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'adu:', ['all-users', 'dry-run', 'user='])
    except getopt.GetoptError as err:
        logging.error(str(err))
        sys.exit(1)

    for o, a in opts:
        if o in ('-a', '--all-users'):
            for path in [x for x in os.listdir('users') if x.endswith('.py')]:
                users.add(path[:-3])
        elif o in ('-d', '--debug'):
            dry_run = True
        elif o in ('-u', '--user'):
            users.add(a)
        else:
            assert False, 'unexpected option %s' % o

    cache = gerrit.read_cache('cache.gz')
    cache = [c for c in cache if gerrit.filter_date_cached_today(c)] # only consider newly cached entries

    for user in users:
        try:
            config = imp.load_source('config', 'users/' + user + '.py')
            r = Recipient(config.email, config.filters)
            r.send_email(cache, dry_run)
        except IOError as err:
            logging.error("Could not send email for user %s: %s", user, str(err))

if __name__ == '__main__':
    main()
