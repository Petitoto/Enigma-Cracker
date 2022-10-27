from core.constants import ALPHABET
from core.machine import Enigma


# Encrypt text + compute scores
def crypt(reflector, rotors, ring, plugboard, positions, ftext):
    machine = Enigma(reflector, rotors, ring, plugboard, positions)
    processed = machine.crypt(ftext)    
    return processed


# Count the letters that Enigma can process
def count(text):
    n = sum([1 for c in text if c.upper() in ALPHABET])
    return n


# Turn / roll back rotors
def turn_rotors(n, configs):
    gen, *opts = configs
    for conf in gen(*opts):        
        machine = Enigma(conf['Reflector'], conf['Rotors'], conf['Ring'], conf['Plugboard'], conf['Positions'])
        
        if n > 0:
            for _ in range(n):
                machine.turnrotors()
            conf['Positions'] = machine.dump_conf()[4]
            yield conf
        
        else:
            machines = [machine]
            for _ in range(-n):
                newmachines = machines
                for i, machine in enumerate(machines):
                    m = machine.rturnrotors()
                    if m and m != -1:
                        newmachines.append(m)
                    elif m == -1:
                        del newmachines[i]
                machines = newmachines
            
            for machine in machines:
                conf = {}
                conf['Reflector'], conf['Rotors'], conf['Ring'], conf['Plugboard'], conf['Positions'] = machine.dump_conf()
                yield conf