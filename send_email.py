#!/usr/bin/env python3
"""
Use mutt to send an email with an html body to a list of users -- OR --
dump the intermediate jsons (intended for emails) for debugging.
"""
import datetime
import getopt
import gnupg
import imp
import logging
import os
import subprocess
import sys

import gerrit

class Recipient:
    """
    Contains email address and watched projects filters acquired from
    users/email.address.py file.
    """

    def __init__(self, email, filters):
        self._email = email
        self._filters = filters

    def _send_email(self, html, gpg_recipient):
        timenow = datetime.datetime.now()
        home = os.environ["HOME"]
        gpg = gnupg.GPG(gnupghome = home + "/.gnupg/")
        f = open(gpg_recipient + ".gpg", "rb")
        decrypted_data = gpg.decrypt_file(f)
        if not decrypted_data.ok:
            raise Exception('failed to send mail: ' + decrypted_data.stderr)
        f.close()
        var, val = str(decrypted_data).split("=")
        var = var.strip()
        val = val.strip()
        os.putenv(var, val)
        subject = 'AOSP Gerrit digest %s' % timenow.strftime('%A %d %B %Y')
        argv = ['mutt',
                '-F', 'muttrc',
                '-e', 'set content_type=text/html',
                '-s', subject,
                self._email]
        proc = subprocess.Popen(argv,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        (_, stderr) = proc.communicate(html.encode('utf-8'))
        if proc.returncode != 0:
            raise Exception('failed to send mail: ' + stderr.decode('utf-8'))

    def send_email(self, cache, dry_run, gpg_recipient):
        """
        Prepares cache into the email's body and sends an email
        to Recipient's email address -- OR -- if dry_run is set
        to true, dump the json into a log file.
        """

        if not self._filters:
            raise Exception('recipient "%s" has no filters' % self._email)

        contents = gerrit.format_html(cache, self._filters)
        if not contents:
           raise Exception('no content')

        if dry_run:
            logging.info(self._email)
            logging.info(gerrit.format_json(cache, self._filters))
            logging.info(contents)
            return

        html = u''

        html += u'<?xml version="1.0" encoding="UTF-8"?>\n'
        html += u'<!DOCTYPE html PUBLIC '
        html += u'"-//W3C//DTD XHTML 1.0 Strict//EN" '
        html += u'"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
        html += u'<html lang="en" xmlns="http://www.w3.org/1999/xhtml">\n'
        html += u'<head>\n'
        html += u'<title>AOSP digest</title>\n'
        html += gerrit.format_css()
        html += u'</head>\n'
        html += u'<body>\n'
        html += contents
        html += u'</body>\n'
        html += u'</html>'

        self._send_email(html, gpg_recipient)

def main(args):
    """
    Send emails to requested users filed in the users folder (use '-a'
    for all users, or '-u user.address' for specific user) -- OR --
    create a json dump for specified users for debugging purposes.
    """

    dry_run = False
    users = set()
    gpg_recipient = ""
    logging.basicConfig(format='%(message)s', level=logging.INFO)

    try:
        opts, _ = getopt.getopt(args, 'adu:r:', ['all-users', 'dry-run', 'user=', 'rec='])
    except getopt.GetoptError as err:
        logging.error(str(err))
        sys.exit(1)

    for option, val in opts:
        if option in ('-a', '--all-users'):
            for path in [x for x in os.listdir('users') if x.endswith('.py')]:
                users.add(path[:-3])
        elif option in ('-d', '--debug'):
            dry_run = True
        elif option in ('-u', '--user'):
            users.add(val)
        elif option in ('-r', '--rec'):
            gpg_recipient=val
        else:
            assert False, 'unexpected option %s' % option

    cache = gerrit.read_cache('cache.gz')
    # only consider newly cached entries:
    cache = [c for c in cache if gerrit.filter_date_cached_today(c)]

    for user in users:
        try:
            config = imp.load_source('config', 'users/' + user + '.py')
            r = Recipient(config.email, config.filters)
            r.send_email(cache, dry_run, gpg_recipient)
        except IOError as err:
            logging.error("Could not send email for user %s: %s", user, str(err))

if __name__ == '__main__':
    main(sys.argv[1:])
