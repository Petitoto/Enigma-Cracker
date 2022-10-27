from itertools import product, combinations
from copy import deepcopy

from core.constants import ALPHABET

n_ALPHABET = len(ALPHABET)

# Generate all configurations according to the specified model
def gen_configs(model, progressBar=None):
    rotors_possibilities = []
    for rotor_i in model['Rotors']:
        rotors_possibilities.append(rotor_i.split())
    
    rotors_n = model['RotorsCount']
    confs = product(model['Reflectors'].split(), *rotors_possibilities, *(ALPHABET,)*rotors_n)
    
    for conf in confs:
        if model['Duplicates'] or len(set(conf[1:rotors_n+1])) == len(conf[1:rotors_n+1]):
            if progressBar:
                progressBar.inc()
            yield {'Reflector':conf[0], 'Rotors':' '.join(conf[1:rotors_n+1]), 'Ring':'1 1 1', 'Plugboard':'', 'Positions':''.join(conf[rotors_n+1:])}


# Count configurations generated by gen_configs
def gen_configs_count(model):
    if model['Duplicates']:
        n = 1
        for r in model['Rotors']:
            n *= len(r.split())
    
    else:
        n = 0
        rotors_possibilities = []
        for rotor_i in model['Rotors']:
            rotors_possibilities.append(rotor_i.split())
        rotors = product(*rotors_possibilities)
        for rotors in rotors:
            if len(set(rotors)) == len(rotors):
                n +=1
    
    n *= len(model['Reflectors'].split()) * n_ALPHABET**model['RotorsCount']
    return n


# Add a plug to each configuration
def gen_plugs(configs):
    gen, *opts = configs
    for conf in gen(*opts):        
        remaining_alphabet = ALPHABET
        for l in conf['Plugboard'].replace(' ',''):
            remaining_alphabet = remaining_alphabet.replace(l, '')
        
        for p in combinations(remaining_alphabet, 2):
            newconf = deepcopy(conf)
            plugs = ' '.join(conf['Plugboard'].split() + [p[0]+p[1]])
            newconf['Plugboard'] = plugs
            yield newconf


# Generate ring settings
def gen_ring(ringonly, configs):
    gen, *opts = configs
    for conf in gen(*opts):        
        rings = product(range(1,27), repeat=len(conf['Ring'].split()))
        for r in rings:
            newconf = deepcopy(conf)
            r = [str(e) for e in r]
            newconf['Ring'] = ' '.join(r)
            
            if not ringonly:
                newpos = []
                for i in range(len(r)):
                    shift = int(r[i]) - int(conf['Ring'].split()[i])
                    pos = ALPHABET.index(conf['Positions'][i])
                    newpos.append(ALPHABET[(pos + shift) % n_ALPHABET])
                newconf['Positions'] = ''.join(newpos)
            
            yield newconf