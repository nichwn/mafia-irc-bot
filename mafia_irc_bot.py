#TODO - override notices?
#TODO - !help or /msg HELP etc.
#TODO - check getEtc. rather than etc.

"""

An IRC bot which manages Mafia games.

"""

from twisted.words.protocols import irc
from twisted.internet import reactor, protocol


class Role:
    """Stores role information."""

    def __init__(self, r_name, alignment, ab_active, gop):
        self.r_name = r_name
        self.alignment = alignment
        self.ab_active = ab_active
        self.gop = gop
        self.ab_target = None


class Player:
    """Stores player information."""

    def __init__(self, status, role):
        self.status = status
        self.role = role
        self.vote = []
        self.voted_by = []


class MafiaGame:
    """Handles the mafia game."""

    player_list = []
    player_data = []

    #Flags for game states
    INITIAL = 0
    SIGN_UP = 1
    DAY = 2
    NIGHT = 3

    state = INITIAL


    def newGame(self):
        """Start a new game."""
        self.state = SIGN_UP

    def commands(self):
        """Returns a list of currently available commands and how to use
        them."""
        #TODO - implement
        pass

    def getPhase():
        """Returns a flag that indicates the current phase."""
        return self.status

    def getSign_Up():
        """Returns a flag that indicates the initial phase."""
        return self.INITIAL

    def getSign_Up():
        """Returns a flag that indicates the sign_up phase."""
        return self.SIGN_UP

    def getSign_Up():
        """Returns a flag that indicates the day phase."""
        return self.DAY

    def getSign_Up():
        """Returns a flag that indicates the night phase."""
        return self.NIGHT

    def end(user):
        pass
        #TODO - implement


class MafiaBot:
    """A bot which manages a mafia game."""

    nickname = "Mafiabot"
    sourceURL = ""  # TODO - fill in later
    
    game = MafiaGame()


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
        """Parse and interpret commands."""
        user = user.split('!', 1)

        #Check if it is a command
        if msg.startswith('!'):
            command = msg[1:].lower()
        elif msg.startswith(user + ": !"):
            command = msg[len(user) + 4:].lower()
        elif msg.startswith(user + ":!"):
            command = msg[len(user) + 3].lower()
        else:
            return;

        #Interpret command
        if command == "new":
            #Attempt to start a new game
            if channel != self.nickname and self.game.status == INITIAL:
                #Start a new game
                self.game.newGame()
                msg = ("A new mafia game has begun! Type !join to join. There is "
                       "minimum of 5, and a maximum of 12 players that can play.\n "
                       "The game starter has been given Game Operator (GOP) status "
                       "and can commence the game by typing !start")
                
            elif self.game.status != INITIAL:
                #Can't start a new game as one is already in progress
                msg = ("A game is already in progress. Wait for it to finish "
                       "before starting a new one.\nIf you'd like to end a "
                       "game early, you can type !end to end the game, or "
                       "!restart to restart the game if you're the GOP.")
                
            else:
                #Can't start a new game, as we don't know what channel to play
                #it in
                msg = ("You can't start a game with a PM. Please try again "
                       "in the channel you'd like to play in.")
            self.msg(channel, msg)

        elif command == "help":
            #Help requested. Output usable commands.
            #TODO - implement
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

        elif command == "end":
            #Attempt to end the game
            if channel != self.nickname:
                if self.game.end():
                    #Success
                    msg = ("The game has been closed early by request of "
                           + user + ". Thanks for playing!")
                else:
                    msg = ("Failed to end the game. Are you sure that a game "
                           "is running, and that you're the GOP?")
            else:
                msg = ("This command cannot be sent via PM.")
            self.msg(channel, msg)

        elif command == "":

        

            
        #TODO - add more commands


    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        #TODO - change name in player lists etc.
