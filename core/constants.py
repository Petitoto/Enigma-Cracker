BANNER = '''\
  _____       _                              ____                _
 | ____|_ __ (_) __ _ _ __ ___   __ _       / ___|_ __ __ _  ___| | _____ _ __
 |  _| | '_ \| |/ _` | '_ ` _ \ / _` | ___ | |   | '__/ _` |/ __| |/ / _ \ '__|
 | |___| | | | | (_| | | | | | | (_| ||___|| |___| | | (_| | (__|   <  __/ |
 |_____|_| |_|_|\__, |_| |_| |_|\__,_|      \____|_|  \__,_|\___|_|\_\___|_|
                |___/
By Petitoto
'''

HELP_CMD = {'General': ['help', 'exit'],
        'Attributes': ['get', 'set', 'unset'],
        'Configurations': ['add_config', 'gen_configs', 'gen_plugs', 'gen_ring','import_configs', 'export_configs', 'compute'],
        'Cryptanalysis': ['crypt', 'ic_attack', 'ngram_attack', 'kp_attack', 'turing_attack', 'rejewski_attack', 'cribs_finder', 'ring_recovery'],
        'Misc': ['count', 'turn_rotors', '#'],
        'Topics information': ['attributes', 'rotors', 'machines']}

ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

ROTORS = {
    'I':('EKMFLGDQVZNTOWYHXUSPAIBRCJ', 'Q'),
    'II':('AJDKSIRUXBLHWTMCQGZNPYFVOE', 'E'),
    'III':('BDFHJLCPRTXVZNYEIWGAKMUSQO', 'V'),
    'IV':('ESOVPZJAYQUIRHXLNFTGKDCMWB', 'J'),
    'V':('VZBRGITYUPSDNHLXAWMJQOFECK', 'Z'),
    'VI':('JPGVOUMFYQBENHZRDKASXLICTW', 'ZM'),
    'VII':('NZJHGRCXMYSWBOUFAIVLPEKQDT', 'ZM'),
    'VIII':('FKQHTLXOCBJSPDZRAMEWNIUYGV', 'ZM'),
    'Beta':('LEYJVCNIXWPBQMDRTAKZGFUHOS', ''),
    'Gamma':('EKMFLGDQVZNTOWYHXUSPAIBRCJ', '')
}

REFLECTORS = {
    'B':'YRUHQSLDPXNGOKMIEBFZCWVJAT',
    'C':'FVPJIAOYEDRZXWGCTKUQSBNMHL',
    'B-thin':'ENKQAUYWJICOPBLMDXZVFTHRGS',
    'C-thin':'RDOBJNTKVEHMLFCWZAXGYIPSUQ',
}

MACHINES = {
    'M3':{'Reflectors': 'B C', 'Rotors':['I II III IV V']*3, 'RotorsShort':['I - V']*3, 'Duplicates':False},
    'M4':{'Reflectors': 'B-thin C-thin', 'Rotors':['Beta Gamma']+['I II III IV V VI VII VIII']*3, 'RotorsShort':['Beta Gamma']+['I - VIII']*3, 'Duplicates':False}
}

STEPPING_PROCESS = '''
        - third rotor is stepped if the second rotor is on its turnover notch
        - second rotor is stepped if it is on its turnover notch (only for machine with at least 3 rotors) or if the first rotor is on its turnover notch
        - first rotor is always stepped
        - other rotors are never stepped
'''