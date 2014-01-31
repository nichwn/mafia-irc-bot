# TODO - override notices?
# TODO - !help or /msg HELP etc.
# TODO - manage if a player d/cs or is kicked
# TODO - more generic block of private actions - command whitelist?
# - split phase
# TODO - put self.nickname.lower() == channel into a function

"""

An IRC bot which manages Mafia games.

"""

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol

import sys, random


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

    #Flags for mafia numbers in relation to player numbers
    SECOND_MAFIA = 8
    THIRD_MAFIA = 11

    def __init__(self):
        self.players = {}
        self.gop = ""
        self.round = 0
        self.actions = 0
        self.nl_alias = ["nobody", "no-one", "noone", "no_lynch"]
        self.nl_voted = []
        self.phase = self.INITIAL

    def newGame(self, user):
        """Start a new game."""
        self.phase = self.SIGN_UP
        self.gop = user.lower()
        self.players[self.gop] = Player()

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
        self.round = 0
        self.actions = 0
        self.nl_voted = []

    def transferGop(self, user, target):
        """Transfer GOP to a target player."""
        user = user.lower()
        target = target.lower()
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
        user = user.lower()
        if user not in self.players:
            self.players[user] = Player()
            return True
        else:
            return False

    def leave(self, user):
        """Removes a player from the player list, if possible."""
        user = user.lower()
        if user in self.players:
            del self.players[user]
            return True
        else:
            return False

    def numPlayers(self):
        """Determines if there are players left."""
        return len(self.players)

    def newGop(self):
        """Changes the new GOP."""
        self.gop = self.players.keys()[0]
        return self.gop

    def isGop(self, user):
        """Determine if the user is GOP."""
        return user.lower() == self.gop

    def roleGen(self):
        """Generate player roles, and return them."""
        role_vanilla = Role("Vanilla", "Town", None)
        role_goon = Role("Goon", "Mafia", None)

        # Construct role list
        roles = []
        p_num = self.numPlayers()
        

        # Mafia roles
        count = 0
        if p_num >= self.THIRD_MAFIA:
            # 3 mafia players
            n_mafia = 3
        elif p_num >= self.SECOND_MAFIA:
            # 2 mafia players
            n_mafia = 2
        else:
            # 1 mafia player
            n_mafia = 1

        while count < n_mafia:
            roles.append(role_goon)
            count += 1

        # Town roles
        count = 0
        n_town = p_num - n_mafia

        while count < n_town:
            roles.append(role_vanilla)
            count += 1

        return roles

    def roleDist(self, roles):
        """Distribute roles to players."""
        # Assign roles
        random.shuffle(roles)
        i = 0
        for p in self.players:
            self.players[p].role = roles[i]
            i += 1

        # The mafia as a whole has one action
        self.actions += 1

    def rollRoles(self):
        """Determines peoples roles."""
        roles = self.roleGen()
        self.roleDist(roles)

    def getPlayers(self):
        """Returns player data as a dict."""
        return self.players

    def nextRound(self):
        """Increments the round number, and returns it."""
        self.round += 1
        return self.round

    def setDay(self):
        """Sets the game status to 'Day'."""
        self.phase = self.DAY

    def clear(self):
        """Clears data that doesn't need to be kept between phases."""
        for p in self.players:
            self.players[p].vote = None
            self.players[p].voted_by = []
            self.players[p].role.ab_target = None

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

    def getMajority(self):
        """Determine and return majority."""
        # Majority is > 50%, which can be determined by total / 2 + 1
        self.majority = len(self.players) / 2 + 1
        return self.majority

    def getMafia(self):
        """Returns a list of players with the alignment, 'Mafia'."""
        mafia = []
        for player, data in self.players.iteritems():
            if data.role.alignment == "Mafia":
                mafia.append(player)
        return mafia

    def resVote(self, target):
        """Return True if the target player has been lynched, else False."""
        # Voted for a player
        if target in self.players:
            if len(self.players[target].voted_by) >= self.majority:
                return True
            
        # Voted for 'No Lynch'
        else:
            if len(self.nl_voted) >= self.majority:
                return True

        return False

    def addVote(self, target, user):
        """Adds a vote to target player. Return True if the target player was
        lynched after this vote, else return False."""

        user = user.lower()
        target = target.lower()

        # Check player exists
        if target not in self.nl_alias and target not in self.players:
            raise "Player {} not found when assigning vote.".format(target)

        # Remove previous vote, if any
        old = self.players[user].vote
        if old is not None and old not in self.nl_alias:
            # Previously voted for a player
            self.players[old].voted_by.remove(user)
        elif old is not None:
            # Previously voted for 'No Lynch'
            self.nl_voted.remove(user)

        # Add new vote
        self.players[user].vote = target
        if target not in self.nl_alias:
            # Voted for a player
            self.players[target].voted_by.append(user)
        else:
            # Voted for 'No Lynch'
            self.nl_voted.append(user)
            
        return self.resVote(target)

    def getNoLynchAliases(self):
        """Return a list of aliases for 'No Lynch'."""
        return self.nl_alias


