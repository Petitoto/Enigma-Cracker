#/usr/bin/env python3

import cmd
import itertools
from threading import Thread
import gc
from copy import deepcopy
import json
import time

from core.constants import BANNER, HELP_CMD, ALPHABET, ROTORS, REFLECTORS, MACHINES, STEPPING_PROCESS
from core.utils import ProcessManager, Colors, prompt, InvalidCommand, Validators, ProgressBar
import modules


colored = Colors()

class MainMenu(cmd.Cmd):
    intro = 'Enigma cryptanalysis tool\nUse \'?\' or \'help\' for help, \'Ctrl+C\' to abort any task, \'exit\' to leave\n'
    prompt = colored.red('Enigma-Cracker > ')
    
    attributes = ['text','configs', 'process']
    defaultvalues = {'text':'', 'configs':(lambda: '',), 'process':'1'}
    
    
    def __init__(self):
        self.progressBar = ProgressBar()
        self.init(self.defaultvalues)
        super().__init__()
    
    
    # Internal methods
    def init(self, values):
        try:
            if 'text' in values:
                self.text = values['text']
                self.ftext = self.filter_text(values['text'])
            
            if 'configs' in values:
                self.configs = values['configs']
            
            if 'process' in values:
                if not int(values['process']) >= 1:
                    raise InvalidCommand
                self.process = int(values['process'])
        
        except:
            raise InvalidCommand('Invalid value')
    
    
    def filter_text(self, text):
        filtered = ''
        for letter in text:
            if letter.upper() in ALPHABET:
                filtered += letter.upper()
        return filtered
    
    
    def unfilter_text(self, text):
        for i, letter in enumerate(self.text):
                if letter.islower():
                    text = text[:i] + text[i].lower() + text[i+1:]
                elif letter.upper() not in ALPHABET:
                    text = text[:i] + letter + text[i:]
        return text
    
    
    def _list2gen(self, configs, progressBar):
        for c in configs:
            progressBar.inc()
            yield deepcopy(c)
    
    
    def add_configs(self, configs, n):
        if isinstance(self.configs, list) and isinstance(configs, list):
            self.configs.extend(configs)
        
        else:
            if isinstance(self.configs, list):
                self.progressBar = ProgressBar()
                self.progressBar.addBar(len(self.configs))
                self.configs = (self._list2gen, self.configs, self.progressBar)
                configs = (configs[0], configs[1], self.progressBar)
            
            if isinstance(configs, list):
                configs = (self._list2gen, configs, self.progressBar)
            
            def chain(configs1, configs2):
                gen1, *opts1 = configs1
                gen2, *opts2 = configs2
                return itertools.chain(gen1(*opts1), gen2(*opts2))
            
            self.configs = (chain, self.configs, configs)
        
        self.progressBar.addBar(n)
    
    
    def edit_configs(self, gen, *opts, force_multiprocess=False):
        if self.process == 1 and not force_multiprocess:
            if isinstance(self.configs, list):
                self.progressBar = ProgressBar()
                self.progressBar.addBar(len(self.configs))
                self.configs = (self._list2gen, self.configs, self.progressBar)
            
            self.configs = (gen, *opts, self.configs)
        
        else:
            if not isinstance(self.configs, list):
                self.do_compute('')
            
            if self.process > 1:
                print(colored.info('Launching %s processes...' % self.process))
            
            self.configs = ProcessManager(gen, self.configs, self.process).run(*opts)
            gc.collect()
            
            self.progressBar = ProgressBar()
            self.progressBar.addBar(len(self.configs))
    
    
    def progressBarThread(self):
        def displayBar():
            self.progressBar.update()
            while self.progressBar.value == 0:
                time.sleep(0.5)
            while self.progressBar.value > 0:
                self.progressBar.update()
                time.sleep(0.5)
        
        self.progressBar.value = 0
        t = Thread(target=displayBar)
        t.start()
    
    
    # Attributes
    def do_get(self, attr):
        '''
        Get attribute value
        =>  get <attribute>
        '''
        if not attr in self.attributes: raise InvalidCommand('Unknown attribute: %s' % (attr))
        
        val = getattr(self, attr)
        if not val: raise InvalidCommand('Attribute \'%s\' is empty' % (attr))
        
        if attr == 'text':
            length = ' (%s chars / %s letters)' % (len(val), len(self.ftext))
        
        elif attr == 'configs' and not isinstance(self.configs, list):
            if not self.progressBar.maxval: raise InvalidCommand('Attribute \'configs\' is empty')
            print(colored.info('Configurations are stored using generators : counting them...'))
            
            gen, *opts = self.configs
            configs = gen(*opts)
            
            self.progressBarThread()
            val = list(itertools.islice(configs, 50))
            length = sum(1 for _ in configs) + len(val)
            
            self.progressBar.finish()
            
            if length > len(val):
                val.append('...')
            val = '\n'.join(map(str, val))
            length = ' (%s)' % length
        
        elif attr == 'configs':
            length = ' (%s)' % len(val)
            val = '\n'.join(map(str, self.configs[:50]))
            if len(self.configs) > 50:
                val += '\n...'
        
        else:
            length = ''
        
        if isinstance(attr, list):
            attr = '\n'.join(attr)
        
        print(colored.success('Value of \'%s\'%s:\n' % (attr, length)))
        print(str(val) + '\n')
    
    
    def do_set(self, line):
        '''
        Set attribute value
        => set <attribute> <value>
        '''
        attr, val, _ = self.parseline(line)
        if not attr and val: raise InvalidCommand('Missing attribute or value')
        if not attr in self.attributes: raise InvalidCommand('Unknown attribute: %s' % (attr))
        if not attr != 'configs': raise InvalidCommand('Can\'t directly set \'configs\' attribute. Use add_config, import_configs or gen_configs')
        
        if attr == 'process':
            val = int(val)
        
        value = {attr: val}
        if self.init(value):
            print(colored.success('Attribute \'%s\' set\n' % (attr)))
    
    
    def do_unset(self, attr):
        '''
        Reset attribute value
        => unset <attribute>
        '''
        if not attr in self.attributes: raise InvalidCommand('Unknown attribute: %s' % (attr))
        
        if attr == 'configs':
            self.progressBar = ProgressBar()
        
        value = {attr: self.defaultvalues[attr]}
        
        self.init(value)
        print(colored.success('Attribute \'%s\' unset\n' % (attr)))
    
    
    # Configurations 
    def do_add_config(self, line):
        '''
        Add a configuration
        => add_config <config> | add_config -> follow instructions
        '''
        if line:
            conf = json.loads(line.replace('\'', '"'))
        
        else:
            conf = {}
            conf['Reflector'] = prompt('Reflector:', validator=Validators().Reflector)
            conf['Rotors'] = prompt('Rotors:', validator=Validators().Rotors)
            conf['Ring'] = prompt('Ring settings:', validator=Validators(len(conf['Rotors'].split(' '))).Ring)
            conf['Plugboard'] = prompt('Plugboard settings:', validator=Validators().Plugboard)
            conf['Positions'] = prompt('Position of each rotor:', validator=Validators(len(conf['Rotors'].split(' '))).Positions)
        
        self.add_configs([conf], 1)
        print(colored.success('%s\nadded to attribute \'configs\'\n' % (conf)))
    
    
    def do_gen_configs(self, line):
        '''
        Generate all possible configurations according to the specified model (without plugboard & ring settings)
        => gen_configs <machine> | gen_configs -> follow instructions
        '''
        model = {}
        if line:
            if not line in MACHINES: raise InvalidCommand('Machine %s not found' % line)
            model['Reflectors'] = MACHINES[line]['Reflectors']
            model['RotorsCount'] = len(MACHINES[line]['Rotors'])
            model['Rotors'] = MACHINES[line]['Rotors']
            model['Duplicates'] = MACHINES[line]['Duplicates']
        
        else:
            model['Reflectors'] = prompt('Available reflectors:', validator=Validators().Reflectors)
            model['RotorsCount'] = prompt('Number of rotors:', validator=Validators().PosInt)
            model['Rotors'] = []
            for i in range(model['RotorsCount']):
                model['Rotors'].append(prompt('Available rotors for position n°%s:' % (i+1), validator=Validators().Rotors))
            model['Duplicates'] = prompt('Allow duplicate rotors? (Y/N)', validator=Validators().YN)
        
        n = modules.generate.gen_configs_count(model)
        self.add_configs((modules.generate.gen_configs, model, self.progressBar), n)
        
        print(colored.success('Configurations added\n'))
    
    
    def do_gen_plugs(self, line):
        '''
        Add a new plug to the plugboard for each configuration
        => gen_plugs
        '''
        self.edit_configs(modules.generate.gen_plugs)  
        print(colored.success('Plugboard settings added\n'))
    
    
    def do_gen_ring(self, line):
        '''
        Generate ring settings for each configuration, and change the rotor positions according to the new ring settings
        Use '-ringonly' to edit only ring settings
        => gen_ring (-ringonly)
        '''
        self.edit_configs(modules.generate.gen_ring, line == '-ringonly')
        print(colored.success('Ring settings added\n'))
    
    
    def do_import_configs(self, file):
        '''
        Add configurations from a file
        => import_configs <file>
        '''
        if not file: raise InvalidCommand('Missing configuration file')
        
        def gen(file):
            try:
                with open(file) as f:
                    for conf in f:
                        yield json.loads(conf.strip('\n'))
            except OSError:
                raise InvalidCommand('Could not open file: %s' % (file))
        
        self.add_configs((gen, file), sum(1 for _ in open(file)))
        
        print(colored.success('Configurations added\n'))
    
    
    def do_export_configs(self, file):
        '''
        Append current configurations to a file
        => export_configs <file>
        '''
        if not file: raise InvalidCommand('Missing file')
        if not self.configs: raise InvalidCommand('No configuration to export')
        
        try:
            fconfig = open(file, 'a')
            
            print(colored.success('Exporting configurations to %s...' % file))
            
            configs = self.configs
            if not isinstance(self.configs, list):
                gen, *opts = self.configs
                configs = gen(*opts)
            for conf in configs:
                conf = json.dumps(conf) + '\n'
                fconfig.write(conf)
            
            fconfig.close()
        
        except OSError:
            raise InvalidCommand('Could not open file: %s' % (file))
        
        print(colored.success('Configurations exported\n'))
    
    
    def do_compute(self, line):
        '''
        Execute all generators and store configurations into a list
        => compute
        '''
        if not not isinstance(self.configs, list): raise InvalidCommand('Configurations are already stored as a list')
        if not self.progressBar.maxval: raise InvalidCommand('No configuration found')
        
        print(colored.success('Computing configurations...'))
        
        self.progressBarThread()
        gen, *opts = self.configs
        self.configs = list(gen(*opts))
        self.progressBar.finish()
        self.progressBar = ProgressBar()
        self.progressBar.addBar(len(self.configs))
    
    
    # Cryptanalysis
    def do_crypt(self, line):
        '''
        Encrypt or decrypt text using each configuration
        Print specified scores for each processed text
        => crypt (-ic) (-ngram <file>) (-kp <plaintext>)
        '''
        if not self.ftext: raise InvalidCommand('Missing text attribute')
        if not self.progressBar.maxval: raise InvalidCommand('No configurations found')
        
        possible_args = ['-ic', '-ngram', '-kp']
        ic, ngram, kp = False, (), ''
        
        args = line.split()
        i = 0
        while i < len(args):
            if args[i] == '-ic':
                ic = True
                i += 1
                
            elif args[i] == '-ngram':
                file = []
                j = i+1
                while j < len(args) and not args[j] in possible_args:
                    file.append(args[j])
                    j += 1
                file = ' '.join(file)
                
                try:
                    ngrams = {}
                    nsize = len(open(file).readline().split()[0])
                    with open(file) as f:
                        for line in f:
                            gram, p = line.strip('\n').split()
                            if not len(gram) == nsize: raise InvalidCommand('ngram file must contain ngrams of same size')
                            ngrams[gram] = int(p)
                except OSError:
                    raise InvalidCommand('Invalid ngram file: %s' % (file))
                
                ngram = (nsize, ngrams)
                i = j
                
            elif args[i] == '-kp':
                kp = []
                j = i+1
                while j < len(args) and not args[j] in possible_args:
                    kp.append(args[j])
                    j += 1
                kp = ' '.join(kp)
                
                if not len(kp) == len(self.text): raise InvalidCommand('Known plaintext must be the corresponding plaintext of the \'text\' attribute')
                i = j
            
            else:
                raise InvalidCommand('Invalid argument: %s' % args[i])
        
        print(colored.success('Processing text using each configuration...'))
        
        configs = self.configs
        if not isinstance(self.configs, list):
            gen, *opts = self.configs
            configs = gen(*opts)
        
        for i, conf in enumerate(configs):
            print(colored.bold('%s - %s' % (i+1, conf)))
            
            rotors, reflector, ring, plugboard, positions = conf['Rotors'], conf['Reflector'], conf['Ring'], conf['Plugboard'], conf['Positions']
            fprocessed = modules.misc.crypt(reflector, rotors, ring, plugboard, positions, self.ftext)
            processed = self.unfilter_text(fprocessed)
            
            scores = []
            if ic:
                scores.append('IC: %.5f' % modules.ic.calcic(fprocessed))
            if ngram:
                nsize, ngrams = ngram
                scores.append('NGRAM: %.4f' % modules.ngram.calc_ngramscore(nsize, ngrams, fprocessed))
            if kp:
                scores.append('KP: %s' % modules.known_plaintext.calc_kpscore(kp, fprocessed))
            
            if scores:
                print(colored.bold(', '.join(scores)))
            
            print(processed + '\n')
    
    
    def do_ic_attack(self, line):
        '''
        Keep N configurations with the highest indexes of coincidence (and sort them by IC)
        Or keep configurations with index of coincidence superior to a specified value
        => ic_attack <N> | ic_attack -ic <ic_min>
        '''
        if not self.text: raise InvalidCommand('Missing text attribute')
        
        if line.startswith('-ic'):
            try:
                ic_min = float(line[3:])
            except ValueError:
                raise InvalidCommand('Invalid minimum index of coincidence')
            print(colored.success('Index of coincidence attack: IC >= %s\n' % ic_min))
            self.edit_configs(modules.ic.ic_attack, ic_min, self.ftext)
        else:
            try:
                n = int(line)
            except ValueError:
                raise InvalidCommand('Invalid number of configurations')
            print(colored.success('Index of coincidence attack: %s highest IC\n' % n))
            self.edit_configs(modules.ic.ic_n_attack, n, self.ftext)
            
            if self.process > 1:
                print(colored.info('Merging the results of the %s processes...' % self.process))
                process = self.process
                self.process = 1
                self.edit_configs(modules.ic.ic_n_attack, n, self.ftext, force_multiprocess=True)
                self.process = process
    
    
    def do_ngram_attack(self, line):
        '''
        Keep N configurations with the highest ngram scores (and sort them by ngram)
        A ngram file is required (format : 'NGRAM count(NGRAM)' per line)
        => ngram_attack <N> <file>
        '''
        if not line and len(line.split()) >= 2: raise InvalidCommand('Missing arguments')
        if not self.text: raise InvalidCommand('Missing text attribute')
        
        n, file, _ = self.parseline(line)
        
        try:
            n = int(n)
        except ValueError:
            raise InvalidCommand('Invalid number of configurations')
        
        try:
            ngrams = {}
            nsize = len(open(file).readline().split()[0])
            with open(file) as f:
                for line in f:
                    gram, p = line.strip('\n').split()
                    if not len(gram) == nsize: raise InvalidCommand('ngram file must contain ngrams of same size')
                    ngrams[gram] = int(p)
        except OSError:
            raise InvalidCommand('Invalid ngram file: %s' % (file))
        
        
        print(colored.success('%s-gram attack: %s highest scores, based on %s\n') % (nsize, n, file))
        self.edit_configs(modules.ngram.ngram_n_attack, n, nsize, ngrams, self.ftext)
        
        if self.process > 1:
            print(colored.info('Merging the results of the %s processes...' % self.process))
            process = self.process
            self.process = 1
            self.edit_configs(modules.ngram.ngram_n_attack, n, nsize, ngrams, self.ftext, force_multiprocess=True)
            self.process = process
    
    
    def do_kp_attack(self, line):
        '''
        Keep N configurations which produce the closest text from a known plaintext
        Or keep configurations which produce the exact known plaintext
        => kp_attack <N> <plaintext> | kp_attack -exact <plaintext>
        '''
        if not len(line.split()) > 1: raise InvalidCommand('Missing arguments')
        
        n = line.split()[0]
        plaintext = line[len(n)+1:]
        
        if not len(plaintext) == len(self.text): raise InvalidCommand('Known plaintext must be the corresponding plaintext of the \'text\' attribute')
                
        if n == '-exact':
            print(colored.success('Exact known plaintext attack\n'))
            self.edit_configs(modules.known_plaintext.kp_attack, self.filter_text(plaintext), self.ftext)
        
        else:
            try:
                n = int(n)
            except ValueError:
                raise InvalidCommand('Invalid number of configurations')
            print(colored.success('Known plaintext attack: %s highest scores\n' % n))
            self.edit_configs(modules.known_plaintext.kp_score_attack, n, self.filter_text(plaintext), self.ftext)
            
            if self.process > 1:
                print(colored.info('Merging the results of the %s processes...' % self.process))
                process = self.process
                self.process = 1
                self.edit_configs(modules.known_plaintext.kp_score_attack, n, self.filter_text(plaintext), self.ftext, force_multiprocess=True)
                self.process = process
    
    
    def do_turing_attack(self, line):
        '''
        Keep configurations compatible with a crib, using the Turing's bombe
        => turing_attack <crib>
        '''
        if not line: raise InvalidCommand('Missing crib')
        if not self.text: raise InvalidCommand('Missing text attribute')
        
        crib = self.filter_text(line)
        if not len(self.ftext) == len(crib): raise InvalidCommand('Crib length does not match the text attribute')
        
        print(colored.success('Cribs based attack (Turing\'s bombe)'))
        
        menu, node, loops = modules.turing.gen_menu(crib, self.ftext)
        print(colored.success('Running with %d loop%s. Hypothesis: %s is fixed by the plugboard\n' % (loops, 's' if loops > 1 else '', node)))
        self.edit_configs(modules.turing.crib_attack, menu, node)
    
    
    def do_rejewski_attack(self, line):
        '''
        Rejewski's characteristics attack implementation
        This attack requires several message keys encrypted twice with the daily key at the begining of the message
        => rejewski_attack <double encrypted key 1> <double encrypted key 2> ...
        '''
        n2 = len(line.split()[0])
        if not not n2 % 2: raise InvalidCommand('Keys should be encrypted twice')
        if not all([len(k) == n2 for k in line.split()]): raise InvalidCommand('Invalid keys')
        n = n2 // 2
        
        print(colored.success('Rejewski attack: %s keys\n' % len(line.split())))
        chains = modules.rejewski.rejewski_chains(line, n)
        self.edit_configs(modules.rejewski.rejewski_attack, chains)
    
    
    def do_cribs_finder(self, file):
        '''
        Find possible cribs from a wordlist
        Wordlist is a file with one crib per line
        => cribs_finder <file>
        '''
        if not file: raise InvalidCommand('Missing wordlist')
        if not self.text: raise InvalidCommand('Missing text attribute')
        
        try:
            words = [w.strip('\n') for w in open(file).readlines()]
        except OSError:
            raise InvalidCommand('Could not open file: %s' % (file))
        
        print(colored.success('Cribs finder: %s' % (file)))
        
        cribs = modules.cribs.find_cribs(words, self.text, self.filter_text)
        
        if not cribs:
            print(colored.fail('No crib found'))
        else:
            print(colored.success('Found possible cribs:'))
            for c in cribs.keys():
                encrypted = [self.text[i:i+len(c)] for i in cribs[c]]
                print('%s:' % c)
                print('-> %s\n' %  ' ; '.join(encrypted))
    
    
    def do_ring_recovery(self, line):
        '''
        Recover ring settings. May be launched several times
        => ring_recovery -> follow instructions
        '''
        if not self.ftext: raise InvalidCommand('Missing text attribute')
        print(colored.success('Ring settings recovery'))
        
        configs = self.configs
        if not isinstance(self.configs, list):
            gen, *opts = self.configs
            configs = gen(*opts)
        
        blocks = []
        for i, conf in enumerate(configs):
            print(colored.bold('%s: %s' % (i+1, conf)))
            
            rotors, reflector, ring, plugboard, positions = conf['Rotors'], conf['Reflector'], conf['Ring'], conf['Plugboard'], conf['Positions']
            fprocessed = modules.misc.crypt(reflector, rotors, ring, plugboard, positions, self.ftext)
            processed = self.unfilter_text(fprocessed)
            
            print(processed + '\n')
            
            block = self.filter_text(prompt('Enter a full well-decrypted block'))
            if not block in fprocessed: raise InvalidCommand('Block not found')
            blocks.append((fprocessed.index(block), len(block)))
        
        self.edit_configs(modules.ring.recover_ring, blocks)
        
        print(colored.success('New ring settings applied. You may launch the command again\n'))
    
    
    # Misc
    def do_count(self, line):
        '''
        Count the letters of a text (only letters Enigma can process, ie a-zA-Z)
        => count <text>
        '''
        n = modules.misc.count(line)
        print(colored.success('%s letters\n' % n))
    
    
    def do_turn_rotors(self, line):
        '''
        Turn configurations' rotors
        Rolling back rotors may add new configurations or remove some
        => turn_rotors <new_position>
            <new_position> is a positive integer to turn on rotors or a negative integer to roll back rotors
        '''
        try:
            n = int(line)
            if n == 0:
                raise InvalidCommand

            self.edit_configs(modules.misc.turn_rotors, n)
            print(colored.success('Rotors %s by %s keys\n') % ('rolled back' if n < 0 else 'turned', abs(n)))
            
        except ValueError:
            raise InvalidCommand('Invalid new position')
      
    
    # Topics information
    def help_attributes(self):
        attributes = '''
        Attributes:
            text: text to encrypt, decrypt, or attack
            configs: Enigma configurations to encrypt, decrypt, or attack the text
            process: number of processes to launch attacks (default: 1)
        
        NB: multi processing prevents storing configurations as generators
        '''
        
        print(attributes)
    
    
    def help_rotors(self):
        info_wiring = '''
        +-------------------+----------------------------+
        |       Rotor       | ABCDEFGHIJKLMNOPQRSTUVWXYZ |
        +-------------------+----------------------------+%s
        +-------------------+----------------------------+
        '''
        info_notches = '''
        +---------------+----------------------+
        |     Rotor     | Turnover Position(s) |
        +---------------+----------------------+%s
        +---------------+----------------------+
        '''
        info_stepping = '''
        Stepping mechanism (rotors ordered right to left):%s''' % STEPPING_PROCESS
        
        wiring = ''
        notches = ''
        for rotor in ROTORS:
            wiring += '\n{}| {:{}} | {} |'.format(' '*8, rotor, 17, ROTORS[rotor][0])
            
            notch = ROTORS[rotor][1]
            if notch:
                notch_l = []
                for n in notch:
                    i = ALPHABET.index(n)
                    notch_l.append('%s -> %s' % (ALPHABET[i], ALPHABET[(i+1) % len(ALPHABET)]))
                notches += '\n{}| {:{}} | {:{}} |'.format(' '*8, rotor, 13, ' & '.join(notch_l), 20)
        
        for reflector in REFLECTORS:
            wiring += '\n{}| Reflector {:{}} | {} |'.format(' '*8, reflector, 7, REFLECTORS[reflector])
        
        print(info_wiring % wiring)
        print(info_notches % notches)
        print(info_stepping)
    
    
    def help_machines(self):
        info_machines = '''
        +---------------+----------------+------------------+------------+
        |    Machine    |   Reflectors   |      Rotors      | Duplicates |
        +---------------+----------------+------------------+------------+%s
        +---------------+----------------+------------------+------------+
        '''
        
        machines = ''
        for machine in MACHINES:
            machines += '\n{}| {:{}} | {:{}} | * {:{}} | {:{}} |'.format(' '*8, machine, 13, MACHINES[machine]['Reflectors'], 14, MACHINES[machine]['RotorsShort'][0], 14, str(MACHINES[machine]['Duplicates']), 10)
            for rotor in MACHINES[machine]['RotorsShort'][1:]:
                machines += '\n{}| {:{}} | {:{}} |   {:{}} | {:{}} |'.format(' '*8, '', 13, '', 14, rotor, 14, '', 10)
        
        print(info_machines % machines)
    
    
    # General & Cmd utils
    def do_help(self, arg):
        '''
        Print allowed commands or help about a command
        => help (<command>) | ? (<command>)
        '''
        
        comment_help = '''
        Leave comment, do nothing else
        => # <comment>
        '''
        
        if arg:
            if arg == '#':
                print(comment_help)
            elif arg == '?':
                super().do_help('help')
            else:
                if not any([arg in HELP_CMD[topic] for topic in HELP_CMD.keys()]): raise InvalidCommand('Unknown command: %s' % arg)
                super().do_help(arg)
        
        else:
            print('Use help <command> to get more help\n')
            for topic in HELP_CMD.keys():
                self.print_topics(topic, HELP_CMD[topic], 15, 80)
    
    
    def do_exit(self, line):
        '''
        Close Enigma-Cracker
        => exit
        '''
        print(colored.blue('Bye'))
        exit()
    
    
    def onecmd(self, line):
        try:
            super().onecmd(line)
        
        except KeyboardInterrupt:
            self.progressBar.finish()
            print(colored.fail('Abort'))
            if self.configs:
                print(colored.success('Configurations restored\n'))
            else:
                print(colored.fail('Failed to restore configurations\n'))
            gc.collect()
        
        except InvalidCommand as e:
            print(colored.fail('%s\n' % e))
            return False
        
        except Exception as e:
            print(colored.fail('%s\n' % e))
            return False
    
    
    def default(self, line):
        cmd, _, line = self.parseline(line)
        if cmd == 'EOF':
            raise KeyboardInterrupt
        if not line.startswith('#'): raise InvalidCommand('Unknown command: %s' % (cmd))
    
    
    def completedefault(self, text, line, begidx, endidx):
        cmd, _, _ = self.parseline(line)
        
        if cmd in ['set', 'get', 'unset']:
            if not text:
                completions = self.attributes[:]
            else:
                completions = [f for f in self.attributes if f.startswith(text)]
            return completions
        
        else:
            return []
    
    
    def emptyline(self):
        pass




if __name__ == '__main__':
    print(colored.blue(BANNER))
    try:
        MainMenu().cmdloop()
    except KeyboardInterrupt:
        print(colored.blue('\nBye'))