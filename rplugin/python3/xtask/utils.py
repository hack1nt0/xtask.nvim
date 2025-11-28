import os, json, glob, shutil, time
from typing import Tuple, List

conffname = os.path.join(os.path.dirname(__file__), 'conf.json')
conf: dict = json.load(open(conffname))
def save_conf(): open(conffname, 'w').write(json.dumps(conf, indent=4))

task_dir = os.path.join(os.path.dirname(__file__), 'tasks'); os.makedirs(task_dir, exist_ok=True)
template_dir = os.path.join(os.path.dirname(__file__), 'templates'); os.makedirs(template_dir, exist_ok=True)

INFO = 'xtask.json'

# first look for 'xtask.json', otherwise for any .json file which 'name' key exists;
def get_xinfo(path: str) -> dict:
    fname = os.path.join(path, INFO)
    xinfo = {
        "name": os.path.abspath(path),
        "desc": "",
        "url": "",

        "test_way": 1,
        "tcs": "*.tc",
        "sol": "sol.cpp",
        "gen": "gen.py",
        "interactive": 0,
        "cmd": "",

        "cpu": 1000,
        "mem": 256,
        "result": 1,

        "ctime": '0', #1970-1-1
    }
    if os.path.exists(fname):
        xinfo.update(json.loads(open(fname).read()))
    return xinfo

def get_all_tasks() -> List[Tuple[str,dict]]:
    cwd = os.getcwd()
    path = task_dir
    os.chdir(task_dir)
    # return [(os.path.dirname(info), json.loads(open(info).read())) for info in glob.glob(os.path.join(TASKS, '**', INFO))]
    res = [(os.path.join(path, subdir), get_xinfo(subdir)) for subdir in os.listdir(path) if os.path.isdir(subdir)]
    os.chdir(cwd)
    return res

def get_all_files(path: str) -> List[str]:
    res = []
    for root, dirnames, filenames in os.walk(path):
        if root in ['bin', 'build'] or root.endswith('.dSYM'):
            dirnames.clear()
        else:
            for filename in filenames:
                res.append(os.path.join(root, filename))
    return res

def taskname_to_dirname(name: str) -> str:
    return name.replace('/', '\\/').replace(' ', '')


def delete_task(path: str):
    shutil.rmtree(path)


def update_xinfo(path:str):
    xinfo = get_xinfo(path)
    cmds = {}
    with open(os.path.join(path, 'Makefile'), 'w') as w:
        buf = ''
        alldeps = ''
        for filerole in ['sol', 'gen']:
            filename = xinfo[filerole]
            filepref, filesufx = os.path.splitext(filename)
            fileexe = f'{filepref}.exe'
            match filesufx:
                case '.cpp':
                    buf += f'{fileexe}: {filename}\n\tc++ -std=c++2b -I../include -Wl,-stack_size -Wl,0x10000000 -g -Wall -Wfatal-errors -DDEBUG  -fsanitize=address -fsanitize=undefined -o {fileexe} {filename}\n\n'
                    # buf += f'{fileexe}: {filename}\n\tpwd\n\tg++-15 -std=c++23 -Wl,-stack_size -Wl,0x10000000 -g -Wall -Wfatal-errors -DDEBUG -o {fileexe} {filename}\n\n'
                    alldeps += f' {fileexe}'
                    cmds[filerole] = f'./{fileexe}'
                case '.py':
                    cmds[filerole] = f'python3 {filename}'
        buf += f"all: {alldeps}\n\n"
        buf += f'clean: \n\trm -rf bin\n\n'
        w.write(buf)
    # generate xtask.json
    xinfo['cmds'] = cmds
    with open(os.path.join(path, INFO), 'w') as w: json.dump(xinfo, w, indent=4)
    # generate .vscode/launch.json
    solver = xinfo['sol']
    prefix, suffix = os.path.splitext(solver)
    c = {}
    match suffix:
        case '.cpp':
            c = {
                "name": "Cpp",
                "type": "lldb",
                "request": "launch",
                "program": f"{prefix}.exe",
                "cwd": "${workspaceFolder}",
                "stdio": ["debug.in", None, None],
            }
        case '.py':
            c = {
                "name": "Python",
                "type": "debugpy",
                "request": "launch",
                "program": solver,
                "cwd": "${workspaceFolder}",
            }
    launchjson = {
        "version": "0.2.0",
        "configurations": [c],
    }
    fpath = os.path.join(path, '.vscode')
    os.makedirs(fpath, exist_ok=True)
    fname = os.path.join(fpath, 'launch.json')
    with open(fname, 'w') as w: json.dump(launchjson, w, indent=4)

import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor, Future
import json
import os, sys
import shutil, glob, tempfile, time
from typing import List, Type, Dict, Any, Tuple
from datetime import datetime

log = logging.getLogger(__name__)

PORT = 12345

resultprpr = {
    1: '❔',
    2: '✅',
    4: '❌',
    8: '⭐',
}

import itertools
import textwrap


# def shorten(s: str, W = 30): return s[:W] if W <= 2 else s[:W-2]+'..'

def shorten(s:str, w:int):
    if len(s) <= w: return s
    nkeep = w - 1
    return f'…{s[len(s)-nkeep:]}'

def clamp(v, lo, hi): return min(max(v, lo), hi)

