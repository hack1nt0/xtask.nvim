import os, sys, io
import subprocess
from subprocess import Popen, PIPE
import argparse
import random as R
from cyaron import *

class Jurger:
    # read input
    def __init__(self):
        raise RuntimeError()


    # throw Runtime Error when wrong answer
    # when query is none, optionally answer init info to solver...
    def answer(self, query=None) -> str:
        if not query:
            pass
        else:
            pass
        raise RuntimeError()
    

    def print_chat(self, no, Q, A):
        print(no, Q, A, sep='\t', file=sys.stderr, flush=True)
    
    def run(self, sol_cmd):
        psol = Popen(
            f'/usr/bin/time -al {sol_cmd}',
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            text=True,
        )
        try:
            no = 0
            Q = None
            A = self.answer(Q)
            if A:
                no += 1
                self.print_chat(no, Q, A)
                # self.chats.append((Q, A))
                psol.stdin.write(A)
            for Q in psol.stdout:
                A = self.answer(Q)
                no += 1
                self.print_chat(no, Q, A)
                # self.chats.append((Q, A))
                psol.stdin.write(A)
        except BrokenPipeError:
            # self.print_chats()
            exit(1)
        except RuntimeError as e:
            # self.print_chats()
            exit(2)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('sol_cmd')
    args = p.parse_args()
    Jurger().run(args.sol_cmd)
