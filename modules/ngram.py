from math import log10

from core.machine import Enigma


# Compute the ngram score of a text
def calc_ngramscore(nsize, ngrams, text):
    processed_ngrams = (text[i:i+nsize] for i in range(len(text) - (nsize-1)))
    score = sum(log10(ngrams[gram]) for gram in processed_ngrams if gram in ngrams)  # NB: for unknown ngrams => ngrams[??] = 1
    return score


# Select n configuraitons with highest ngram score (and sort them by score)
def ngram_n_attack(n, nsize, ngrams, ftext, configs):
    nconfs = []
    
    gen, *opts = configs
    for conf in gen(*opts):        
        machine = Enigma(conf['Reflector'], conf['Rotors'], conf['Ring'], conf['Plugboard'], conf['Positions'])
        processed = machine.crypt(ftext)
        
        score = calc_ngramscore(nsize, ngrams, processed)
        
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