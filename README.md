# aosp-digest

Scripts to query AOSP Gerrit for newly merged changes and optionally notify a
list of recipients via mail.


## Intended workflow
Execute "update-cache.py && send-email.py -a" on a recurring basis, e.g. by
using crontab.


## Hacking
- Limit which users receive a mail: "send-email.py --user=firstname.lastname".
  This expects a file users/firstname.lastname.py exists. The --user option may
  be given multiple times.

- Expected content of users/firstname.lastname.py file is:
  email="email@domain"
  filters=[
    (("title", predicate))
  ]]
  where predicate is a regular python function used to filter out the changes.

- Print debug information on stdout instead of sending emails:
  "send-email.py [-a|--user=...] -d".


## .netrc
The Gerrit API used by update-cache.py requires an authenticated login. Add the
following lines to ~/.netrc:

machine android.googlesource.com login USERNAME password PASSWORD
machine android-review.googlesource.com login USERNAME password PASSWORD

The USERNAME/PASSWORD credentials can be obtained as follows:
- log into https://android-review.googlesource.com/ and go to Settings/HTTP Password.
- The page creates an entry for .gitcookies file in the format
  android.googlesource.com	FALSE	/	TRUE	2147483647	o	USERNAME=PASSWORD
- copy/paste the USERNAME and PASSWORD portions to .netrc file

## muttrc
send-email.py uses mutt to send emails. For mutt to pick up the correct settings,
place a local configuration file for mutt (muttrc) here using the appropriate
muttrc*.template file.

## gpg
Sending emails over smtp that requires authentication means that credentials need to
be supplied in order for the mail to be sent. Instead of placing your password in
muttrc file in plain text, use the following encryption scheme using gpg:
- write a file 'pwenc' with the following content:
```
ACCT=<password>
```
- encrypt the 'pwenc' file using gpg as follows:
```
gpg --encrypt --recipient <recipient-id> pwenc --output <recipient-id>.gpg
```
  where <recipient-id> is a string identifying the "recipient" in gpg parlance
  that has a private key to decrypt the resulting encrypted file
- in order to avoid writing the passphrase every time the password needs to be
  decrypted follow these steps:
  - modify $HOME/.gnupg/gpg.conf with the following content:
```
use-agent
pinentry-mode loopback
```
  - modify $HOME/.gnupg/gpg-agent.conf with the following content:
```
allow-loopback-pinentry
```
  - reload gpg-connect agent with the following command in shell
```
gpg-connect-agent reloadagent /bye
```
- decrypt the <recipient-id>.gpg file at least once using:
```
gpg --decrypt
```
- execute `send_email.py -r <recipient-id>`
