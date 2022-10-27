from core.machine import Enigma


# Compute the known plaintext score of a text
def calc_kpscore(plaintext, text):
    score = sum(1 for i in range(len(text)) if text[i] == plaintext[i])
    return score


# Select configurations using a known plaintext
def kp_attack(fplaintext, ftext, configs):
    gen, *opts = configs
    for conf in gen(*opts):
        machine = Enigma(conf['Reflector'], conf['Rotors'], conf['Ring'], conf['Plugboard'], conf['Positions'])
        processed = machine.crypt(ftext)
        
        if processed == fplaintext:
            yield conf


# Select the n closest configurations from a known plaintext (and sort them by score)
def kp_score_attack(n, fplaintext, ftext, configs):
    nconfs = []
    
    gen, *opts = configs
    for conf in gen(*opts):
        machine = Enigma(conf['Reflector'], conf['Rotors'], conf['Ring'], conf['Plugboard'], conf['Positions'])
        processed = machine.crypt(ftext)
        
        score = calc_kpscore(fplaintext, processed)
        
        if len(nconfs) < n or score >= nconfs[-1][1]:
            if len(nconfs) < n:
                nconfs.append((conf, score))
            else:
                nconfs[-1] = (conf, score)
            i = len(nconfs)-2
            while i >= 0 and nconfs[i][1] < score:
                nconfs[i], nconfs[i+1] = nconfs[i+1], nconfs[i]
                i -= 1
    
    for c, _ in nconfs:
        yield c