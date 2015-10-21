# coding=utf-8
"""
factoid.py - willie module for simple factoid keeping
Copyright 2015, Matthijs Kooijman <matthijs@stdin.nl>

Permission is hereby granted, free of charge, to anyone obtaining a copy
of this document and accompanying files, to do whatever they want with
them without any restriction, including, but not limited to, copying,
modification and redistribution.

NO WARRANTY OF ANY KIND IS PROVIDED.

---------------
This module allows remembering simple facts about arbitrary keys. It
supports remembering multiple facts for a single key and facts can be
referred to by multiple keys by using aliases.

To add a fact:

    .foo is a common placeholder in programming
    .examples are necessary for making things clear

    <blathijs> .foo is a common placeholder in programming
    <grobbebol> blathijs: I now know about foo
    <blathijs> .examples are necessary for making things clear
    <grobbebol> blathijs: I now know about examples

To add a second fact for a key:

    <blathijs> .foo is also an acronym for Forward Observational Officer
    <grobbebol> blathijs: I now know more about foo

Quering a fact is done by just using the key as a name:

    <blathijs> .foo
    <grobbebol> blathijs: foo a common placeholder in programming, and also an acronym for Forward Observational Officer

Additionally, a fact can be directed to someone else:

    <blathijs> .tell this_other_guy about foo
    <grobbebol> this_other_guy: foo a common placeholder in programming, and also an acronym for Forward Observational Officer
    <blathijs> .teach this_other_guy about foo
    <grobbebol> this_other_guy: foo a common placeholder in programming, and also an acronym for Forward Observational Officer

You can add aliases:

    <blathijs> .foobar aliases foo
    <grobbebol> blathijs: foobar is now an alias for foo
    <blathijs> .fubar refers to foo
    <grobbebol> blathijs: fubar is now an alias for foo
    <blathijs> .fubar
    <grobbebol> blathijs: fubar a common placeholder in programming, and also an acronym for Forward Observational Officer

There are also more explicit commands for doing things in a private
message, which include the channel explicitely. See their corresponding
.help outputs (or see below) for more info.

"""
from willie.module import *

import re
import os
import json

def setup(bot):
    pass

class FactError(Exception):
    """Exception when manipulating factoid, contains human-readable error message."""
    pass

def get_channel_data(bot, channel):
    """Retrieve factoid facts and aliases for the given data. Gets them
       from the database, or from memory if previously loaded already.

       Returns two values, a dict of facts and a dict of aliases.

       The facts dict maps lowercase fact names to a tuple of fact name,
       verb and a list of fact values.

       The aliases dict maps lowercase alias names to the lowercase fact
       names they alias.

       The returned dicts can be modified, but should not be replaced
       entirely."""
    def get_cached(key, cache):
        """Get the value for channel from cache, or get the channel data
           identified by key from the database if not found in the cache."""
        if not channel in cache:
            stored = bot.db.get_channel_value(channel, key)
            if stored is None:
                cache[channel] = {}
            else:
                cache[channel] = stored
        return cache[channel]
    return (get_cached('factoids_facts', get_channel_data.facts_cache),
            get_cached('factoids_aliases', get_channel_data.aliases_cache))
get_channel_data.facts_cache = {}
get_channel_data.aliases_cache = {}

def set_channel_data(bot, channel, facts, aliases):
    """Update fact and/or alias data. Should be passed the two dicts
    returned by get_channel_data(), possibly modified (but not replaced
    by a new dict)."""
    bot.db.set_channel_value(channel, 'factoids_facts', facts)
    bot.db.set_channel_value(channel, 'factoids_aliases', aliases)

    if bot.config.has_option('factoid', 'export_dir'):
        obj = {'facts': facts, 'aliases': aliases}
        fname = os.path.join(bot.config.factoid.export_dir, channel + '.json')
        with open(fname, 'w') as out:
            json.dump(obj, out, indent=4, sort_keys=True)

def get_value(bot, channel, key):
    """Retrieve a single value. Returns (key, verb, facts), where key is
    the key with the original casing, and facts is a list of facts."""
    facts, aliases = get_channel_data(bot, channel)

    # Resolve alias
    try:
        key = aliases[key.lower()]
    except KeyError:
        # No alias defined, that's ok
        pass

    return facts.get(key.lower(), None)

def add_facts(bot, channel, key, verb, add, also):
    """
    Add one or more facts.
    """
    facts, aliases = get_channel_data(bot, channel)
    add = [value.strip() for value in add]
    try:
        key = aliases[key.lower()]
    except KeyError:
        # No alias defined, that's ok
        pass

    try:
        (key, verb, values) = facts[key.lower()]
        if not also:
            raise FactError("{} is already defined. Say \"{} is also ...\" to add an additional meaning".format(key, key))
        values.extend(add)
    except KeyError:
        values = add

    facts[key.lower()] = (key, verb, values)
    set_channel_data(bot, channel, facts, aliases)

