# -*- coding: utf-8 -*-
"""Test module for simplesignals

Copyright (C) 2017 Radomir Matveev GPL 3.0+
"""

from sisi import *

# --------------------------------------------------------------------------- #
# Test module
# --------------------------------------------------------------------------- #
logging.basicConfig(level=logging.INFO)

add_signals("simple signal")
add_signals("pos args", "key args")
log.info("known signals: %s", signals)

class TestSender(object):
    def __init__(self, x):
        self.x = x

#    def sendmsg(self, signal, sender, *args, **kwargs):
#        send(signal, sender, **kwargs)

    def send_simple_signal(self):
        print("[SENDER] send simple signal")
        send("simple signal", sender=self)
        print("[SENDER] send simple signal anonymously")
        send("simple signal")
        print("[SENDER] send simple signal with an invalid sender")
        send("simple signal", sender=Any)

#    def send_pos_args_signal(self):
#        a = "A"
#        b = "B"
#        c = "C"
#        signal = "pos args"
#        sender = self
#        print("[SENDER] send pos args signal with no args")
#        try:
#            send(signal, sender)
#        except KeyError:
#            log.exception(" ")
#            print("As expected we got a KeyError\n")
#        print("[SENDER] send pos args signal with one custom arg:", a)
#        try:
#            send(signal, sender, a)
#        except KeyError:
#            log.exception(" ")
#            print("As expected we got a KeyError\n")
#        print("[SENDER] send pos args signal with two custom args:", a, b)
#        send(signal, sender, a, b)
#        print("[SENDER] send pos args signal with three extra args:",
#              c, b, a)
#        self.sendmsg(signal, sender, c, b, a)

    def send_key_args_signal(self):
        a = "A"
        b = "B"
        c = "C"
        signal = "key args"
        sender = self
        print("[SENDER] send key args signal with no args")
        try:
            send(signal, sender=sender)
        except KeyError:
            log.exception(" ")
            print("As expected we got a KeyError\n")
        print("[SENDER] send key args signal with one custom arg")
        send(signal, sender=sender, kwarg1=c)
        print("[SENDER] send key args signal with three custom args")
        send(signal, sender=sender, kwarg2=a, kwarg3=b, kwarg1=c)


class TestReceiver(object):

    def on__simple_signal(self, sender):
        print("[RECEIVER] received '%s' signal from %s"
              % ("simple signal", sender))
        print()

    def on__pos_args(self, sender, arg1, arg2):
        print("[RECEIVER] received '%s' signal from %s"
              % ("pos_args", sender))
        print("args received:", arg1, arg2)
        print()

    def on__key_args(self, sender, kwarg1, **kwargs):
        print("[RECEIVER] received '%s' signal from %s"
              % ("key_args", sender))
        print("args received:")
        print("kwarg1:", kwarg1)
        print("**kwargs:", kwargs)
        print()


testsender = TestSender("testmsg")
testreceiver = TestReceiver()

autoconnect_signals(testreceiver)

print()
print("Start signaling tests")
print()
testsender.send_simple_signal()
#testsender.send_pos_args_signal()
testsender.send_key_args_signal()

