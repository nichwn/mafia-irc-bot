# TODO - override notices?
# TODO - !help or /msg HELP etc.
# TODO - check getEtc. rather than etc.
# TODO - manage if a player d/cs or is kicked
# TODO - allow for reconnection? Reset game? Continue game but check integrity?

"""

An IRC bot which manages Mafia games.

"""

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol

import sys


class Role:
    """Stores role information."""

    def __init__(self, r_name, alignment, ab_active):
        self.r_name = r_name
        self.alignment = alignment
        self.ab_active = ab_active
        self.ab_target = None


class Player:
    """Stores player information."""

    def __init__(self, state = "alive", role = None):
        self.state = state
        self.role = role
        self.vote = ""
        self.voted_by = []


class MafiaGame:
    """Handles the mafia game."""

    # Flags for game states
    INITIAL = 0
    SIGN_UP = 1
    DAY = 2
    NIGHT = 3


    def __init__(self):
        self.players = {}
        self.gop = ""
        self.phase = self.INITIAL

    def newGame(self, user):
        """Start a new game."""
        self.phase = self.SIGN_UP
        self.gop = user
        self.players[user] = None

    def commands(self):
        """Returns a list of currently available commands and how to use
        them."""
        # TODO - implement
        pass

    def getPhase(self):
        """Returns a flag that indicates the current phase. It's guaranteed
        that the flag values are in the order of:

        Initial < Sign_Up < Day < Night"""
        return self.phase

    def getInitial(self):
        """Returns a flag that indicates the initial phase. It's guaranteed
        that the flag values are in the order of:

        Initial < Sign_Up < Day < Night"""
        return self.INITIAL

    def getSign_Up(self):
        """Returns a flag that indicates the sign_up phase. It's guaranteed
        that the flag values are in the order of:

        Initial < Sign_Up < Day < Night"""
        return self.SIGN_UP

    def getDay(self):
        """Returns a flag that indicates the day phase. It's guaranteed
        that the flag values are in the order of:

        Initial < Sign_Up < Day < Night"""
        return self.DAY

    def getNight(self):
        """Returns a flag that indicates the night phase. It's guaranteed
        that the flag values are in the order of:

        Initial < Sign_Up < Day < Night"""
        return self.NIGHT

    def end(self, user):
        """Attempts to end the game. Return True if the game was ended."""
        if user == self.gop:
            self.gameClear()
            return True
        else:
            return False

    def gameClear(self):
        """Clears the game data in preparation for a new game."""
        self.players = {}
        self.phase = self.INITIAL

    def transferGop(self, user, target):
        """Transfer GOP to a target player."""
        print target, self.players.keys()
        if user == self.gop and target in self.players:
            self.gop = target
            return True
        else:
            return False

    def getLivingPlayers(self):
        """Return a list of all living players."""
        alive = []
        for k, v in self.players.iteritems():
            # Iterate through all the players
            if v.state == "alive":
                # Living player found
                alive.append(k)
        return alive

    def join(self, user):
        """Adds a player to the player list, if not already in it."""
        if user not in self.players:
            self.players[user] = None
            return True
        else:
            return False


