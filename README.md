Grobbebol IRC bot
=================
This is the configuration and custom code for the grobbebol IRC bot.
This IRC bot was conceived to run in #arduino on Freenode. It's most
important feature is a custom-written factoid plugin, that can collect
answers to common questions and links to good resources on common
topics.

Grobbebol runs on top of the willie IRC bot, with some modifications
(which are sent upstream and will hopefully be included).

The version used is https://github.com/matthijskooijman/willie/tree/grobbebol

Grobbebol is being run by Matthijs Kooijman (matthijs@stdin.nl, blathijs
on various IRC networks).

Factoid examples
================
Since an example is clearer than a thousand words of documentation
(sometimes), here's some things you can do in a channel.

```
<blathijs>  !timers is http://www.engblaze.com/microcontroller-tutorial-avr-and-arduino-timer-interrupts
<grobbebol> blathijs: I now know about timers
<blathijs>  !timers is also http://www.instructables.com/id/Arduino-Timer-Interrupts/
<grobbebol> blathijs: I now know more about timers
<blathijs>  !timers
<grobbebol> timers is http://www.engblaze.com/microcontroller-tutorial-avr-and-arduino-timer-interrupts,
            and also http://www.instructables.com/id/Arduino-Timer-Interrupts/
<blathijs>  !timer aliases timers
<grobbebol> blathijs: timer is now an alias for timers
<blathijs>  !timer
<grobbebol> timers is http://www.engblaze.com/microcontroller-tutorial-avr-and-arduino-timer-interrupts,
            and also http://www.instructables.com/id/Arduino-Timer-Interrupts/
<blathijs>  !tell Yotson about timers
<grobbebol> Yotson: timers is http://www.engblaze.com/microcontroller-tutorial-avr-and-arduino-timer-interrupts,
            and also http://www.instructables.com/id/Arduino-Timer-Interrupts/
```

In a private message with grobbebol, you can give a few more commands:
"factoid get", "factoid add", "factoid alias add", "factoid list",
"factoid export", "factoid delete" (admins only). Try e.g. "!help
factoid list" in a private message to find out more.
