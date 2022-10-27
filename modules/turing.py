from copy import deepcopy

from core.constants import ALPHABET
from core.utils import InvalidCommand
from core.machine import Enigma


# Generate the menu for a crib and get the most connected node
def gen_menu(crib, ftext):
    menu = {}
    for i in range(len(crib)):
        for (t1, t2) in [(ftext, crib), (crib, ftext)]:
            if not t1[i] in menu:
                menu[t1[i]] = []
            menu[t1[i]].append((i, t2[i]))
    
    def dfs(first, prec, cur):
        loops = []
        prec = prec[:]
        prec.append(cur)
        for _, n in menu[cur]:
            if n == first and n not in prec[-2:]:
                loops.append(1)
            if n not in prec:
                loops_n = dfs(first, prec, n)
                for l in loops_n:
                    loops.append(l+1)
        return loops
    
    max = (ALPHABET[0], 0, 0)
    for n in menu.keys():
        loops = dfs(n, [], n)
        if len(loops) > max[1]:
            max = (n, len(loops), sum(loops))
        elif len(loops) == max[1] and sum(loops) > max[2]:
            max = (n, len(loops), sum(loops))
    
    return menu, max[0], max[1]//2


# Select configurations compatible with a menu generated from a crib (using Turing's bombe)
# Hypothesis : node is fixed by the plugboard
def crib_attack(menu, node, configs):
    bombe = Bombe(menu)
    
    gen, *opts = configs
    for conf in gen(*opts):
        bombe.desenergize()
        bombe.set_conf(conf['Reflector'], conf['Rotors'], conf['Ring'], conf['Positions'])
        bombe.energize(node, node)
        if bombe.check_stop(node):
            plugboard = bombe.get_plugboard()
            conf['Plugboard'] = plugboard
            yield conf


# Turing's Bombe
class Bombe:
    def __init__(self, menu):
        self.bus = {bus: Bus(bus, menu[bus]) if bus in menu else Bus(bus) for bus in ALPHABET}
        self.scrambler = None
        self.diagonalboard = DiagonalBoard()
    
    def set_conf(self, reflector, rotors, ring, positions):
        self.scrambler = Scrambler(reflector, rotors, ring, positions)
    
    def energize(self, bus, key):
        if not self.scrambler: raise InvalidCommand('Missing Enigma configuration for scramblers')
        
        if not self.bus[bus].keys[key].energized:
            self.bus[bus].keys[key].energized = True
            
            wires = []
            wires.append(self.diagonalboard.get(bus, key))
            for pos, wbus in self.bus[bus].connections:
                wkey = self.scrambler.get(pos, key)
                wires.append((wbus, wkey))
            
            for wbus, wkey in wires:
                self.energize(wbus, wkey)
    
    def desenergize(self):
        for bus in self.bus.values():
            for key in bus.keys.values():
                key.energized = False
    
    def check_stop(self, bus):
        energized = []
        for k in self.bus[bus].keys.values():
            if k.energized:
                energized.append(k.key)
        
        if len(energized) == 1:
            return energized[0]
        
        elif len(energized) == len(ALPHABET)-1:
            k = 0
            while k < len(ALPHABET) and ALPHABET[k] in energized:
                k += 1
            return ALPHABET[k]
        
        else:
            return None
    
    def get_plugboard(self):        
        plugboard = []
        for bus in ALPHABET:
            key = self.check_stop(bus)
            if key and not key+bus in plugboard:
                plugboard.append(bus+key)
        
        return ' '.join(plugboard)


class Bus:
    def __init__(self, letter, connections=[]):
        self.letter = letter
        self.keys = {k: Key(k) for k in ALPHABET}
        self.connections = connections


class Key:
    def __init__(self, key):
        self.key = key
        self.energized = False


class Scrambler:
    def __init__(self, reflector, rotors, ring, positions):
        self.reflector = reflector
        self.rotors = rotors 
        self.ring = ring
        self.positions = positions
        self.computed = {}
    
    def get(self, pos, key):
        if not pos in self.computed.keys():
            enigma = Enigma(self.reflector, self.rotors, self.ring, '', self.positions)
            for _ in range(pos+1):
                enigma.turnrotors()
            self.computed[pos] = enigma
        
        else:
            enigma = self.computed[pos]
        
        return enigma.crypt_key(key)


class DiagonalBoard:
    def get(self, bus, key):
        return key, bus