def set_alias(bot, channel, key, value):
    """Add an alias."""
    facts, aliases = get_channel_data(bot, channel)

    if key.lower() in aliases:
        raise FactError('{} is already an alias, use the delete/forget command to remove the alias first.'.format(key))

    if key.lower() in facts:
        raise FactError('{} already has facts, use the delete/forget command to remove the alias first.'.format(key))

    # Resolve value as an alias, so we never store
    # alias-to-alias, but only alias-to-fact.
    try:
        value = aliases[value.lower()]
    except KeyError:
        # No alias defined, that's ok
        pass

    if not value.lower() in facts:
        raise FactError("{} is not defined yet. Define it first before you can add an alias.".format(value))
    aliases[key.lower()] = value.lower()
    set_channel_data(bot, channel, facts, aliases)

def delete_value(bot, channel, key):
    """Delete a fact or alias."""
    facts, aliases = get_channel_data(bot, channel)
    if key.lower() in facts:
        del facts[key.lower()]
        # Delete all aliases that point to this fact, too
        for k in [k for (k, v) in aliases.items() if v == key.lower()]:
            del aliases[k]
    elif key.lower() in aliases:
        del aliases[key.lower()]
    else:
        raise FactError('I don\'t know about {}'.format(key))
    set_channel_data(bot, channel, facts, aliases)

@commands('(.+?) (is|are) (also )?(.+)')
@require_chanmsg()
@priority('low')
def learn(bot, trigger):
    # Intentionally not documented, since the command regex looks ugly
    # in the commands list. Instead, the private-message version below
    # documents this as well.

    # Note that group 1 is the entire match
    key = trigger.group(2)
    verb = trigger.group(3)
    also = trigger.group(4)
    facts = trigger.group(5)

    channel = trigger.sender

    # Trip any full stop at the end (will be added on output)
    if facts[-1] == '.':
        facts = facts[:-1]

    try:
        # Allow multiple facts, so you can forget and re-add an existing
        # factoid easily.
        add_facts(bot, channel, key, verb, facts.split(' and also '), also)

        if also:
            bot.reply('I now know more about {}'.format(key))
        else:
            bot.reply('I now know about {}'.format(key))
    except FactError as exc:
        bot.reply(exc)

@commands('(.+?) (?:aliases|refers to) (.+)')
@require_chanmsg()
@priority('low')
def alias(bot, trigger):
    # Intentionally not documented, since the command regex looks ugly
    # in the commands list. Instead, the private-message version below
    # documents this as well.

    # Note that group 1 is the entire match, group 2 is the first
    # capture above.
    key = trigger.group(2)
    target = trigger.group(3)

    channel = trigger.sender
    try:
        set_alias(bot, channel, key, target)
        bot.reply('{} is now an alias for {}'.format(key, target))
    except FactError as exc:
        bot.reply(exc)

@commands('forget')
@require_chanmsg()
@require_admin()
def forget(bot, trigger):
    # Intentionally not documented, since the command regex looks ugly
    # in the commands list. Instead, the private-message version below
    # documents this as well.

    # Note that group 1 is the entire match, group 2 is all the
    # arguments, group 3 is the first argument.
    key = trigger.group(3)
    channel = trigger.sender

    try:
        delete_value(bot, channel, key)
        bot.reply('I forgot about {}'.format(key))
    except FactError as exc:
        bot.reply(exc)

@commands('(?:(?:tell|teach) ([^ ]+) about )?(.*)')
@commands('give ([^ ]+) (.*)')
@require_chanmsg()
def get(bot, trigger):
    # Intentionally not documented, since the command regex looks ugly
    # in the commands list. Instead, the private-message version below
    # documents this as well.

    # Note that group 1 is the entire match, group 2 is the first
    # capture above.
    target = trigger.group(2)
    key = trigger.group(3)
    channel = trigger.sender
    error = False
    if target:
        error = True
    # If no target is specified, just reply to the sender
    if not target:
        target = trigger.nick

    do_get(bot, channel, target, key, error)

def do_get(bot, channel, target, key, error):
    """Helper function to get a factoid, format it and reply to target.

       If error is True, an error is emitted if the factoid is not found."""
    value = get_value(bot, channel, key)

    if not value:
        if (error):
            bot.reply("Sorry, I don't know about {}".format(key))
        return

    (key, verb, values) = value

    formatted = ''
    for value in values:
        if formatted:
            formatted += ' and also {}'.format(value)
        else:
            formatted += value

    max_messages = 3
    bot.say('{}: {} {} {}'.format(target, key, verb, formatted), max_messages)

