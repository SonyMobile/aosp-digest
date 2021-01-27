#
# Copyright 2019 Sony Mobile Communications Inc.
# SPDX-License-Identifier: MIT
#
"""
Users of aosp-digest are the recipients of the Gerrit digest. They are represented
in `users/<user>.py` files with the following constants:
 - EMAIL = email address of the recipient
 - FILTERS = list of filters over cached changes. Filter consists of pairs
    (title, predicate), where:
      - title = string representing section title of the filtered cache content
      - predicate = boolean function used to filter the cache content
In order to expose these constants, load specified user configuration as a module.
"""
import importlib.util
import os

import tinycss2


def load_user(user):
    """
    Load user config and custom css file and return as a tuple.
    """
    return _load_config(user), _load_css(user)


def _load_config(user):
    """
    Loads a python file 'users/user.py' and exposes its members
    through a module object.
    """
    modspec = importlib.util.spec_from_file_location(
        "config", os.path.join("users", user + ".py")
    )
    config = importlib.util.module_from_spec(modspec)
    modspec.loader.exec_module(config)
    return config


def _load_css(user):
    """
    Loads default.css and user.css style sheets, and merges them into a
    complete css  like this:
    - if a css node exists in both, the one defined in user.css is taken
      into resulting style sheet
    - if a css node exists in only one of the sheets, it is taken into
      resulting style sheet
    """
    css_default = None
    css_user = None

    try:
        with open(os.path.join("users", "default.css"), "rb") as css_file:
            css_default = css_file.read()
    except OSError:
        pass

    try:
        with open(os.path.join("users", user + ".css"), "rb") as css_file:
            css_user = css_file.read()
    except OSError:
        pass

    if not css_default and not css_user:
        return ""

    rules = dict()
    if css_default:
        rules_default, _ = tinycss2.parse_stylesheet_bytes(
            css_default, skip_whitespace=True, skip_comments=True
        )
        for rule in rules_default:
            if rule.type == "qualified-rule":
                rules[str(rule.prelude)] = rule

    if css_user:
        rules_user, _ = tinycss2.parse_stylesheet_bytes(
            css_user, skip_whitespace=True, skip_comments=True
        )
        for rule in rules_user:
            if rule.type == "qualified-rule":
                rules[str(rule.prelude)] = rule

    css = ""
    for rule in rules.values():
        css += f"\n{rule.serialize()}"

    return css
