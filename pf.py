#!/usr/bin/env python

import chess
import sys
from subprocess import Popen, PIPE

ON_POSIX = 'posix' in sys.builtin_module_names

sf = 'C:\Users\marco\Documents\programmi\stockfish\src\stockfish.exe'
test_epd = 'C:\Users\marco\Documents\programmi\stockfish\src\hard2016beta6.epd'

def read_epd(file):
    epd = []
    with open(file, 'r') as f:
        for line in f:
            epd.append(line)
    return epd

def run_stockfish(sf_path, fen, time, hash=1024, threads=3):
    cmd = ['setoption name Hash value ' + str(hash),
           'setoption name Threads value ' + str(threads),
           'position fen ' + fen,
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

def parse_position(line):
    pos = line.split('bm')
    if len(pos) < 2: # Catch empty or invalid line
        return '', '', '', 'skip line'
    (fen, san) = pos
    f = fen.split()
    attempts = [fen, ' '.join(f[:6]), ' '.join(f[:4]) + ' 0 1'] # Be forgiving on the fen format
    for fen in attempts:
        try:
            board = chess.Board(fen)
            break
        except:
            if fen == attempts[-1]: # At the end
                return '', '', '', "Invalid fen\n\n".format(attempts[0])
    san = san.split(';')[0]
    san = san.replace(',', ' ').replace('!', ' ').split()[0]
    attempts = [san, san + '+', san + '#'] # Be forgiving on the san format
    for san in attempts:
        try:
            board.push_san(san)
            break
        except:
            if san == attempts[-1]: # At the end
                return '', '', '', "Invalid best move: {}\n\n".format(attempts[0])

    return fen, san, board.fen(), 'OK'

def append_result(result_epd, line):
    with open(result_epd, 'a') as f:
        f.write(line)

def compare(score1, score2):
    if 'mate' in score1 or 'mate' in score2:
        return False
    score1 = score1.split('cp')[1].strip()
    score2 = score2.split('cp')[1].strip()
    return int(score1) > int(score2)

def run_session(engine, epd, time_per_move, result_epd):
    open(result_epd, 'w').close()
    for i in range(1, len(epd)):
        pos = epd[i-1].strip()
        (fen, san, new_fen, result) = parse_position(pos)
        if result == 'skip line':
            continue
        print("Position: {}/{}\nPos: {}".format(i, len(epd), pos))
        if result != 'OK':
            print(result)
            append_result(result_epd, pos + '\n')
            continue
        (bestmove, score1) = run_stockfish(engine, fen, time=time_per_move)
        board = chess.Board(fen)
        bestmove = board.san(chess.Move.from_uci(bestmove))
        print("Warm-up best move: {}, score: {}".format(bestmove, score1))
        if (bestmove == san):
            print("Best move already found!\n\n")
            append_result(result_epd, '\n')
            continue
        print("Forcing best move: {}".format(san))
        (bestmove, score2) = run_stockfish(engine, new_fen, time=time_per_move)
        print("After forcing best move, score: {}\n\n".format(score2))
        if compare(score1, score2):
            append_result(result_epd, pos + '\n')
        else:
            append_result(result_epd, '\n')

movetime = 2000
result_epd = test_epd.split('.epd')[0] + '_' + str(movetime / 1000) + 'sec.epd'
epd = read_epd(test_epd)
run_session(sf, epd, movetime, result_epd)