@commands('factoid get')
@require_privmsg
def getcmd(bot, trigger):
    """
    Retrieve an existing factoid.
    e.g. $prefixfactoid get #mychannel deadbeef

    This command is only usable in a private message. To retrieve a factoid in a channel, say:

      $prefixdeadbeef

    Or, to direct the reply at someone else, say:
      $prefixtell this_guy about deadbeef
      $prefixteach this_guy about deadbeef
      $prefixgive this_guy deadbeef
    """
    # Note that group 1 is command, 2 is all arguments, group 3 is the
    # first argument
    channel = trigger.group(3)
    key = trigger.group(4)
    if not channel or not channel in bot.channels:
        bot.reply("Invalid channel specified: {}. Valid channels are {}".format(channel, ', '.join(bot.channels)))
        return

    do_get(bot, channel, trigger.nick, key, True)

@commands('factoid add')
@require_privmsg
def addcmd(bot, trigger):
    """
    Add a factoid, or add more info about an existing factoid.
    e.g. $prefixfactoid add #mychannel deadbeef is a commonly used hexadecimal dummy value

    This command is only usable in a private message. To add a factoid
    in a channel, say:

      $prefixdeadbeef is a commonly used hexadecimal dummy value

    The syntax is the same for adding info, no explicit "also" is
    required like in a channel.
    """
    # Note that group 1 is the full command, 2 is all arguments
    # Since our last argument can contain spaces, we split the arguments
    # here manually.

    args = re.split("\s+", trigger.group(2), 3)
    if len(args) < 4:
        bot.reply("Need at least 4 arguments")
        return

    channel, key, verb, value = args

    if not channel or not channel in bot.channels:
        bot.reply("Invalid channel specified: {}. Valid channels are {}".format(channel, ', '.join(bot.channels)))
        return

    if not verb in ['is', 'are']:
        bot.reply("Only 'is' and 'are' are supported as verbs, not {}".format(verb))
        return

    try:
        add_facts(bot, channel, key, verb, value.split(', and also '), True)
        bot.reply('I now know (more) about {}'.format(key))
    except FactError as exc:
        bot.reply(exc)

@commands('factoid alias add')
@require_privmsg
def addaliascmd(bot, trigger):
    """
    Add an alias to an existing factoid
    e.g. $prefixfactoid alias add #mychannel 0xdeadbeef deadbeef
    to make 0xdeadbeef an aliases to the existing deadbeef factoid.

    Only usable in a private message. To add an alias in a channel, say:

      $prefix0xdeadbeef aliases deadbeef
    """
    # Note that group 1 is command, 2 is all arguments, group 3 is the
    # first argument
    channel = trigger.group(3)
    key = trigger.group(4)
    value = trigger.group(5)

    if not channel or not channel in bot.channels:
        bot.reply("Invalid channel specified: {}. Valid channels are {}".format(channel, ', '.join(bot.channels)))
        return

    try:
        set_alias(bot, channel, key, value)
        bot.reply('{} is now an alias for {}'.format(key, value))
    except FactError as exc:
        bot.reply(exc)

@commands('factoid delete')
@example('.factoid delete #mychannel key')
@require_privmsg()
@require_admin()
def delete(bot, trigger):
    """
    Deletes an existing factoid (or alias).
    e.g. $prefixfactoid delete #mychannel deadbeef

    Only usable in a private message. To delete a factoid in a channel, say:

      $prefixforget deadbeef

    Only admins can delete factoids.
    """
    # Note that group 1 is command, 2 is all arguments, group 3 is the
    # first argument
    channel = trigger.group(3)
    key = trigger.group(4)

    if not channel or not channel in bot.channels:
        bot.reply("Invalid channel specified: {}. Valid channels are {}".format(channel, ', '.join(bot.channels)))
        return

    try:
        delete_value(bot, channel, key)
        bot.reply('I forgot about {}'.format(key))
    except FactError as exc:
        bot.reply(exc)

@commands('factoid list')
@example('.factoid list #mychannel')
@require_privmsg()
def listnames(bot, trigger):
    """
    Lists all factoid and alias names.
    e.g. $prefixfactoid list #mychannel

    Only usable in a private message.
    """
    # Note that group 1 is command, 2 is all arguments, group 3 is the
    # first argument
    channel = trigger.group(3)

    if not channel or not channel in bot.channels:
        bot.reply("Invalid channel specified: {}. Valid channels are {}".format(channel, ', '.join(bot.channels)))
        return

    facts, aliases = get_channel_data(bot, channel)
    # Use msg instead of reply, since that supports splitting
    factnames = [name for (name, verb, values) in facts.values()]
    bot.msg(trigger.nick, 'Facts: {}'.format(', '.join(sorted(factnames))), max_messages=10)
    bot.msg(trigger.nick, 'Aliases: {}'.format(', '.join(sorted(aliases.keys()))), max_messages=10)

@commands('factoid export')
@require_privmsg()
def export(bot, trigger):
    """
    Shows if, and where the factoid database can be downloaded.

    Only usable in a private message.
    """
    if (not bot.config.has_option('factoid', 'export_dir')
        or not bot.config.has_option('factoid', 'export_url')):
        bot.reply('Export not configured')
    else:
        url = bot.config.factoid.export_url
        bot.reply('Factoid data can be found at ' + url)

if __name__ == '__main__':
    print(__doc__.strip())
