#!/usr/bin/env python3
#
# Copyright 2021 Sony Mobile Communications Inc.
# SPDX-License-Identifier: MIT
#
"""
Send an email with an html body to a list of users -- OR --
dump the intermediate jsons (intended for emails) for debugging.
"""
import argparse
import logging
import os
import smtplib
import sys
from datetime import datetime
from email.message import EmailMessage

import gnupg

from cache import Cache
from config import Config
from gerrit import Gerrit
from loader import load_user
from output_formatter import OutputFormatter


class Recipient:
    """
    Contains email address and output formatter object targeting
    given email recipient.
    """

    def __init__(self, email, filters, css):
        self._email = email
        self._css = css
        self._content = None
        self._filters = filters

    def add_content(self, cache, project, url):
        """
        Add OutputFormatter containing cache filtered through
        user's filters.
        """
        self._content = OutputFormatter(cache, project, url, self._css, self._filters)

    def send_email(self, project, smtp_config, gpg_recipient, dry_run):
        """
        - EITHER: send an html email to Recipient using given smtp configuration
                  and gpg_recipient (to get encrypted authentication info)
        - OR: if dry_run is set to true, dump the json into stdout.
        """

        def _subject():
            timenow = datetime.now()
            return f"{project} Gerrit digest {timenow.strftime('%A %d %B %Y')}"

        def _decrypt_auth(gpg_recipient):
            gpg = gnupg.GPG(gnupghome=os.path.join(os.environ["HOME"], ".gnupg"))
            with open(gpg_recipient + ".gpg", "rb") as fgpg:
                decrypted_data = gpg.decrypt_file(fgpg)
                if not decrypted_data.ok:
                    raise Exception(
                        f"failed to send mail: {decrypted_data.stderr}"  # pylint: disable=no-member
                    )
            return str(decrypted_data).strip()

        message = self._content.format_html()
        if dry_run:
            logging.info(self._email)
            logging.info(self._content.format_json())
            logging.info(message)
            return

        msg = EmailMessage()
        msg["Subject"] = _subject()
        msg["From"] = smtp_config.from_address
        msg["To"] = self._email
        msg.set_content(
            "For the list of today's changes in AOSP Gerrit, please turn on HTML."
        )
        msg.add_alternative(message, subtype="html")
        smtp = smtplib.SMTP(smtp_config.url)
        if smtp_config.authentication:
            smtp.ehlo()
            pwd = _decrypt_auth(gpg_recipient)
            smtp.login(smtp_config.uname, pwd)
        smtp.send_message(msg)


class Mailer:
    """
    Collects parameters of the execution call and sends emails
    to individual recipients.
    """

    def __init__(self, params):
        logging.basicConfig(format="%(message)s", level=logging.INFO)

        self._dry_run = params.debug
        self._gpg_recipient = params.gpg_recipient
        self._users = set()
        if params.all:
            for path in [x for x in os.listdir("users") if x.endswith(".py")]:
                self._add_user(path[:-3])
        else:
            if os.path.isfile(os.path.join("users", params.user + ".py")):
                self._add_user(params.user)
            else:
                logging.error("User not found: %s", params.user)

    def _add_user(self, username):
        user, css = load_user(username)
        if user.EMAIL and user.FILTERS and css:
            recipient = Recipient(user.EMAIL, user.FILTERS, css)
            self._users.add(recipient)
        elif not user.EMAIL:
            logging.error("Cannot send email for user %s: No email defined", username)
        elif not user.FILTERS:
            logging.error("Cannot send email for user %s: No filters defined", username)
        elif not css:
            logging.error(
                "Cannot send email for user %s: No formatting defined", username
            )

    def main(self):
        """
        Send emails to requested users filed in the users folder (use '-a'
        for all users, or '-u user.address' for specific user) -- OR --
        create a dump for specified users for debugging purposes.
        """

        conf = Config()
        if conf.smtp.authentication and not self._gpg_recipient:
            logging.error("Cannot send email. SMTP authentication missing.")
            return

        cache = Cache(conf.cache_filename)
        cache.read()
        gerrit = Gerrit(cache, conf.gerrit_url)
        gerrit.get_cached_today()

        for user in self._users:
            try:
                user.add_content(gerrit.cache, conf.project, conf.gerrit_url)
                user.send_email(
                    conf.project, conf.smtp, self._gpg_recipient, self._dry_run
                )
            except IOError as err:
                logging.error("Could not send email for user %s: %s", user, str(err))


if __name__ == "__main__":
    ARGS = argparse.ArgumentParser(
        description="Send an email with latest Gerrit changes to specific user."
    )
    ARGS.add_argument(
        "-d",
        "--debug",
        help="print debug information and don't send email",
        action="store_true",
    )
    ARGS.add_argument(
        "-a",
        "--all",
        help="send emails to all the users in the users folder",
        action="store_true",
    )
    ARGS.add_argument(
        "-u",
        "--user",
        help="specify a user to send an email to",
    )
    ARGS.add_argument(
        "-g",
        "--gpg_recipient",
        help="gnupg recipient of the gpg safe storage",
    )
    PARAMS = ARGS.parse_args()
    if not PARAMS.all and not PARAMS.user:
        ARGS.print_help()
        sys.exit()

    Mailer(PARAMS).main()
