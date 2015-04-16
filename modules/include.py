# coding=utf-8
"""
include.py - willie module to include secondary configs
Copyright 2015, Matthijs Kooijman <matthijs@stdin.nl>

Permission is hereby granted, free of charge, to anyone obtaining a copy
of this document and accompanying files, to do whatever they want with
them without any restriction, including, but not limited to, copying,
modification and redistribution.

NO WARRANTY OF ANY KIND IS PROVIDED.

---------------
This module allows including additional config files, for example to
apply different permissions to a file containing passwords, or to keep
the configuration in a VCS while keeping passwords out of it.

To use it, put something like this in the main configuration file:

[include]
private = private.cfg

This will load and merge private.cfg into the main configuration.
"""

from willie.module import *
from willie.tools import stderr

def setup(bot):
    if bot.config.has_section('include'):
        # Include any config files specified in the [include] section
        for (_, value) in bot.config.parser.items('include'):
            include(bot, value)

        # Now, delete any previously cached section attributes on the
        # config object
        for section in bot.config.parser.sections():
            if hasattr(bot.config, section):
                delattr(bot.config, section)

def include(bot, filename):
    try:
        with open(filename) as f:
            bot.config.parser.readfp(f, filename)
    except Exception as exc:
        stderr("Failed to read included config file {}: {}".format(filename, exc))

if __name__ == '__main__':
    print(__doc__.strip())