def compare(actual: str, answer: str) -> Tuple[int, list]:
    tot = 0
    res = []
    actuals = actual.split()
    answers = answer.split()
    for i, (tac, tan) in enumerate(itertools.zip_longest(actuals, answers), start=1):
        if not tac:
            tac = ''
        if not tan:
            tan = ''
        eq = True
        try:
            eq = abs(float(tan) - float(tac)) < 1e-6
        except ValueError:
            eq = tac == tan
        tot += not eq
        res.append((eq, tac, tan))
    return tot, res

class TerminalLogger:

    def format_wrong(self, s):
        return f"\033[1;31;44m{s}\033[0m"        

    def format_right(self, s):
        return f"\033[1;32m{s}\033[0m"
    
    def format_unknown(self, s):
        return f"\033[1;33m{s}\033[0m"


    def fmt_row(self, rowid, eq, tac, tan):
        rowid = str(rowid)
        eqstr = ' ' if eq else '*'
        # s = f'{tan}{resultprpr[2]}' if eq else f'{tac} ≠ {tan}'
        s = self.format_right(tan) if eq else f'{self.format_wrong(tac)} {self.format_right(tan)}'
        if not tan: s = self.format_unknown(tac)
        return f'{str(rowid).center(3)}│{s}'

    def tail(self):
        pass
    
    def append(self, *Str):
        for e in Str: print(e, file=sys.stderr, end='' if e.endswith('\n') else '\n')

    def append_seperator(self, Str: str):
        print(Str.center(30, '-'), file=sys.stderr)
    
    def clear(self): #TODO
        pass

    def print_tktable(self, rows: List[Tuple[bool, str, str]]):
        for i, e in enumerate(rows, start=1):
            print(self.fmt_row(i, *e), file=sys.stderr)

    def set_titles(self, T: str='', B: str='Ctrl+Alt+F'): 
        pass

    def stdin(self, msg):
        pass
    def stdout(self, msg):
        pass
    def stderr(self, msg):
        pass

    def info(self, msg):
        print(self.format_right(msg), file=sys.stderr)
        
    def error(self, msg):
        print(self.format_wrong(msg), file=sys.stderr)

    def warning(self, msg): #show stderr
        print(self.format_unknown(msg), file=sys.stderr)

    
import threading, typing, functools

def do_nothing(*args): pass


import threading, subprocess
def run_xtask(xinfo: dict, logger: TerminalLogger, terminated=threading.Event()):
    logger.clear()
    # proc = subprocess.Popen(
    #     'make all',
    #     shell=True,
    #     text=True,
    #     stderr=subprocess.PIPE,
    # )
    # for line in proc.stderr:
    #     logger.append(line.rstrip())
    # proc.wait()
    # if proc.returncode:
    #     return
    tw = xinfo['test_way']
    totalmis = 0
    if tw in [1, 2]:
        def gentcfile():
            if tw == 1:
                for x in sorted(glob.glob(xinfo['tcs'])): yield x
            else:
                for i in range(100):
                    IN = f'gen{i}.tc'
                    with open(IN, 'w+') as w:
                        pgen = subprocess.Popen(
                            xinfo['cmds']['gen'],
                            shell=True,
                            text=True,
                            stdout=w,
                            stderr=subprocess.PIPE,
                        )
                        for line in pgen.stderr:
                            logger.append(line.rstrip())
                        gcode = pgen.wait()
                        if gcode: 
                            print(f'Runtime Error of generator finished with code {gcode} !')
                            return ''
                    yield IN
            
        for tcfile in gentcfile():
            if not tcfile: break
            if terminated.is_set(): break
            logger.append_seperator(f'{tcfile}')
            logger.append(*open(tcfile).readlines())
            with (
                open(tcfile) as inputstream,
                tempfile.NamedTemporaryFile(mode="w+") as actualstream,
            ):
                proc = subprocess.Popen(
                    xinfo['cmds']['sol'],
                    shell=True,
                    text=True,
                    stdin=inputstream,
                    stdout=actualstream,
                    stderr=subprocess.PIPE,
                )
                for line in proc.stderr:
                    if terminated.is_set(): break
                    logger.warning(line.strip())
                if terminated.is_set(): break
                
                actualstream.seek(0)
                actuals = actualstream.read()
                answers = inputstream.read()

                open(f'{tcfile}.out', 'w+').write(actuals)
                open(f'{tcfile}.ans', 'w+').write(answers)
                
                mistakes, rows = compare(actuals, answers)
                totalmis += mistakes
                msg = ''
                if mistakes:
                    msg = f'Wrong Answer on {mistakes} tokens!'
                    logger.error(msg)
                    logger.print_tktable(rows)
                else:
                    msg = f'AC in {0} ms'
                    logger.info(msg)
                if mistakes and tw == 2:
                    break
        logger.append('=' * 30)
        if (totalmis == 0):
            msg = f"All test cases passed"
            if terminated.is_set(): msg = "User terminated"
            logger.info(msg)
        else:
            msg = f"Some test cases failed"
            logger.error(msg)

    elif tw == 4:
        r, w = os.pipe()
        proc = subprocess.Popen(
            xinfo['cmd'],
            shell=True,
            text=True,
            stdout=w,
            stderr=w,
            close_fds=True,
        )
        for line in open(r):
            if terminated.is_set(): break
            logger.append(line.rstrip())
    terminated.clear()



import argparse
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('wd')
    p.parse_args()
    args = p.parse_args()
    xinfo = get_xinfo(args.wd)
    logger = TerminalLogger()
    try:
        run_xtask(xinfo, logger)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        log.exception(e)