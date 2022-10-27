from .constants import ROTORS, REFLECTORS, ALPHABET

n_ALPHABET = len(ALPHABET)

class Enigma:
    def __init__(self, reflector, rotors, ring, plugboard, positions):
        self.rotors = []
        for rotor, r, pos in zip(rotors.split(), ring.split(), positions):
            wiring = ROTORS[rotor][0]
            notchs = ROTORS[rotor][1]
            self.rotors.append(Rotor(rotor, wiring, notchs, int(r), pos))
        
        self.reflector = Reflector(reflector, REFLECTORS[reflector])
        self.plugboard = Plugboard(plugboard.split())
    
    def dump_conf(self):
        rotors = ' '.join([rotor.name for rotor in self.rotors])
        reflectors = self.reflector.name
        ring = ' '.join([str(rotor.ring + 1) for rotor in self.rotors])
        plugboard = ' '.join(self.plugboard.plugboard)
        positions = ''.join([ALPHABET[rotor.position] for rotor in self.rotors])
        return reflectors, rotors, ring, plugboard, positions
    
    def crypt(self, text):
        enc = ''
        for key in text:
            self.turnrotors()
            enc += self.crypt_key(key)
        return enc
    
    def crypt_key(self, key):
        key = ALPHABET.index(key)
        k = self.plugboard.get(key)
        for r in reversed(self.rotors):
            k = r.get(k)
        k = self.reflector.get(k)
        for r in self.rotors:
            k = r.rget(k)
        k = self.plugboard.get(k)
        return ALPHABET[k]
    
    def turnrotors(self):
        if len(self.rotors) >= 3:
            if self.rotors[-2].turnover():
                self.rotors[-3].turn()
            if self.rotors[-2].turnover() or self.rotors[-1].turnover():
                self.rotors[-2].turn()
        
        elif len(self.rotors) == 2:
            if self.rotors[-1].turnover():
                self.rotors[-2].turn()
        
        self.rotors[-1].turn()
    
    def rturnrotors(self):
        self.rotors[-1].rturn()
        
        if len(self.rotors) >= 3:
            if self.rotors[-1].turnover():
                self.rotors[-2].rturn()
            if self.rotors[-2].turnover():
                if not self.rotors[-1].turnover():
                    return -1
                self.rotors[-3].rturn()
            
            if self.rotors[-2].rturnover():
                rotors, reflectors, ring, plugboard, positions = self.dump_conf()
                machine = Enigma(rotors, reflectors, ring, plugboard, positions)
                machine.rotors[-2].rturn()
                machine.rotors[-3].rturn()
                return machine
        
        elif len(self.rotors) == 2:
            if self.rotors[-1].turnover():
                self.rotors[-2].rturn()


class Rotor:
    def __init__(self, name='', wiring='ABCDEFGHIJKLMNOPQRSTUVWXYZ', notches=None, ring=1, position='A'):
        self.name = name
        self.wiring = [-1]*n_ALPHABET
        self.rwiring = [-1]*n_ALPHABET
        for i,w in enumerate(wiring):
            wi = ALPHABET.index(w)
            self.wiring[i] = wi
            self.rwiring[wi] = i
        self.notches = notches
        self.position = ALPHABET.index(position)
        self.ring = ring - 1
    
    def get(self, key):
        shift = self.position - self.ring
        index = (key + shift) % n_ALPHABET
        wired = self.wiring[index]
        return (wired - shift) % n_ALPHABET
    
    def rget(self, key):
        shift = self.position - self.ring
        index = (key + shift) % n_ALPHABET
        wired = self.rwiring[index]
        return (wired - shift) % n_ALPHABET
    
    def turnover(self):
        return ALPHABET[self.position] in self.notches
    
    def rturnover(self):
        rposition = (self.position-1) % n_ALPHABET
        return ALPHABET[rposition] in self.notches
    
    def turn(self):
        self.position = (self.position + 1) % n_ALPHABET
    
    def rturn(self):
        self.position = (self.position - 1) % n_ALPHABET


class Reflector:
    def __init__(self, name='', wiring='ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
        self.name = name
        self.wiring = [-1]*n_ALPHABET
        for i,w in enumerate(wiring):
            self.wiring[i] = ALPHABET.index(w)
    
    def get(self, key):
        return self.wiring[key]


class Plugboard:
    def __init__(self, plugboard):
        self.plugboard = plugboard
        self.plugs = {}
        for plug in plugboard:
            plug0, plug1 = ALPHABET.index(plug[0]), ALPHABET.index(plug[1])
            self.plugs[plug0] = plug1
            self.plugs[plug1] = plug0
    
    def get(self, key):
        if key in self.plugs:
            return self.plugs[key]
        return key