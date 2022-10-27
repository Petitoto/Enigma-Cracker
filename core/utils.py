import sys
import multiprocessing
import gc
import time

from .constants import ROTORS, REFLECTORS


class ProcessManager:
    class GenProcess:
        def __init__(self, gen, *opts):
            self.gen = gen
            self.opts = opts
        
        def _init_globals(self, barValue):
            global progressBarValue
            progressBarValue = barValue
        
        def _configs2gen(self, i, configs):
            for c in configs:
                progressBarValue[i] += 1
                yield c
        
        def run(self, i, configs):
            try:
                configs, newconfigs = (self._configs2gen, i, configs), []
                for conf in self.gen(*self.opts, configs):
                    newconfigs.append(conf)
                return newconfigs
            
            except KeyboardInterrupt:
                return None
    
    def __init__(self, gen, configs, nbprocess):
        if not configs: raise InvalidCommand('No configuration found')
        self.gen = gen
        self.configs = configs
        self.nbprocess = nbprocess
        self.progressbar = ProgressBar()
        self.progressbar.addBar(len(self.configs))
    
    def run(self, *opts):
        length = [len(self.configs) // self.nbprocess] * self.nbprocess
        for i in range(len(self.configs) % self.nbprocess):
            length[i] += 1
        
        j, split = 0, []
        for i in range(self.nbprocess):
            split.append((j, j+length[i]))
            j += length[i]
        
        barValue = multiprocessing.RawArray('i', [0] * self.nbprocess)
        
        genconfs = self.GenProcess(self.gen, *opts)
        p = multiprocessing.Pool(processes=self.nbprocess, initializer=genconfs._init_globals, initargs=(barValue,))
        
        try:
            map = p.starmap_async(genconfs.run, zip(range(self.nbprocess), (self.configs[i:j] for i,j in split)))
            while not all(barValue):
                time.sleep(0.5)
                self.progressbar.inc(sum(barValue) - self.progressbar.value)
            gc.collect()
            while not map.ready():
                time.sleep(0.5)
                self.progressbar.inc(sum(barValue) - self.progressbar.value)
                self.progressbar.update()
            print('\n')
        finally:
            p.terminate()
        
        newconfs = []
        for confs in map.get():
            newconfs += confs
        
        return newconfs


def prompt(message, validator=None):
    value = input(message + '\n> ')
    if validator:
        value = validator(value)
    return value


class InvalidCommand(Exception):
    pass


class Colors:
    def __init__(self):
        is_color_terminal = True
        if sys.platform.startswith('win'):
            import ctypes
            import msvcrt
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 4
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            hstdout = msvcrt.get_osfhandle(sys.stdout.fileno())
            mode = ctypes.c_ulong()
            is_color_terminal = kernel32.GetConsoleMode(hstdout, ctypes.byref(mode)) and (mode.value & ENABLE_VIRTUAL_TERMINAL_PROCESSING != 0)
            if not is_color_terminal:
                is_color_terminal = kernel32.SetConsoleMode(hstdout, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING) > 0
        
        if is_color_terminal:
            self.colors = {
                'blue':'\033[94m',
                'green':'\033[92m',
                'cyan':'\033[96m',
                'yellow':'\033[93m',
                'red':'\033[91m',
                'bold':'\033[1;97m',
                'ENDC':'\033[0m'
            }
        else:
            self.BLUE, self.GREEN, self.YELLOW, self.RED, self.ENDC = '', '', '', '', ''
    
    def __getattr__(self, attr):
        def color(string):
            if attr in self.colors:
                return self.colors[attr] + string + self.colors['ENDC']
            else:
                return string
        return color
    
    def success(self, string):
        return self.colors['green'] + '[+] ' + string + self.colors['ENDC']
    
    def info(self, string):
        return self.colors['cyan'] + '[i] ' + string + self.colors['ENDC']
    
    def fail(self, string):
        return self.colors['yellow'] + '[-] ' + string + self.colors['ENDC']
    
    def error(self, string):
        return self.colors['yellow'] + '[-] ' + string + self.colors['ENDC']


class Validators:
    class ValidationError(Exception):
        pass
    
    def __init__(self, *args):
        self.args = args
    
    
    def YN(self, value):
        message = 'Enter Y or N'
        
        if value == 'Y':
            return True
        elif value == 'N':
            return False
        else:
            raise self.ValidationError(message)
    
    
    def PosInt(self, value):
        message = 'Enter a strictly positive integer'
        
        if not value.isdigit():
            raise self.ValidationError(message)
        return int(value)


    def Rotors(self, value):
        message = 'Enter rotors sperarated by a space\nExample: \'I II III\''
        
        if not value:
            raise self.ValidationError(message)
        
        for r in value.split():
            if not r in ROTORS.keys():
                raise self.ValidationError(message)
        
        return value
    
    
    def Reflectors(self, value):
        message = 'Enter reflectors separated by a space\n Example: \'B C\''
        
        if not value:
            raise self.ValidationError(message)
        
        for r in value.split():
            if not r in REFLECTORS.keys():
                raise self.ValidationError(message)
        
        reflectors = list(set(value.split()))
        return ' '.join(reflectors)
    
    
    def Reflector(self, value):
        message = 'Enter a reflector\nExample: \'B\''
        
        if not value in REFLECTORS.keys():
            raise self.ValidationError(message)
        return value
    
    
    def Plugboard(self, value):
        message = 'Incorrect plugboard settings\nExample: \'AD EK RF\' (be careful to not duplicate connections)'
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        
        if not value:
            return value
        
        for v in value.split(' '):
            if not v.isalpha() or len(v) != 2:
                raise self.ValidationError(message)
        
        for char in chars:
            count = value.upper().count(char)
            if count > 1:
                raise self.ValidationError(message)
        
        return value.upper()
    
    
    def Ring(self, value):
        message = 'Incorrect ring settings\nExample for 3 rotors: \'5 1 26\' (integers from 1 to 26)'
        if not isinstance(self.args[0], int):
            return ''
        
        if len(value.split()) != self.args[0]:
            raise self.ValidationError(message)
        
        for v in value.split():
            if not v.isdigit() or int(v) > 26 or int(v) < 1:
                raise self.ValidationError(message)
        
        return value
    
    
    def Positions(self, value):
        message = 'Incorrect rotors positions\nExample for 3 rotors: \'AGD\''
        if not isinstance(self.args[0], int):
            return ''
        
        if len(value) != self.args[0] or not value.isalpha():
            raise self.ValidationError(message)
        return value.upper()


class ProgressBar:
    barlength = 50
    
    def __init__(self):
        self.displaylength, self.maxval, self.value, self.t0 = 0, 0, 0, 0
    
    def finish(self):
        time.sleep(0.6)
        print('\n')
        self.value = 0
    
    def addBar(self, maxval):
        self.maxval += maxval
    
    def inc(self, n=1):
        if n > 0:
            if self.value == 0:
                self.t0 = time.time()
            self.value += n
    
    def update(self):
        if not self.maxval: raise InvalidCommand('No Bar were added to the ProgressBar')
        
        inc = self.maxval / 100
        percent = self.value / inc
        if percent > 0:
            eta = round((time.time() - self.t0) * (100 / percent - 1))
            if eta // 3600 > 0:
                eta_s = '%s h' % (eta // 3600)
            elif eta // 60 > 0:
                eta_s = '%s min' % (eta // 60)
            else:
                eta_s = '%s s' % (eta)
        else:
            eta_s = '?'
        
        sys.stdout.write('\r')
        bar = '[{:{}}] {:10.2f}% (ETA: {})'.format('#' * int(percent / 100 * self.barlength), self.barlength, percent, eta_s)
        barlen = len(bar)
        if barlen < self.displaylength:
            bar += ' ' * (self.displaylength - barlen)
        self.displaylength = barlen
        sys.stdout.write(bar)
        sys.stdout.flush()