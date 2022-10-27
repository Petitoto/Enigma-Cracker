from core.constants import ALPHABET
from core.machine import Enigma


# Generate chains lengths from double encrypted keys
def rejewski_chains(keys, n):
    links = [{l: None for l in ALPHABET} for _ in range(n)]
    for k in keys.split():
        for i in range(n):
            links[i][k[i]] = k[i+n]
    
    chains = [[] for _ in range(n)]
    for i in range(n):
        for k in range(len(ALPHABET)):
            l0 = ALPHABET[k]
            
            chain = 1
            l = l0
            while l and links[i][l] != l0:
                l1, links[i][l] = links[i][l], None
                l = l1
                chain += 1
            
            if l:
                chains[i].append(chain)
    
    for c in chains:
        c.sort()
    
    return chains


# Select configurations compatible with Rejewski's characteristics
def rejewski_attack(chains, configs):
    n = len(chains)
    chains_set = [set(chains[i]) for i in range(n)]
    
    gen, *opts = configs
    for conf in gen(*opts):
        if n != len(conf['Rotors'].split()):
            continue
        
        keys = []
        for l in ALPHABET:
            machine = Enigma(conf['Reflector'], conf['Rotors'], conf['Ring'], conf['Plugboard'], conf['Positions'])
            keys.append(machine.crypt(l*2*n))
        
        conf_chains = rejewski_chains(' '.join(keys), n)
        
        valid = True
        for i in range(n):
            for e in chains_set[i]:
                valid = valid and (chains[i].count(e) <= conf_chains[i].count(e))
        if valid:
            yield conf