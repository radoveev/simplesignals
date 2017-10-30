# -*- coding: utf-8 -*-
"""Simple, pure python signaling module inspired by pydispatcher

Copyright (C) 2017 Radomir Matveev GPL 3.0+

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""


# --------------------------------------------------------------------------- #
# Import libraries
# --------------------------------------------------------------------------- #
import inspect
import logging


# --------------------------------------------------------------------------- #
# Define classes
# --------------------------------------------------------------------------- #
class Representer(object):
    """Represents "Anonymous" or "Any".
    """
    def __init__(self, meaning):
        self.meaning = meaning

    def __str__(self):
        return "<{}>".format(self.meaning)

    def __repr__(self):
        return "<{}>".format(self.meaning)
Any = Representer("any")
Anonymous = Representer("anonymous")


class ConnectionMap(object):
    """Maps signals and senders to lists of receivers.
    """
    def __init__(self):
        self.connections = {}  # {"sig1": {sender1: [reic1, ...], ...}, ...}

    def connect(self, receiver, signal, sender):
        log.info("Connect %s to '%s' from %s", receiver, signal, sender)
        # get map of senders for this signal
        if signal not in self.connections:
            self.connections[signal] = {}
        sendermap = self.connections[signal]
        # get map of receivers for this sender
        if sender not in sendermap:
            sendermap[sender] = []
        receivers = sendermap[sender]
        # add new receiver to sender
        receivers.append(receiver)
         #TODO the next line might be unneccessary
        self.connections[signal][sender] = receivers

    def get_receivers(self, signal, sender):
        # signals from anonymous senders are sent
        # to all receivers of that signal
        if sender is Anonymous:
            sender = Any
        receivers = []
        # determine which signals are relevant
        if signal is Any:  # all are relevant
            signals = self.connections.keys()
        else:  # only one signal is relevant
            signals = []
            # is there a sendermap for this signal?
            if signal in self.connections:
                signals.append(signal)
            # receivers that listen to any signal have to be included
            if Any in self.connections:
                signals.append(Any)
            # are there any receivers listening to this signal?
            if not signals:
                log.warning("No receivers found for '%s' from %s",
                            signal, sender)
        # fetch sendermaps for all relevant signals
        for sig in signals:
            sendermap = self.connections[sig]
            # determine which senders are relevant
            if sender is Any:
                senders = sendermap.keys()
            else:
                senders = []
                # is there a receiverlist for this sender?
                if sender in sendermap:
                    senders.append(sender)
                # receivers that listen to any sender have to be included
                if Any in sendermap:
                    senders.append(Any)
                # are there any receivers listening to this sender?
                if not senders:
                    log.warning("No receivers found for '%s' from %s",
                                signal, sender)
            # fetch receiverlists for all relevant senders
            for sen in senders:
                receivers.extend(sendermap[sen])
        return receivers


class Connections(object):
    """Connects senders via signals to lists of receivers or channels.

    A channel itself is just a name for a list of receivers.
    """
    def __init__(self):
        self.connmap = ConnectionMap()

    def connect(self, receiver, signal=Any, sender=Any, channel=None):
        """This function connects a receiver to a signal.

        For a description of valid arguments for this method, read the
        docstring of the connect function in this package.
        """
        if callable(receiver) is False:
            raise ValueError("Receiver is not callable: %s" % receiver)
        if sender is None:
            raise ValueError("Cannot connect to anonymous signals explicitly.")
        if channel is None:
            self.connmap.connect(receiver, signal, sender)
        else:
            self.connmap.connect(receiver, signal, channel)

    def send(self, signal, sender=Anonymous, channel=None, **kwargs):
        """This function sends a signal safely.

        For a description of valid arguments for this method, read the
        docstring of the send function in this package.
        """
        # warn about Any as sender
        if sender is Any:
            log.warning("%s is not a valid sender. " +
                        "The signal is sent anonymously instead.", sender)
            sender = Anonymous
        # get a list of all receivers for this signal
        if channel is None:
            receivers = self.connmap.get_receivers(signal, sender)
        else:
            receivers = self.connmap.get_receivers(signal, channel)
        # prepare the keyword arguments
        kwargs["sender"] = sender
        if channel is not None:
            kwargs["channel"] = channel
        # call each receiver with the appropriate arguments
        for receiver in receivers:
            safecall(receiver, **kwargs)

    def prettyprint(self):
        for signal in sorted(self.connmap.keys()):
            print(signal, ":")
            for sender in self.connmap[signal].keys():
                print("\t", sender, "\t", self.connmap[signal][sender])


# --------------------------------------------------------------------------- #
# Declare module globals
# --------------------------------------------------------------------------- #
log = logging.getLogger(__name__)
signals = set([Any])
channels = set([Any])
connections = Connections()
# Any and Anonymous are instantiated above because
# they are used as default arguments in class methods


# --------------------------------------------------------------------------- #
# Define functions
# --------------------------------------------------------------------------- #
def connect(receiver, signal=Any, sender=Any, channel=None):
    """This function connects a receiver to a signal.

    If a channel is given, the sender argument is ignored.

    If signal is Any the receiver is connected to all signals for the
    specified sender or channel.
    If sender is Any the receiver is connected to all senders for the
    specified signal. The channel argument must be None.
    If channel is Any the receiver is connected to all channels for the
    specified signal. The sender argument is ignored.
    """
    global connections
    if channel is not None and sender is not Any:
        log.warning("Connecting %s via '%s' to channel '%s'; " +
                    "The specified sender %s was ignored.",
                    receiver, signal, channel, sender)
    # warn about unknown signal, but connect it anyway
    if signal not in signals:
        log.warning("Connecting unknown signal '%s' on %s", signal, receiver)
    # warn about unknown channel, but connect it anyway
    if channel is not None and channel not in channels:
        log.warning("Connecting unknown channel '%s' on %s", channel, receiver)
    connections.connect(receiver, signal, sender, channel)


def send(signal, sender=Anonymous, channel=None, **kwargs):
    """This function sends a signal safely and warns about unknown signals.

    If a channel is given, the sender argument does not influence which
    receivers will receive the signal. Nevertheless the sender argument will
    be passed on to the revceiver.

    Keyword arguments given to this function are passed on to signal handlers
    if they have a keyword argument with the same name.

    If signal is Any, all receivers connected to the specified sender or
    channel are called.
    If sender is Anonymous, all receivers connected to the specified signal
    are called. The channel argument must be None.
    If channel is Any, all receivers connected to the specified signal are
    called. The sender argument is ignored.
    """
    global connections
    # warn about unknown signals...
    if signal not in signals:
        log.warning("Sending unknown signal %s from %s", signal, sender)
    # ...but send them anyway
    log.info("Send signal '%s' from '%s'", signal, sender)
    connections.send(signal, sender, channel, **kwargs)


def safecall(iscalled, **kwargs):
    """Tries to call the callable with as little risk as possible."""
    called_signature = inspect.signature(iscalled)
    args_to_inspect = kwargs.copy()
    accepted_args = []
    accepted_kwargs = {}
    for name in called_signature.parameters:
        param = called_signature.parameters[name]
        if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
            try:
                arg = args_to_inspect.pop(name)
            except KeyError as exc:
                recname = iscalled.__name__
                raise TypeError(
                        "The receiver '%s' expects " % recname +
                        "the argument '%s', " % name +
                        "but it was not sent.\n%s: %s" % (recname, iscalled)
                        ) from exc
            accepted_args.append(arg)
        # TODO: check if the following parameter kinds can actually be used
        elif param.kind == inspect.Parameter.KEYWORD_ONLY:
            accepted_kwargs[name] = args_to_inspect.pop(name)
        elif param.kind == inspect.Parameter.VAR_KEYWORD:
            accepted_kwargs.update(args_to_inspect)
            args_to_inspect = {}
        else:
            raise NotImplementedError("Receiver parameter " +
                                      str(param.kind) + " is not supported." +
                                      " Use keyword parameters instead.")
    iscalled(*accepted_args, **accepted_kwargs)


def add_signals(*signallist):
    """Adds a list of new signals to the set of known signals."""
    global signals
    for sig in signallist:
        signals.add(sig)


def remove_signals(*signallist):
    """Removes a list of signals from the set of known signals."""
    global signals
    for sig in signallist:
        signals.remove(sig)


def add_channels(*channellist):
    """Adds a list of new channels to the set of known channels."""
    global channels
    for chan in channellist:
        channels.add(chan)


def remove_channels(*channellist):
    """Removes a list of channels from the set of known channels."""
    global channels
    for chan in channellist:
        channels.remove(chan)


def autoconnect_signals(receiver, prefix="on__", senders=None, channels=None):
    """Connects methods of the receiver object to signals.

    The naming convention for signal handler methods is the signal name (with
    spaces replaced by underscores) with a prefix.
        Example:
            prefix = "on__"
            name of signal = "an example signal"
            name of signal handler method = "on__an_example_signal"

    If the receiver should only receive the signal if it was sent by a specific
    sender, the senders keyword argument should be a dict with signal names as
    keys and senders as values.
        Example:
            The receiver should only receive "restricted signal" if it was sent
            by the sender some_sender.
            senders = {"restricted signal": some_sender,
                       "another signal": [another_sender, third_sender]}

    If the receiver should only receive the signal if it was sent via a
    specific channel, the channels keyword argument should be a dict with
    signal names as keys and channels as values.
        Example:
            The receiver should only receive "channeled signal" if it was sent
            via the channel "cool channel".
            channels = {"channeled signal": "cool channel",
                        "yet another signal": ["cool channel", "test channel"]}

    """
    log.debug("Connecting signals on %s", receiver)
    # handle keyword arguments
    if senders is None:
        senders = {}
    if channels is None:
        channels = {}
    # list all methods of this class (based on inspect.getmembers)
    handlers = []
    for name in dir(receiver):
        if name.startswith(prefix):
            method = getattr(receiver, name)
            if inspect.ismethod(method):
                handlers.append((name, method))
    # connect handlers
    for name, method in handlers:
        # determine signal name
        signal = name[len(prefix):].replace("_", " ")
        # see if a specific sender should be used for this signal
        senderdata = senders.get(signal, [])
        # handle single sender
        if isinstance(senderdata, (list, tuple)):
            senderlist = senderdata  # multiple senders
        else:
            senderlist = [senderdata]  # single sender
        # connect receiver to senders
        for sender in senderlist:
            connect(method, signal=signal, sender=sender, channel=None)
        # see if a specific channel should be used for this signal
        channeldata = channels.get(signal, [])
        # handle single channel
        if isinstance(channeldata, (list, tuple)):
            channellist = channeldata  # multiple channels
        else:
            channellist = [channeldata]  # single channel
        # connect receiver to channel
        for channel in channellist:
            connect(method, signal=signal, sender=Any, channel=channel)
        # if neither channel nor sender were specified,
        # connect the signal to any sender and any channel
        if not senderlist and not channellist:
            connect(method, signal=signal, sender=Any, channel=Any)

#        senderdata = self.senders.get(signal, dispatcher.Any)
#        # handle multiple senders
#        if isinstance(senderdata, list):
#            senderlist = senderdata
#        elif isinstance(senderdata, tuple):
#            log.error("Must use a list, not a tuple, to specify multiple" +
#                    " senders: %s", senderdata)
#            senderlist = []
#            #TODO no reason to break down, just fix the problem
#        else:
#            senderlist = [senderdata]
#        for sender in senderlist:
#            # warn about unknown signals...
#            if signal not in self.signals:
#                msg = "Connecting unknown signal %s on %s"
#                log.warning(msg, signal, self)
#            # ...but connect them anyway
#            if sender=="any garments":
#                print(sender, "connected to", self)
#            dispatcher.connect(method, signal=signal, sender=sender)
#            #msg = "Connecting %s from sender %s\n\tto %s"
#            #log.info(msg, signal, sender, method)
