#!/usr/bin/env python3
"""
Schedule periodic execution of update_cache and send_email scripts.
This is because gpg batch decription will not work in crontab, due
to gpg sessions being to short.

crontab equivalent:
55 4 * * * cd /warehouse/shelf/oss/aosp-digest/aosp-digest/ && \
   ./update_cache.py && \
   ./send_email.py -a -r <gpg-recipient> > some.log 2>&1

is to run this script with:
./scheduler.py -r <gpg-recipient> > some.log 2>&1
"""
import getopt
import logging
import sys
import time
import schedule

import send_email
import update_cache

def job(r):
    """
    Update the cache and send the email.
    """
    update_cache.main()
    send_email.main(["-a", "-r" + r])

def main():
    """
    Take the parameters and schedule the job.
    """
    gpg_recipient = ""
    logging.basicConfig(format='%(message)s', level=logging.INFO)
    try:
        opts, _ = getopt.getopt(sys.argv[1:], 'r:', ['rec='])
    except getopt.GetoptError as err:
        logging.error(str(err))
        sys.exit(1)

    for option, val in opts:
        if option in ('-r', '--rec'):
            gpg_recipient = val
        else:
            assert False, 'unexpected option %s' % option

    schedule.every().day.at("4:56").do(job, r=gpg_recipient)

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    main()
