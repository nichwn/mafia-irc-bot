#TODO - help messages
#TODO - delete player.vote? A loop through player votes might be less of a
#       hassle than dealing with it all the time.
#TODO - override notices
#TODO - manage kicked/disconnected players
#TODO - change GOP on player death
#TODO - add parameters etc. for nickname, channel, passwords and so forth
#TODO - add the cop role

"""

An IRC bot which manages Mafia games.

"""

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol

import sys
import random


class Role:
    """
    Stores role information.
    """

    def __init__(self, r_name, alignment, ab_active):
        self.r_name = r_name
        self.alignment = alignment
        self.ab_active = ab_active
        self.ab_target = None


class Player:
    """
    Stores player information.
    """

    def __init__(self, user, state="alive", role=None):
        self.name_case = user
        self.state = state
        self.role = role
        self.vote = None
        self.voted_by = []


class MafiaGame:
    """
    Handles the mafia game.
    """

    #Flags for game states
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
        self.used_actions = 0
        self.nl_alias = ["Nobody", "No-one", "Noone", "No_Lynch"]
        self.nl_voted_by = []
        self.phase = self.INITIAL
        self.mkill = None

    def newGame(self, user):
        """
        Start a new game.
        """
        self.phase = self.SIGN_UP
        self.gop = user.lower()
        self.players[self.gop] = Player(user)

    def commands(self):
        """
        Returns a list of currently available commands and how to use
        them.
        """
        #TODO - implement
        pass

    def getPhase(self):
        """
        Returns a flag that indicates the current phase. It's guaranteed
        that the flag values are in the order of:

        Initial < Sign_Up < Day < Night
        """
        return self.phase

    def getInitial(self):
        """
        Returns a flag that indicates the initial phase. It's guaranteed
        that the flag values are in the order of:

        Initial < Sign_Up < Day < Night
        """
        return self.INITIAL

    def getSign_Up(self):
        """
        Returns a flag that indicates the sign_up phase. It's guaranteed
        that the flag values are in the order of:

        Initial < Sign_Up < Day < Night
        """
        return self.SIGN_UP

    def getDay(self):
        """
        Returns a flag that indicates the day phase. It's guaranteed
        that the flag values are in the order of:

        Initial < Sign_Up < Day < Night
        """
        return self.DAY

    def getNight(self):
        """
        Returns a flag that indicates the night phase. It's guaranteed
        that the flag values are in the order of:

        Initial < Sign_Up < Day < Night
        """
        return self.NIGHT

    def end(self, user):
        """
        Attempts to end the game. Return True if the game was ended.
        """
        if self.isGop(user):
            self.gameClear()
            return True
        else:
            return False

    def gameClear(self):
        """
        Clears the game data in preparation for a new game.
        """
        self.players = {}
        self.phase = self.INITIAL
        self.round = 0
        self.actions = 0
        self.used_actions = 0
        self.nl_voted_by = []
        self.mkill = None

    def transferGop(self, user, target):
        """
        Transfer GOP to a target player.
        """
        user = user.lower()
        target = target.lower()
        if user == self.gop and target in self.players:
            self.gop = target
            return True
        else:
            return False

    def getLivingPlayers(self):
        """
        Return a list of all living players.
        """
        alive = []
        for v in self.players.itervalues():
            #Iterate through all the players
            if v.state == "alive":
                #Living player found
                alive.append(v.name_case)
        return alive

    def join(self, user):
        """
        Adds a player to the player list, if not already in it.
        """
        luser = user.lower()
        if luser not in self.players:
            self.players[luser] = Player(user)
            return True
        else:
            return False

    def leave(self, user):
        """
        Removes a player from the player list, if possible.
        """
        user = user.lower()
        if user in self.players:
            del self.players[user]
            return True
        else:
            return False

    def numPlayers(self):
        """
        Determines if there are players left.
        """
        return len(self.players)

    def newGop(self):
        """
        Changes the GOP. There must be at least one living player.
        """
        #TODO - add proper error message
        self.gop = self.players.keys()[0]
        return players[self.gop].name_case

    def isGop(self, user):
        """
        Determine if the user is GOP.
        """
        return user.lower() == self.gop

    def roleGen(self):
        """
        Generate player roles, and return them.
        """
        role_vanilla = Role("Vanilla", "Town", None)
        role_goon = Role("Goon", "Mafia", None)

        #Construct role list
        roles = []
        p_num = self.numPlayers()

        #Mafia roles
        count = 0
        if p_num >= self.THIRD_MAFIA:
            #3 mafia players
            n_mafia = 3
        elif p_num >= self.SECOND_MAFIA:
            #2 mafia players
            n_mafia = 2
        else:
            #1 mafia player
            n_mafia = 1

        while count < n_mafia:
            roles.append(role_goon)
            count += 1

        #The mafia as a whole have one action
        self.actions += 1

        #Town roles
        count = 0
        n_town = p_num - n_mafia

        while count < n_town:
            roles.append(role_vanilla)
            count += 1

        return roles

    def roleDist(self, roles):
        """
        Distribute roles to players.
        """
        #Assign roles
        random.shuffle(roles)
        i = 0
        for p in self.players:
            self.players[p].role = roles[i]
            i += 1

    def rollRoles(self):
        """
        Determines peoples roles.
        """
        roles = self.roleGen()
        self.roleDist(roles)

    def getPlayers(self):
        """
        Returns player data as a dict.
        """
        return self.players

    def nextPhase(self):
        """
        Sets the phase to 'Day' if it isn't already. Else, set to 'Night'.
        Return the round number.
        """
        if self.phase != self.DAY:
            self.phase = self.DAY
            self.round += 1
        else:
            self.phase = self.NIGHT
        return self.round

    def setDay(self):
        """
        Sets the game status to 'Day'.
        """
        self.phase = self.DAY

    def setNight(self):
        """
        Sets the game status to 'Night'.
        """
        self.phase = self.NIGHT

    def clear(self):
        """
        Clears data that doesn't need to be kept between phases.
        """
        for p in self.players:
            self.players[p].vote = None
            self.players[p].voted_by = []
            self.players[p].role.ab_target = None
        self.used_actions = 0
        self.mkill = None

    def detVictory(self):
        """
        Determines if an alignment has won. Return None if no alignment has.
        """
        #Tally up
        mafia = 0
        align = []
        for data in self.players.values():
            align.append(data.role.alignment)
            if data.role.alignment == "Mafia":
                mafia += 1

        #Determine victory
        if mafia == 0:
            return "Town"
        elif mafia * 2 >= len(align):
            return "Mafia"
        return None

    def getMajority(self):
        """
        Determine and return majority.
        """
        #Majority is > 50%, which can be determined by total / 2 + 1
        self.majority = self.numPlayers() / 2 + 1
        return self.majority

    def resVote(self, target):
        """
        If the target player has the majority of votes on them, remove
        them and return their name, alignment and role name, except for a
        'No Lynch', which returns None. Return False if the condition has not
        been fulfilled.
        """
        #Voted for a player
        target = target.lower()
        if target in self.players:
            if len(self.players[target].voted_by) >= self.majority:
                return self.removePlayer(target)

        #Voted for 'No Lynch'
        else:
            if len(self.nl_voted_by) >= self.majority:
                return None

        return False

    def removePlayer(self, target):
        """
        Removes a player and returns their name, alignment and role name.
        """
        target = target.lower()
        name = self.players[target].name_case
        align = self.players[target].role.alignment
        role = self.players[target].role.r_name
        del self.players[target]
        return (name, align, role)

    def resolveNight(self):
        """
        Resolves night phase actions. Return the name, alignment and role
        of the mafia's target, or None otherwise.
        """
        if self.mkill is None:
            return None
        targ = self.mkill.lower()
        if targ in self.players:
            return self.removePlayer(targ)
        else:
            return None

    def delLower(self, seq, target):
        """
        Deletes the first occurence of target in a list (case insensitive).
        """
        i = [item.lower() for item in seq].index(target.lower())
        del seq[i]

    def addVote(self, target, user):
        """
        Adds a vote to target player. Return True if the target player was
        lynched after this vote, else return False (including if the target
        player isn't present).
        """

        luser = user.lower()
        ltarget = target.lower()
        lnl_alias = [i.lower() for i in self.nl_alias]
        lplayers = [i.lower() for i in self.players]

        #Check player exists
        if ltarget not in lnl_alias and ltarget not in lplayers:
            return False

        #Remove previous vote, if any
        old = self.players[luser].vote
        if old is not None and old.lower() in lplayers:
            #Previously voted for a player
            self.delLower(self.players[old.lower()].voted_by, user)
        elif old is not None:
            #Previously voted for 'No Lynch'
            self.delLower(self.nl_voted_by, user)

        #Add new vote
        self.players[luser].vote = target
        if ltarget in lplayers:
            #Voted for a player
            self.players[ltarget].voted_by.append(user)
        else:
            #Voted for 'No Lynch'
            self.nl_voted_by.append(user)

        return self.resVote(target)

    def getNoLynchAliases(self):
        """
        Return a list of aliases for 'No Lynch'.
        """
        return self.nl_alias

    def pExist(self, target):
        """
        Determines whether a player exists (or is an alias for 'No Lynch'/
        Nobody).
        """
        living = [p.lower() for p in self.getLivingPlayers()]
        nlalias = [a.lower() for a in self.getNoLynchAliases()]
        target = target.lower()

        if target in living or target in nlalias:
            return True
        else:
            return False

    def getVotes(self):
        """
        Returns a list of all votes with the format of:

        [[target, number of votes, voter1, voter2 (if any), ...], ...]

        Players without any votes are ignored. The elements will be sorted by
        the number of votes, and then by the target's name.
        """
        result = []

        #Search through every player
        for player in self.players:
            n_votes = len(self.players[player].voted_by)

            #Player with votes found
            if n_votes:
                result.append(self.calcIndiVote(self.players[player].name_case,
                                                n_votes,
                                                self.players[player].voted_by))

        #Add votes for 'No Lynch', if any
        n_votes = len(self.nl_voted_by)
        if n_votes:
            result.append(self.calcIndiVote(self.nl_alias[0], n_votes,
                                            self.nl_voted_by))

        result.sort(key=lambda item: (item[1], item[0]))
        return result

    def calcIndiVote(self, name, n_votes, votes):
        """
        Creates an element as specified by self.getVotes. Intended for use by
        self.getVotes only.
        """
        element = []
        element.append(name)
        element.append(n_votes)
        element.extend(votes)
        return element

    def mafiaKill(self, target, user):
        """
        Sets the target for the mafia kill, and if it succeeded,
        returns True.
        """
        #Check that the user is mafia
        mafia = [m.lower() for m in self.getPAlign()]
        if user.lower() not in mafia:
            return False

        #Check if the target player exists
        if not self.pExist(target):
            return False

        old = self.mkill
        self.mkill = target

        #Check if a previous target existed
        if old is None:
            self.used_actions += 1

        return True

    def detEndNight(self):
        """
        Returns True if all actions have been submitted.
        """
        if self.used_actions == self.actions:
            return True
        return False

    def isPlayer(self, user):
        """
        Returns True if the user is in the player list.
        """
        return user.lower() in self.players

    def getPAlign(self, align="Mafia"):
        """
        Returns a list of players with the alignment that matches align.
        """
        players = []
        for v in self.players.itervalues():
            if v.role.alignment == align:
                players.append(v.name_case)
        return players

    def nickChange(self, old_nick, new_nick):
        """
        Handles player nickname changes. If a conflict with the aliases "
        "for 'No Lynch' occurs, returns True and performs no actions. Else,
        return False.
        """
        lold_nick = old_nick.lower()
        lnew_nick = new_nick.lower()

        #Check for conflict
        if self.inNLAlias(lnew_nick):
            return True

        p_data = self.players.pop(lold_nick, None)

        #Not a player
        if p_data is None:
            return False

        #Update player storage
        p_data.name_case = new_nick
        self.players[lnew_nick] = p_data

        #Update player votes
        for p in self.players:
            if self.players[p].vote == old_nick:
                self.players[p].vote = new_nick

            try:
                i = self.players[p].voted_by.index(old_nick)
            except:
                pass
            else:
                self.players[p].voted_by[i] = new_nick

            try:
                j = self.nl_voted_by.index(old_nick)
            except:
                pass
            else:
                self.nl_voted_by[j] = new_nick

        #Update gop
        if self.gop == lold_nick:
            self.gop = lnew_nick

        return False

    def inNLAlias(self, nick):
        """
        Returns True if nick is in an alias for 'No Lynch'/'No Action'.
        Case insensitive.
        """
        if nick.lower() in [n.lower() for n in self.nl_alias]:
            return True


