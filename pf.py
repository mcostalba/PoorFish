#!/usr/bin/env python

import sys
from subprocess import Popen, PIPE

ON_POSIX = 'posix' in sys.builtin_module_names

engine = 'C:\Users\marco\Documents\programmi\stockfish\src\stockfish'
test_epd = 'C:\Users\marco\Documents\programmi\stockfish\src\web.epd'
time_per_move = 2000

def read_epd(file):
    epd = []
    with open(file, 'r') as f:
        for line in f:
            epd.append(line.decode("utf-8"))
    return epd

def run_stockfish(sf_path, fen, time, forced_bm='', hash=1024, threads=3):
    if forced_bm:
        forced_bm = ' moves ' + forced_bm

    cmd = ['setoption name Hash value ' + str(hash),
           'setoption name Threads value ' + str(threads),
           'position fen ' + fen + forced_bm,
           'go movetime ' + str(time)]

    p = Popen(sf_path, stdout=PIPE, stdin=PIPE, universal_newlines=True, close_fds=ON_POSIX)
    p.stdin.write('\n'.join(cmd) + '\n') # Note the trailing '\n'
    line = ''
    while 'bestmove' not in line:
        line = p.stdout.readline()
        if 'score' in line:
            score = line.split('score ')[-1].split(' nodes')[0].strip()

    bestMove = line.split('bestmove')[1].strip().split(' ')[0]
    p.stdin.close()
    exit_code = p.wait()
    return bestMove, score

epd = read_epd(test_epd)
for i in range(1, len(epd)):
    fen = epd[i-1].split('bm')[0]
    print("Position: {}/{}\nFen: {}".format(i, len(epd), fen))
    (bestmove, score) = run_stockfish(engine, fen, time=time_per_move)
    print("Warm-up best move: {}, score: {}\nForcing best move: {}".format(bestmove, score, bestmove))
    (bestmove, score) = run_stockfish(engine, fen, time=time_per_move, forced_bm=bestmove)
    print("After forcing best move, score: {}\n\n".format(score))




