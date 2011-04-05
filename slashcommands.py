from dice import DiceParser, DiceRoller
from models.sessionmodels import *

# Creates SlashCommandHandlers
class SlashCommandHandlerFactory:
    @staticmethod
    def create(command, session, user):
        if command == "/roll":
            return SlashRollCommandHandler()
        elif command == "/nick":
            return SlashNickCommandHandler(session, user)
        else:
            return UnknownSlashCommandHandler()
    
# Handles slash commands
class SlashCommandHandler:
    def handle(self, command, args): 
        abstract
        
class SlashNickCommandHandler(SlashCommandHandler):
    def __init__(self, session, user):
      self.session = session
      self.user = user
      
    def handle(self, command, args):
        for player in self.session.players:
          if player.user == self.user:
            old_nickname = player.nickname
            player.nickname = args
            player.put()
            return old_nickname  + " changed name to " + player.nickname
        return "unknown player"
        
# Handles a "/roll 1d20" styled command
class SlashRollCommandHandler(SlashCommandHandler):
    parser = DiceParser()
    roller = DiceRoller()
    
    def handle(self, command, args):
        dc, sc = SlashRollCommandHandler.parser.parse(args)
        total, individuals = SlashRollCommandHandler.roller.roll(dc, sc)
        if dc > 1:
            return "Roll %s: %s (%i)" % (args, str(individuals), total)
        else:
            return "Roll %s: %i" % (args, total)

# Handles an unknown command
class UnknownSlashCommandHandler(SlashCommandHandler):
    def handle(self, command, args):
        return "Unknown slash command: %s" % command
