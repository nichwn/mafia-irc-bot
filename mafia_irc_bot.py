# TODO - override notices?
# TODO - !help or /msg HELP etc.
# TODO - check getEtc. rather than etc.
# TODO - manage if a player d/cs or is kicked
# TODO - allow for reconnection? Reset game? Continue game but check integrity?
# TODO - more generic block of private actions - command whitelist?
# TODO - put self.nickname.lower() == channel into a function
# TODO - instead of calling privmsg, make a function and call that
# (ex. !restart and !end)

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
        self.vote = None
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
        self.round = 0
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
        if self.isGop(user):
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

    def leave(self, user):
        """Removes a player from the player list, if possible."""
        if user in self.players:
            del self.players[user]
            return True
        else:
            return False

    def numPlayers(self):
        """Determines if there are players left."""
        return len(self.players.keys())

    def newGop(self):
        """Changes the new GOP."""
        self.gop = self.players.keys()[0]
        return self.gop

    def isGop(self, user):
        """Determines if the user is GOP."""
        return user == self.gop

    def rollRoles(self):
        """Determines peoples roles, and returns player data."""
        pass

    def nextRound(self):
        """Increments the round number, and returns it."""
        self.round += 1
        return self.round

    def setDay(self):
        """Sets the game status to 'Day'."""
        self.phase = self.DAY

    def clear(self):
        """Clears data that doesn't need to be kept between phases."""
        for data in players.values():
            data.vote = None
            self.voted_by = []
            self.role.ab_target = None

    def detVictory(self):
        """Determines if an alignment has won. Return None if no alignment has.
        """
        align = []
        for data in self.players.values():
            if data.role.alignment not in align:
                align.append(data.role.alignment)
                if len(align) > 1:
                    # More than one alignment still remains
                    return None
        return align[0]


class MafiaBot(irc.IRCClient):
    """A bot which manages a mafia game."""

    nickname = "Mafiabot"  # TODO - make an argument parameter
    password = "mafiabot"  # TODO - make an argument parameter
    sourceURL = ""  # TODO - fill in later

    MIN_PLAYERS = 5
    MAX_PLAYERS = 12


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
            # Attempt to begin a new game
            if (channel != self.nickname.lower() and
                self.game.getPhase() == self.game.getInitial()):
                # Begin a new game
                self.game.newGame(user)
                msg = ("A new mafia game has begun! Type !join to join. There "
                       "is a minimum of {}, and ".format(self.MIN_PLAYERS) +
                       "a maximum of {} players ".format(self.MAX_PLAYERS) +
                       "that can play.\nThe game starter has been given Game "
                       "Operator (GOP) status and can commence the game by "
                       "typing !start.")

            elif self.game.getPhase() != self.game.getInitial():
                # Can't begin a new game as one is already in progress
                msg = ("A game is already in progress. Wait for it to finish "
                       "before starting a new one.\nIf you'd like to end a "
                       "game early, you can type !end to end the game, or "
                       "!restart to restart the game if you're the GOP.")

            else:
                # Can't begin a new game, as we don't know what channel to play
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
                if (self.game.join(user) and
                    self.game.numPlayers() <= self.MAX_PLAYERS):
                    # Joined!
                    msg = "{} has joined the game.".format(user_orig)
                elif self.game.numPlayers() > self.MAX_PLAYERS:
                    # Too many players
                    msg = ("{} failed to join the game as the game capacity "
                           "reached the cap.")
                else:
                    # Already signed up
                    msg = ("Failed to join the game, as {} ".format(user_orig)
                           + "has already entered.")
            elif self.nickname.lower() == channel:
                    # Can't sign up privately
                    msg = "You can't join a game via PM."
            else:
                # Wrong phase
                msg = "You can't join the game right now."
            self.msg_send(self.nickname, channel, user, msg)

        elif command == "leave":
            #Attempt to leave a new game.
            if (self.game.getPhase() == self.game.getSign_Up()
                and self.nickname.lower() != channel):
                gop = self.game.isGop(user)
                if self.game.leave(user):
                    # Left!
                    msg = "{} has left the game.".format(user_orig)
                    if self.game.numPlayers() == 0:
                        # Players remaining?
                        msg += (" As there are no players left the "
                                "game has been closed.")
                        self.game.gameClear()
                    elif gop:
                        # Leaving playing was GOP. Select a new one.
                        n_gop = self.game.newGop()
                        msg += " {} is now GOP.".format(n_gop)
                else:
                    # Not in game
                    msg = ("Failed to leave the game, as {}".format(user_orig)
                           + "has not entered it.")
            elif self.nickname.lower() == channel:
                    # Can't sign up privately
                    msg = "You can't leave a game via PM."
            else:
                # Wrong phase
                msg = "You can't leave the game right now."
            self.msg_send(self.nickname, channel, user, msg)

        elif command == "start":
            n_players = self.game.numPlayers()
            if (self.game.isGop(user) and
                self.MIN_PLAYERS <= n_players and
                self.nickname.lower() != channel):
                # Closes sign ups and begins the game
                msg = ("Sign ups have been closed, and the game will begin "
                       "shortly. You should be receiving your roles now.")
                self.gameStart()
                return
            elif not self.game.isGop(user):
                # Only GOP can use this command
                msg = "Only the GOP can use this command."
            elif self.MIN_PLAYERS > n_players:
                # Not enough players
                msg = ("Insufficient number of players. The minimum number "
                       "is {} and there is/are only ".format(self.MIN_PLAYERS) +
                       "{} player(s) signed up.".format(n_players))
            else:
                # Can't start via private message
                msg = ("You cannot use this command via PM.")
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

    def gameStart(self):
        players = self.game.rollRoles()
        self.rollDay()

    def rollDay(self):
        """Roll a new day phase."""
        round = self.game.nextRound()
        self.newPhaseAct()
        self.game.setDay()
        #TODO - implement flavour

    def newPhaseAct(self):
        """Performs actions required at the start of every phase."""
        self.game.clear()
        vict = self.game.detVictory()
        if vict is not None:
            # Victory achieved
            self.victory()

    def victory(self):
        """Winning proceedings."""
        pass
            


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