class MafiaBot(irc.IRCClient):
    """A bot which manages a mafia game."""

    nickname = "Mafiabot"  # TODO - make an argument parameter
    password = "mafiabot"  # TODO - make an argument parameter
    sourceURL = ""  # TODO - fill in later


    # Connection

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.game = MafiaGame()

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)


    # Events

    def signedOn(self):
        """After connecting to the server, join the channel."""
        self.join(self.factory.channel)

    def joined(self, channel):
        """After joining a channel, output a greeting."""
        msg = ("I'm a bot which manages mafia games. /say or PM me !help for "
               "help.")
        self.msg(channel, msg)

    def privmsg(self, user, channel, msg):
        """Parse and interpret commands."""

        # Usernames are stored in lowercase, but the original input needs to be
        # kept for message outputs
        user_orig = user.split('!', 1)[0]
        user = user_orig.lower()

        # Check if it is a command
        if msg.startswith('!'):
            command_orig = msg[1:]
        elif msg.startswith(user + ": !"):
            command_orig = msg[len(user) + 4:]
        elif msg.startswith(user + ":!"):
            command_orig = msg[len(user) + 3]
        else:
            return;

        # For commands where parameters may be outputted, the original input
        # needs to be kept
        command = command_orig.lower()
        
        # Interpret command
        if command == "new":
            # Attempt to start a new game
            if (channel != self.nickname.lower() and
                self.game.getPhase() == self.game.getInitial()):
                # Start a new game
                self.game.newGame(user)
                msg = ("A new mafia game has begun! Type !join to join. There "
                       "is a minimum of 5, and a maximum of 12 players that "
                       "can play.\nThe game starter has been given Game "
                       "Operator (GOP) status and can commence the game by "
                       "typing !start.")

            elif self.game.getPhase() != self.game.getInitial():
                # Can't start a new game as one is already in progress
                msg = ("A game is already in progress. Wait for it to finish "
                       "before starting a new one.\nIf you'd like to end a "
                       "game early, you can type !end to end the game, or "
                       "!restart to restart the game if you're the GOP.")

            else:
                # Can't start a new game, as we don't know what channel to play
                # it in
                msg = ("You can't start a game with a PM. Please try again "
                       "in the channel you'd like to play in.")
            self.msg_send(self.nickname, channel, user, msg)

        elif command == "help":
            # Help requested. Output usable commands.
            # TODO - implement
            curr_phase = self.game.getPhase()
            if curr_phase == self.game.getInitial():
                pass
            elif curr_phase == self.game.getSign_Up():
                pass
            elif curr_phase == self.game.getDay():
                pass
            elif curr_phase == self.game.getNight():
                pass
            # TODO - also print out 'anytime' commands

        elif command == "end":
            # Attempt to end the game
            if (channel != self.nickname.lower() and
                self.game.getPhase() != self.game.getInitial()):
                if self.game.end(user):
                    # Success
                    msg = ("The game has been closed early by request of "
                           + user_orig + ". Thanks for playing!")
                else:
                    msg = ("Failed to end the game. Are you sure that a game "
                           "is running, and that you're the GOP?")
            elif channel == self.nickname.lower():
                msg = ("This command cannot be sent via PM.")
            else:
                msg = ("You can't end a game that hasn't started!")
            self.msg_send(self.nickname, channel, user, msg)

        elif command == "restart":
            # Attempt to restart the game
            restart = 0
            if (channel != self.nickname.lower() and
                self.game.getPhase() != self.game.getInitial()):
                if self.game.end(user):
                    # Success
                    msg = ("The game has been closed early by request of "
                           + user_orig + ". Thanks for playing!")
                    restart = 1
                else:
                    msg = ("Failed to restart the game. Are you sure that a game "
                           "is running, and that you're the GOP?")
            elif channel == self.nickname.lower():
                msg = ("This command cannot be sent via PM.")
            else:
                msg = ("You can't end a game that hasn't started!")
            self.msg_send(self.nickname, channel, user, msg)

            if restart:
                # Begin a new game
                msg = "!new"
                self.privmsg(user, channel, msg)

        elif command[:3] == "gop":
            # Request to transfer GOP

            # Check if a second argument has been provided
            try:
                target = command.split()[1]
                target_orig = command_orig.split()[1]
            except:
                target = ""

            if target and self.game.transferGop(user, target):
                # Success
                msg = ("GOP has been transferred from "
                       "{} to {}.".format(user_orig, target_orig))
            elif not target:
                # Second argument not provided
                msg = "Failed as no player name was provided."
            else:
                # Other failure
                msg = ("Failed to transfer GOP. Are you sure you have GOP, "
                        "and that the player '{}' exists?".format(target_orig))
            self.msg_send(self.nickname, channel, user, msg)

        elif command == "alive":
            # Not yet tested, as there's no way to start the game yet. A bit
            # dumb to have written it at this stage I'll admit.
            if self.game.getPhase() > self.game.getSign_Up():
                # Game active, so determine living players
                msg = "Players alive:"
                for player in self.game.getLivingPlayers():
                        msg += '\n' + player
            else:
                # Game inactive
                msg = "No game is running."
            self.msg_send(self.nickname, channel, user, msg)

        elif command == "join":
            #Attempt to join a new game.
            if (self.game.getPhase() == self.game.getSign_Up()
                and self.nickname.lower() != channel):
                if self.game.join(user):
                    # Joined!
                    msg = "{} has joined the game.".format(user_orig)
                else:
                    # Already signed up
                    msg = ("Failed to join the game, as '{}' ".format(user_orig)
                           + "has already entered.")
            elif self.nickname.lower() == channel:
                    # Can't sign up privately
                    msg = "You can't join a game via PM."
            else:
                # Wrong phase
                msg = "You can't join the game right now."
            self.msg_send(self.nickname, channel, user, msg)
                




        # TODO - add more commands


    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        # TODO - change name in player lists etc.


        # Other functions

    def msg_send(self, nickname, channel, user, msg):
        """Determines where to send a message, and sends it."""
        if nickname.lower() == channel:
            # Private message
            self.msg(user, msg)
        else:
            # Channel
            self.msg(channel, msg)


class MafiaBotFactory(protocol.ClientFactory):
    """A factory for MafiaBots."""

    def __init__(self, channel):
        self.channel = channel

    def buildProtocol(self, addr):
        bot = MafiaBot()
        bot.factory = self
        return bot

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, terminate the program."""
        reactor.stop()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()


if __name__ == '__main__':
    # Create factory protocol and application
    bot = MafiaBotFactory("mtest")

    # Connect factory to this host and port
    reactor.connectTCP("irc.vision-irc.net", 6667, bot)

    # Run bot
    reactor.run()
