#!/usr/bin/env python

import argparse
import chess
import os
import sys
from subprocess import Popen, PIPE

ON_POSIX = 'posix' in sys.builtin_module_names

def read_epd(file):
    epd = []
    cnt = 0
    with open(file, 'r') as f:
        for line in f:
            epd.append(line)
            if line.strip():
                cnt += 1
    return epd, cnt

def run(args, fen):
    cmd = ['setoption name Hash value ' + str(args.hash),
           'setoption name Threads value ' + str(args.threads),
           'position fen ' + fen,
           'go movetime ' + str(args.movetime)]
    p = args.process
    p.stdin.write('\n'.join(cmd) + '\n') # Note the trailing '\n'
    line = ''
    while 'bestmove' not in line:
        line = p.stdout.readline()
        if 'score' in line:
            score = line.split('score ')[-1].split(' nodes')[0].strip()
    bestMove = line.split('bestmove')[1].strip().split(' ')[0]
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
    attempts = [san, san + '+'] # Be forgiving on the san format
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
    return int(score1) > -int(score2)

def run_session(args):
    open(args.result_epd, 'w').close() # Clear output file
    epd, total = read_epd(args.testsuite)
    args.process = Popen(args.engine, stdout=PIPE, stdin=PIPE, universal_newlines=True, close_fds=ON_POSIX)
    cnt = 0
    for i in range(1, len(epd)):
        pos = epd[i-1].strip()
        (fen, san, new_fen, result) = parse_position(pos)
        if result == 'skip line':
            append_result(args.result_epd, '\n')
            continue
        cnt += 1
        print("Position: {}/{}\nPos: {}".format(cnt, total, pos))
        if result != 'OK':
            print(result)
            append_result(args.result_epd, pos + '\n')
            continue
        (bestmove, score1) = run(args, fen)
        board = chess.Board(fen)
        bestmove = board.san(chess.Move.from_uci(bestmove))
        print("Warm-up best move: {}, score: {}".format(bestmove, score1))
        if (bestmove == san):
            print("Best move already found!\n\n")
            append_result(args.result_epd, '\n')
            continue
        print("Forcing best move: {}".format(san))
        (bestmove, score2) = run(args, new_fen)
        print("After forcing best move, score: {}\n\n".format(score2))
        if compare(score1, score2):
            append_result(args.result_epd, pos + '\n')
        else:
            append_result(args.result_epd, '\n')
    args.process.stdin.close() # Make the engine to quit
    args.process.wait()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run DBT test on a epd testsuite')
    parser.add_argument("engine", help="Path to the chess engine")
    parser.add_argument("testsuite", help="Path to the epd testsuite file")
    parser.add_argument("movetime", help="Time for each position in milliseconds", type=int)
    parser.add_argument("--threads", help="Number of threads", type=int, default=3)
    parser.add_argument("--hash", help="Hash table size in MB", type=int, default=1024)
    args = parser.parse_args()

    if not os.path.isfile(args.engine):
        print("Engine {} not found.".format(args.engine))
        sys.exit(0)

    if not os.path.isfile(args.testsuite):
        print("Testsuite {} not found.".format(args.testsuite))
        sys.exit(0)

    fname = args.testsuite.split('.epd')[0]
    args.result_epd = fname + '_' + str(args.movetime / 1000) + 'sec.epd'

    print("Running DBT on {}, successful positions will be written \ninto {}, "
          "preserving line number. Each position will \nbe searched for "
          "{} milliseconds.\n".format(args.testsuite, args.result_epd, args.movetime))

    run_session(args)