class MafiaBot(irc.IRCClient):
    """A bot which manages a mafia game."""

    nickname = "Mafiabot"  # TODO - make an argument parameter
    password = None  # TODO - make an argument parameter
    sourceURL = ""  # TODO - fill in later

    MIN_PLAYERS = 1  # DEBUG TODO - set to 1 for debugging purposes - set to 5
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
        user = user.split('!', 1)[0]

        # Check for a command
        if msg.startswith('!'):
            line = msg[1:]
        else:
            return

        # Check if a second argument has been provided
        try:
            target = line.split()[1]
        except:
            target = ""

        # For commands where parameters may be outputted, the original input
        # needs to be kept
        command = line.lower().split()[0]

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
                           + user + ". Thanks for playing!")
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
                           + user + ". Thanks for playing!")
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
            if target and self.game.transferGop(user, target):
                # Success
                msg = ("GOP has been transferred from "
                       "{} to {}.".format(user, target))
            elif not target:
                # Second argument not provided
                msg = "Failed as no player name was provided."
            else:
                # Other failure
                msg = ("Failed to transfer GOP. Are you sure you have GOP, "
                        "and that the player '{}' exists?".format(target))
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
                    msg = "{} has joined the game.".format(user)
                elif self.game.numPlayers() > self.MAX_PLAYERS:
                    # Too many players
                    msg = ("{} failed to join the game as the game capacity "
                           "reached the cap.")
                else:
                    # Already signed up
                    msg = ("Failed to join the game, as {} ".format(user)
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
                    msg = "{} has left the game.".format(user)
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
                    msg = ("Failed to leave the game, as {} ".format(user)
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
                self.gameStart(channel)
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
        elif command == "vote":
            # Change one's vote
            # TODO - move the next line into its own function
            exist = (target.lower() in self.game.getLivingPlayers() or
                     target.lower() in self.game.getNoLynchAliases())
            lynched = False
            if self.nickname.lower() == channel:
                # Can't start via private message
                msg = ("You cannot use this command via PM.")
            elif self.game.getPhase() != self.game.getDay():
                # Day phase only command
                msg = "This command can only be used in the Day Phase."
            elif not exist:
                # Target not found
                msg = ("Invalid voted. Player "
                       "'{}' not found.".format(target))
            else:
                lynched = self.game.addVote(target, user)
                msg = ""
            self.msg_send(self.nickname, channel, user, msg)

            # Someone lynched? # TODO - up to here
            if lynched != False:
                # Vote is sufficient to lynch someone
                self.rollNight(channel, target)
        
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

    def gameStart(self, channel):
        self.game.rollRoles()
        self.outRoles()
        self.rollDay(channel)
        # TODO - game start flavour

    def rollDay(self, channel):
        """Roll a new day phase."""
        self.newPhaseAct()
        self.game.setDay()
        majority = self.game.getMajority()
        p_num = self.game.numPlayers()
        r = self.game.nextRound()

        # Day flavour
        msg = "Another day rises on the townsfolk."
        self.msg(channel, msg)
        self.newDayDeathFlav()
        msg = ("It is now Day {}. With {} people alive, ".format(r, p_num) +
               "it will take {} votes for majority to be ".format(majority) +
               "reached.")
        self.msg(channel, msg)
        

    def newPhaseAct(self):
        """Performs actions required at the start of every phase."""
        self.game.clear()
        vict = self.game.detVictory()
        if vict is not None:
            # Victory achieved
            self.victory()
            # TODO - will need to terminate out of enveloping functions

    def victory(self):
        """Winning proceedings."""
        pass

    def newDayDeathFlav(self):
        pass

    def outRoles(self):
        """Gives players their role information."""
        players = self.game.getPlayers()
        mafia = self.game.getMafia()
        for p_name, data in players.iteritems():
            r_name = data.role.r_name
            align = data.role.alignment
            msg = "You are a(n) {} {}.\n".format(align, r_name)

            # Mafia information
            if align == "Mafia":

                # Teammates
                msg += "Your team is composed of:\n"
                for m in mafia:
                    msg += "{}\n".format(m)
                msg += "And you may PM them at any time.\n"

                # Kill
                msg += ("The mafia alignment has a kill shared between them, "
                        "which can be used during the night phase with the "
                        "command:\n/msg "
                        "{} <kill target>.".format(self.nickname))

            self.msg(p_name, msg)

    def rollNight(self, channel, target):
        """Rolls a new night phase."""
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
        "connection failed:", reason
        reactor.stop()


if __name__ == '__main__':
    # Create factory protocol and application
    bot = MafiaBotFactory("mtest")

    # Connect factory to this host and port
    reactor.connectTCP("irc.mibbit.com", 6667, bot)

    # Run bot
    reactor.run()