class MafiaBot(irc.IRCClient):
    """
    A bot which manages a mafia game.
    """

    nickname = "Mafiabot"  # TODO - make an argument parameter
    password = None  # TODO - make an argument parameter
    sourceURL = ""  # TODO - fill in later

    MIN_PLAYERS = 1  # DEBUG TODO - set to 1 for debugging purposes - set to 5
    MAX_PLAYERS = 12

    #Connection

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.game = MafiaGame()

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    #Events

    def signedOn(self):
        """
        After connecting to the server, join the channel.
        """
        self.join(self.factory.channel)

    def joined(self, channel):
        """
        After joining a channel, output a greeting.
        """
        msg = ("I'm a bot which manages mafia games. /say or PM me !help for "
               "help.")
        self.msg(channel, msg)

    def privmsg(self, user, channel, msg):
        """
        Parse and interpret commands.
        """

        #Usernames are stored in lowercase, but the original input needs to be
        #kept for message outputs
        user = user.split('!', 1)[0]

        #Check if a second argument has been provided
        try:
            target = msg.split()[1]
        except:
            target = ""

        #For commands where parameters may be outputted, the original input
        #needs to be kept
        farg = msg.lower().split()[0]

        #Interpret the entire command
        self.runCommand(farg, target, user, channel)

    def irc_NICK(self, prefix, params):
        """
        Called when an IRC user changes their nickname.
        """
        old_nick = prefix.split('!')[0]
        new_nick = params[0]

        #Check that the game has started
        if self.game.getPhase() > self.game.getSign_Up():
            shared = self.game.nickChange(old_nick, new_nick)
        else:
            shared = False

            #Check nobody
            if self.game.inNLAlias(new_nick):
                msg = ("As this nickname has been reserved as an alias for "
                       "'No Lynch' or 'No Action', {} ".format(new_nick) +
                       "will be removed from the game.\n")
                self.msg(self.gaChan, msg)
                self.comLeave(old_nick, self.gaChan, new_nick)

                #Reset GOP
                self.game.newGop()

        if shared:
            data = self.game.removePlayer(old_nick)

            #Reset phase actions
            self.resetPhaseAct(self.gaChan)
            majority = self.game.getMajority()

            #General message
            msg = ("As this nickname has been reserved as an alias for "
                   "'No Lynch' or 'No Action', {} ".format(new_nick) +
                   "has been removed from the game.\nThey were a "
                   "{} {}.\n".format(data[1], data[2]) + "All actions this "
                   "phase have been reset.\n")

            #Day only message
            if self.game.getPhase() == self.game.getDay():
                msg += "It will take {} votes for majority.".format(majority)

            self.msg(self.gaChan, msg)

            #Reset GOP
            self.game.newGop()

    #Other functions

    def runCommand(self, farg, target, user, channel):
        """
        Interprets and runs a given command.
        """

        isPlayer = self.game.isPlayer(user)

        if channel == self.nickname.lower():
            #Privately sent command
            self.comsPrivate(farg, target, user, isPlayer)
        else:
            #Publicly sent command:
            self.comsPublic(farg, target, user, channel, isPlayer)

    def comsPrivate(self, farg, target, user, isPlayer):
        """
        Interprets and runs private commands.
        """
        if isPlayer:
            if farg == "help":
                self.comHelp(user)
            elif farg == "alive":
                self.comAlive(user)
            elif farg == "kill":
                self.comKill(target, user, user)

    def comHelp(self, channel):
        """
        Gives help messages to the user.
        """
        curr_phase = self.game.getPhase()
        if curr_phase == self.game.getInitial():
            pass
        elif curr_phase == self.game.getSign_Up():
            pass
        elif curr_phase == self.game.getDay():
            pass
        elif curr_phase == self.game.getNight():
            pass
        #TODO - also print out 'anytime' commands

    def comKill(self, target, user, channel):
        """
        Registers the target for the mafia kill, and if it's the last
        action, rolls to the next round. Only works during the night phase.
        """
        #Check phase
        if self.game.getPhase() != self.game.getNight():
            return

        #Kill
        succ = self.game.mafiaKill(target, user)
        if succ:
            msg = "{} has now been targeted for the mafia kill.".format(target)
            for p in self.game.getPAlign():
                self.msg(p, msg)
        else:
            msg = ("Failed to designate {} ".format(target) +
                   "as the mafia kill target.")
            self.msg(channel, msg)

        #End of night phase?
        end_phase = self.game.detEndNight()
        if end_phase:
            self.rollToDay(self.gaChan)

    def comsPublic(self, farg, target, user, channel, isPlayer):
        """
        Interprets and runs public commands.
        """

        #All public commands must start with a '!' to distinguish them from
        #other messages
        if not farg.startswith('!'):
            return
        else:
            farg = farg[1:]

        #Run the command
        if isPlayer:
            if farg == "start":
                self.comStart(user, channel)
            elif farg == "vote":
                self.comVote(target, user, channel)
            elif farg == "votes":
                self.comVotes(user, channel)
            elif farg == "alive":
                self.comAlive(channel)

        if farg == "new":
            self.comNew(user, channel)
        elif farg == "end":
            self.comEnd(user, channel)
        elif farg == "restart":
            self.comRestart(user, channel)
        elif farg == "gop":
            self.comGop(target, user, channel)
        elif farg == "join":
            self.comJoin(user, channel)
        elif farg == "leave":
            self.comLeave(user, channel)

    def comNew(self, user, channel):
        """
        Attempts to begin a new game.
        """

        #Begin a new game
        if self.game.getPhase() == self.game.getInitial():

            self.game.newGame(user)
            self.gaChan = channel
            msg = ("A new mafia game has begun! Type !join to join. There "
                   "is a minimum of {}, and ".format(self.MIN_PLAYERS) +
                   "a maximum of {} players ".format(self.MAX_PLAYERS) +
                   "that can play.\nThe game starter has been given Game "
                   "Operator (GOP) status and can commence the game by "
                   "typing !start.")

        #Can't begin a new game as one is already in progress
        else:
            msg = ("A game is already in progress. Wait for it to finish "
                   "before starting a new one.\nIf you'd like to end a "
                   "game early, you can type !end to end the game, or "
                   "!restart to restart the game if you're the GOP.")
        self.msg(channel, msg)

    def comEnd(self, user, channel):
        """
        Attempt to end the game.
        """
        if (self.game.getPhase() != self.game.getInitial() and
                self.game.end(user)):
            #Success
            msg = ("The game has been closed early by request of "
                   + user + ". Thanks for playing!")
        elif self.game.getPhase() == self.game.getInitial():
            msg = "You can't end a game that hasn't started!"
        else:
            msg = ("Failed to end the game. Are you sure that a game "
                   "is running, and that you're the GOP?")
        self.msg(channel, msg)

    def comRestart(self, user, channel):
        """
        Attempt to restart the game.
        """
        restart = 0
        if (self.game.getPhase() != self.game.getInitial() and
                self.game.end(user)):
            #Success
            msg = ("The game has been closed early by request of "
                   + user + ". Thanks for playing!")
            restart = 1
        elif self.game.getPhase() == self.game.getInitial():
            msg = "You can't end a game that hasn't started!"
        else:
            msg = ("Failed to restart the game. Are you sure that a game "
                   "is running, and that you're the GOP?")
        self.msg(channel, msg)

        if restart:
            #Begin a new game
            msg = "!new"
            self.privmsg(user, channel, msg)

    def comGop(self, target, user, channel):
        """
        Request to transfer GOP.
        """
        if target and self.game.transferGop(user, target):
            #Success
            msg = ("GOP has been transferred from "
                   "{} to {}.".format(user, target))
        elif not target:
            msg = "Failed as no player name was provided."
        else:
            msg = ("Failed to transfer GOP. Are you sure you have GOP, "
                   "and that the player '{}' exists?".format(target))
        self.msg(channel, msg)

    def comAlive(self, channel):
        """
        Lists out the names of all living players.
        """
        if self.game.getPhase() > self.game.getSign_Up():
            #Game active, so determine living players
            msg = "Players alive:"
            for player in self.game.getLivingPlayers():
                    msg += '\n' + player
        else:
            #Game inactive
            msg = ("Failed, as this command only works during the main "
                   "section of the game.")
        self.msg(channel, msg)

    def comJoin(self, user, channel):
        """
        Attempt to join a new game.
        """
        if (self.game.numPlayers() <= self.MAX_PLAYERS and
                self.game.getPhase() == self.game.getSign_Up() and
                self.game.join(user)):

            #Joined!
            msg = "{} has joined the game.".format(user)
        elif self.game.numPlayers() > self.MAX_PLAYERS:
            #Too many players
            msg = ("{} failed to join the game as the game capacity "
                   "reached the cap.")
        elif self.game.getPhase() != self.game.getSign_Up():
            #Wrong phase
            msg = "Failed to join as sign-ups aren't open."
        else:
            #Already signed up
            msg = ("Failed to join the game, as {} ".format(user)
                   + "has already entered.")
        self.msg(channel, msg)

    def comLeave(self, user, channel, alt_name=None):
        """
        Attempt to leave a new game.
        """
        gop = self.game.isGop(user)
        if (self.game.getPhase() == self.game.getSign_Up() and
                self.game.leave(user)):

            #Left!
            if alt_name is None:
                msg = "{} has left the game.".format(user)
            else:
                msg = "{} has left the game.".format(alt_name)
            if self.game.numPlayers() == 0:
                #Players remaining?
                msg += (" As there are no players left the "
                        "game has been closed.")
                self.game.gameClear()
            elif gop:
                #Leaving playing was GOP. Select a new one.
                n_gop = self.game.newGop()
                msg += " {} is now GOP.".format(n_gop)

        elif self.game.getPhase() != self.game.getSign_Up():
            #Wrong phase
            msg = "Failed as you can only leave the game during sign-ups."
        else:
            #Not in game
            msg = ("Failed to leave the game, as {} ".format(user)
                   + "has not entered it.")
        self.msg(channel, msg)

    def comStart(self, user, channel):
        """
        Attempt to close sign-ups and start the game.
        """
        n_players = self.game.numPlayers()
        if (self.game.isGop(user) and
                self.MIN_PLAYERS <= n_players and
                self.game.getPhase() == self.game.getSign_Up()):
            #Closes sign ups and begins the game
            msg = ("Sign ups have been closed, and the game will begin "
                   "shortly. You should be receiving your roles now.")
            self.gameStart(channel)
            return
        elif self.game.getPhase() != self.game.getSign_Up():
            #Wrong phase
            msg = ("Failed to start the game, as it can only be done during "
                   "sign ups.")
        elif not self.game.isGop(user):
            #Only GOP can use this command
            msg = "Only the GOP can use this command."
        else:
            #Not enough players
            msg = ("Insufficient number of players. The minimum number "
                   "is {} and there is/are only ".format(self.MIN_PLAYERS) +
                   "{} player(s) signed up.".format(n_players))
        self.msg(channel, msg)

    def comVote(self, target, user, channel):
        """
        Change a player's vote target. Rolls to Night if a player is
        lynched.
        """
        exist = self.game.pExist(target)
        lynched = False
        if self.game.getPhase() != self.game.getDay():
            #Day phase only command
            msg = "This command can only be used in the Day Phase."
        elif not exist:
            #Target not found
            msg = ("Invalid vote. Player "
                   "'{}' not found.".format(target))
        else:
            lynched = self.game.addVote(target, user)
            msg = ""
        self.msg(channel, msg)

        #Someone lynched?
        if lynched:
            #Vote is sufficient to lynch someone
            self.rollToNight(lynched, channel)

    def comVotes(self, user, channel):
        """
        Outputs a list of all players with votes on them, how many, and who
        voted for them.
        """
        v_data = self.game.getVotes()
        msg = ""

        #Check for it being an appropriate phase
        if self.game.getPhase() != self.game.getDay():
            msg = "Failed, as there isn't a lynch being held right now."
            self.msg(channel, msg)
            return

        #Check for no votes:
        if not len(v_data):
            msg += "There have been no votes placed."

        #Format vote data for output
        for target in v_data:
            msg += "{} [{}]:".format(target[0], target[1])
            msg += " {}".format(target[2])
            target = target[3:]
            for voter in target:
                msg += ", {}".format(voter)
            msg += '\n'

        self.msg(channel, msg)

    def gameStart(self, channel):
        """
        Start the game.
        """
        self.game.rollRoles()
        self.outRoles()
        self.rollToDay(channel)

    def rollToDay(self, channel):
        """
        Roll a new day phase.
        """
        self.nightActFlav(channel)

        data = self.rollGeneral(channel)
        majority = self.game.getMajority()

        #End of game
        if data is None:
            return
        else:
            r, p_num = data

        msg = ("Another day rises on the townsfolk.\n"
               "It is now Day {}. With {} people alive, ".format(r, p_num) +
               "it will take {} votes for majority to be ".format(majority) +
               "reached.")
        self.msg(channel, msg)

    def rollToNight(self, lynched, channel):
        """
        Roll a new night phase.
        """
        if lynched is None:
            msg = "Nobody was lynched today.\n"
        else:
            name = lynched[0]
            align = lynched[1]
            role = lynched[2]
            msg = ("{} was lynched. They were a(n) ".format(name) +
                   "{} {}.\n".format(align, role))

        data = self.rollGeneral(channel)

        #End of game
        if data is None:
            return
        else:
            r, p_num = data

        msg += ("Night falls upon the town, and the townsfolk scurry back "
                "into their beds.\n")
        msg += ("It is now Night {}. There are currently ".format(r) +
                "{} people alive.".format(p_num))
        self.msg(channel, msg)

    def rollGeneral(self, channel):
        """
        Return requisite data to roll phases, and performs some new phase
        proceedings.

        Return format is:

        [round number, number of players]

        Or None if the game has ended
        """
        end = self.resetPhaseAct(channel)

        if end:
            return None

        r = self.game.nextPhase()
        p_num = self.game.numPlayers()
        return [r, p_num]

    def resetPhaseAct(self, channel):
        """
        Performs actions required to initialise every phase. Return
        True if the game has ended, else False.
        """
        self.game.clear()
        return None  # TODO - debug purposes only: remove
        vict = self.game.detVictory()
        if vict is not None:
            #Victory achieved
            self.victory(vict, channel)
            return True
        return False

    def victory(self, vict, channel):
        """
        Winning proceedings.
        """
        win_play = self.game.getPAlign(vict)

        msg = ("Game over! The winning alignment is: '{}'\n".format(vict) +
               "The winning players are:\n")
        for p in win_play:
            msg += "{}\n".format(p)
        msg += ("Thanks for playing! You may start a new game with the "
                "command !new.")
        self.msg(channel, msg)

        self.game.gameClear()

    def nightActFlav(self, channel):
        """
        Outputs night flavour resulting from player actions.
        """
        res = self.game.resolveNight()
        if res is not None:
            name, align, role = res
            msg = "{} was killed. They were a {} {}.".format(name, align, role)
        else:
            msg = ""
        self.msg(channel, msg)

    def outRoles(self):
        """
        Gives players their role information.
        """
        players = self.game.getPlayers()
        mafia = self.game.getPAlign()
        for p_name, data in players.iteritems():
            r_name = data.role.r_name
            align = data.role.alignment
            msg = "You are a(n) {} {}.\n".format(align, r_name)

            #Mafia information
            if align == "Mafia":

                #Teammates
                msg += "Your team is composed of:\n"
                for m in mafia:
                    msg += "{}\n".format(m)
                msg += "And you share teamspeak with them.\n"

                #Kill
                msg += ("The mafia alignment has a kill shared between them, "
                        "which can be used during the night phase with the "
                        "command:\n/msg "
                        "{} kill <kill target>.".format(self.nickname.lower()))

            self.msg(p_name, msg)


class MafiaBotFactory(protocol.ClientFactory):
    """
    A factory for MafiaBots.
    """

    def __init__(self, channel):
        self.channel = channel

    def buildProtocol(self, addr):
        bot = MafiaBot()
        bot.factory = self
        return bot

    def clientConnectionLost(self, connector, reason):
        """
        If we get disconnected, terminate the program.
        """
        reactor.stop()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()


if __name__ == '__main__':
    #Create factory protocol and application
    bot = MafiaBotFactory("mtest")

    #Connect factory to this host and port
    reactor.connectTCP("irc.mibbit.com", 6667, bot)

    #Run bot
    reactor.run()
