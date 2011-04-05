import random
import re
    
class DiceRoller:
    def roll(self, diceCount, sideCount):
        total = 0
        a = []
        for _ in range(0, diceCount):
            v = random.randint(1, sideCount)
            a.append(v)
            total += v
        return total, a
    
# Parses 1d6 into (1, 6)
# Obviously needs error checking
class DiceParser:
    regex = re.compile("(?P<dc>\d+)d(?P<sc>\d+)")
    def parse(self, source):
        m = re.search(DiceParser.regex, source)
        return (int(m.group("dc")), int(m.group("sc")))