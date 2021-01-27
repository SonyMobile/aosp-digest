# aosp-digest

Scripts to query a given Gerrit instance for newly merged changes and optionally notify a
list of recipients via email.
Traditionally, targeted Gerrit instance was that of AOSP (https://android-review.googlesource.com/),
hence the name of the tool.

## Intended workflow
- Execute `pip install -r requirements.txt` to setup scripts for usage.

- Execute `update-cache.py && send-email.py -a` on a recurring basis, e.g. by
  using crontab.

## Configuration

### config.yaml
Configure Gerrit and smtp parameters using a `config.yaml` file with the
following content:
```
gerrit:
    project: "name of the project on url, e.g. AOSP, Chromium, Gerrit etc."
    url: "url/of/the/gerrit/server"
    cache_filename: "filename_of_the_cache_file"
smtp:
    url: "url/of/the/smtp/server
    authentication: <True if smtp server requires authentication | False otherwise>
    uname: "user.name.on.smtp.server"
    from: "Email address to user in the 'From:' field of sent email"
```

For the time being the script assumes master branch.

### Users
Users of aosp-digest are the recipients of the Gerrit digest. They are represented
in `users/<user>.py` files with the following constants:
 - EMAIL = email address of the recipient
 - FILTERS = list of filters over cached changes. Filter consists of pairs
    (title, predicate), where:
      - title = string representing section title of the filtered cache content
      - predicate = boolean function used to filter the cache content
        `predicate(c: change) -> bool`, where change is a dictionary of changes
        defined in gerrit.py, and return value is True if the particular change
        satisfies the rule defined in predicate and should be presented under
        the `title`.


These constants are mandatory for the definition of a recipient.

#### Email style customization
As email is being sent as HTML, its style is handled by default.css. In order to
customize the style per user, set values of customizable elements in user's css
file `users/<user>.css`. (This file is not necessary. If missing, then default.css
is used.)

Customizable elements:
- `h1` - customize head of email
- `h2` - customize section title
- `ul` - customize bullet list block
- `ul li`
    - To customize the project title, modify `ul li` element.
      This will set the style for the whole block, so you will
      have to reset in the subsequent `ul li` children.
    - Note that Outlook doesn't render nth-child selector on this element.
- `ul ul` - customize item list child
- `ul ul li`
    - If you customized the `ul li` element, this is where you
      reset the customization if you need to style the individual
      lines of the list.
- `ul ul li a` - link to Gerrit URL

Note:
- `@import` css rule is not respected.
- Css rules are not merged between default and user css files. Instead,
  sheets are merged as follows:
    - if a css node exists in both default and user sheet, the one defined
      in user.css is taken into the resulting style sheet
    - if a css node exists in only one of the sheets, it is taken into
      the resulting style sheet

ie. css nodes defined in both style sheets are taken from the user sheet
and other css nodes are taken verbatim.

### .netrc
The Gerrit API used by update_cache.py requires an authenticated login. Add the
following lines to your `.netrc` file for AOSP Gerrit (or similar for other
Gerrit instances):

```
machine android.googlesource.com login USERNAME password PASSWORD
machine android-review.googlesource.com login USERNAME password PASSWORD
```

The USERNAME/PASSWORD credentials can be obtained as follows:
- log into https://android-review.googlesource.com/ and go to Settings/HTTP Password.
- The page creates an entry for `.gitcookies` file in the format
```
  android.googlesource.com	FALSE	/	TRUE	2147483647	o	USERNAME=PASSWORD
```
- copy/paste the USERNAME and PASSWORD portions to `.netrc` file

### gpg
Sending emails over smtp that requires authentication means that credentials need to
be supplied in order for the mail to be sent. Instead of placing your password in
plain text, use the following encryption scheme using gpg:
- write a file 'pwenc' with the smtp password in it
- encrypt the 'pwenc' file using gpg as follows:
```
gpg --encrypt --output <recipient-id>.gpg --recipient <recipient-id> pwenc
```
  where `<recipient-id>` is a string identifying the "recipient" in gpg parlance
  that has a private key to decrypt the resulting encrypted file.
  - To disambiguate from email reciepient, gpg "recipient" is refered to as
  gpg-recipient.
  - Remove `pwenc` file.
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
- decrypt the <gpg-recipient-id>.gpg file at least once using:
```
gpg --decrypt <gpg-recipient-id>.gpg > /dev/null 2>&1
```
- run:
```
send_email.py -g <gpg-recipient-id>
```

## Usage
### update_cache.py
Calling `update-cache.py` will update the cache in `config.yaml:gerrit.cache_filename`.

### send_email.py
Send an email with latest Gerrit changes to specific user.

```
send_email.py [-h] [-d] [-a] [-u USER] [-g GPG_RECIPIENT]

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           print debug information and don't send email
  -a, --all             send emails to all the users in the users folder
  -u USER, --user USER  specify a user to send an email to
  -g GPG_RECIPIENT, --gpg_recipient GPG_RECIPIENT
                        gnupg recipient of the gpg safe storage
```

## Hacking
- Execute:
  - `pip install -r dev-requirements.txt` to prepare environment for development.
  - `pre-commit install` to install a pre-commit hook to the local .git.

- Limit which users receive a mail: `send-email.py --user=firstname.lastname`.
  This command expects a file `users/firstname.lastname.py` exists. The --user option may
  be given multiple times.

- Print debug information on stdout instead of sending emails:
  `send-email.py [-a|--user=...] -d`.

- When updating imports make sure to update [requirements.txt](requirements.txt) and
  [NOTICE](NOTICE) files.
  (For updated list of licenses run `pylicense requirements.txt`.)

## Contributing
Submit an issue or create a Merge Request.
If it's your first code contribution, please add your name to [AUTHORS](AUTHORS) file in alphabetical order.

## LICENSE
Copyright 2019 Sony Mobile Communications Inc.
The project is licensed under the MIT license.
See [LICENSE](LICENSE) file.
