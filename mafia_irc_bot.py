#TODO - override notices?
#TODO - !help or /msg HELP etc.

"""

An IRC bot which manages Mafia games.

"""

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol


class MafiaGame:
    pass

class MafiaBot:
    """A bot which manages a mafia game."""

    nickname = "Mafiabot"


    #Connection

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    
    #Events

    def signedOn(self):
        """After connecting to the server, join the channel."""
        self.join(self.factory.channel)

    def joined(self, channel):
        """After joining a channel, output a greeting."""
        msg = ("I'm a bot which manages mafia games. /say or PM me !help for "
               "help.")
        self.msg(channel, msg)

    def privmsg(self, user, channel, msg):
        """Interpret commands."""
        user = user.split('!', 1)

        #Check if it is a command
        if msg.startswith('!'):
            command = msg[1:]
        elif msg.startswith(user + ": !"):
            command = msg[len(user) + 4:]
        elif msg.startswith(user + ":!"):
            command = msg[len(user) + 3]
        else:
            return;

        #Interpret command
        #TODO - commands and their respective functions here

    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        #TODO - change name in player lists etc.
