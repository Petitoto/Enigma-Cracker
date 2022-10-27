from core.constants import ALPHABET
from core.machine import Enigma

n_ALPHABET = len(ALPHABET)

# Recover ring settings from rotors bad length
def recover_ring(blocks, configs):
    gen, *opts = configs
    for conf, (pos, block) in zip(gen(*opts), blocks):
        reflector, rotors, ring, plugboard, positions = conf['Reflector'], conf['Rotors'], conf['Ring'], conf['Plugboard'], conf['Positions']
        machine = Enigma(reflector, rotors, ring, plugboard, positions)
        
        size = block
        rotor_i = -1
        while size >= n_ALPHABET:
            size = round(size / n_ALPHABET)
            rotor_i -= 1
        
        for _ in range(pos+block):
            machine.turnrotors()
        
        if rotor_i == -2 and len(rotors) >= 3:   # Double stepping
            size += len(machine.rotors[rotor_i].notches)
        
        if not machine.rotors[rotor_i].turnover():
            size = n_ALPHABET - size
        
        positions = list(positions)
        positions[rotor_i] = ALPHABET[(ALPHABET.index(positions[rotor_i]) + size) % n_ALPHABET]
        conf['Positions'] = ''.join(positions)
        
        ring = ring.split()
        ring[rotor_i] = str((int(ring[rotor_i]) + size - 1) % n_ALPHABET + 1)
        conf['Ring'] = ' '.join(ring)
        
        yield conf