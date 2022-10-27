from core.constants import ALPHABET
from core.machine import Enigma


# Compute the index of coincidence of a text
def calcic(text):
    alphabetcount = 0
    total = len(text) * (len(text)-1)
    
    if total == 0:
        return 0
    
    for letter in ALPHABET:
        nq = text.count(letter)
        alphabetcount += nq * (nq-1)
    
    return alphabetcount/total


# Select configurations according to a minimum IC
def ic_attack(ic_min, ftext, configs):
    gen, *opts = configs
    for conf in gen(*opts):
        machine = Enigma(conf['Reflector'], conf['Rotors'], conf['Ring'], conf['Plugboard'], conf['Positions'])
        ic = calcic(machine.crypt(ftext))
        
        if ic >= ic_min:
            yield conf


# Select n configurations with highest IC (and sort them by IC)
def ic_n_attack(n, ftext, configs):
    nconfs = []
    
    gen, *opts = configs
    for conf in gen(*opts):        
        machine = Enigma(conf['Reflector'], conf['Rotors'], conf['Ring'], conf['Plugboard'], conf['Positions'])
        ic = calcic(machine.crypt(ftext))
        
        if len(nconfs) < n or ic >= nconfs[-1][1]:
            if len(nconfs) < n:
                nconfs.append((conf, ic))
            else:
                nconfs[-1] = (conf, ic)
            i = len(nconfs)-2
            while i >= 0 and nconfs[i][1] < ic:
                nconfs[i], nconfs[i+1] = nconfs[i+1], nconfs[i]
                i -= 1
    
    for c, _ in nconfs:
        yield c