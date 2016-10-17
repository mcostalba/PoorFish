#!/usr/bin/env python

from __future__ import print_function

import argparse
import os
import sys
from subprocess import Popen, PIPE
import chess

ON_POSIX = 'posix' in sys.builtin_module_names


def read_epd(fname):
    epd = []
    total = 0
    with open(fname, 'r') as f:
        for line in f:
            epd.append(line)
            if line.strip():
                total += 1
    return epd, total


def run(args, fen):
    cmd = ['setoption name Hash value ' + str(args.hash),
           'setoption name Threads value ' + str(args.threads),
           'position fen ' + fen,
           'go movetime ' + str(args.movetime)]
    p = args.process
    p.stdin.write('\n'.join(cmd) + '\n')  # Note the trailing '\n'
    line = ''
    while 'bestmove' not in line:
        line = p.stdout.readline()
        if 'score' in line:
            score = line.split('score ')[-1].split(' nodes')[0].strip()

    bestMove = line.split('bestmove')[1].strip().split(' ')[0]
    return bestMove, score


def try_until_ok(attempts, f):
    for item in attempts:
        try:
            return f(item)
        except:
            if item == attempts[-1]:  # At the end
                return None


def parse_position(line):
    pos = line.split('bm')
    if len(pos) < 2:  # Catch empty or invalid line
        return None, None, 'skip line'

    (fen, san) = pos
    f = fen.split()
    attempts = [fen, ' '.join(f[:6]), ' '.join(f[:4]) + ' 0 1']
    board = try_until_ok(attempts, chess.Board)
    if not board:
        return None, None, "Invalid fen {}\n\n".format(fen)

    san = san.replace(';', ' ').replace(',', ' ').replace('!', ' ').split()[0]
    san = san.replace('0-0-0', 'O-O-O').replace('0-0', 'O-O')
    attempts = [san, san + '+']
    move = try_until_ok(attempts, board.parse_san)
    if not move:
        return None, None, "Invalid best move {}\n\n".format(san)

    return board, board.san(move), 'OK'


class ResultWriter(object):
    def __init__(self, result_epd):
        self.result_epd = result_epd
        open(result_epd, 'w').close()  # Clear output file

    def __call__(self, pos = ''):
        with open(self.result_epd, 'a') as f:
            f.write(pos + '\n')


def compare(score1, score2):
    if 'mate' in score1 or 'mate' in score2:
        return False

    score1 = score1.split('cp')[1].strip()
    score2 = score2.split('cp')[1].strip()
    return int(score1) > -int(score2)


def run_session(args):
    append = ResultWriter(args.result_epd)
    epd, total = read_epd(args.testsuite)
    args.process = Popen(args.engine, stdout=PIPE, stdin=PIPE,
                         universal_newlines=True, close_fds=ON_POSIX)
    cnt = 0
    for pos in epd:
        pos = pos.strip()
        (board, san, result) = parse_position(pos)
        if result == 'skip line':
            append()
            continue

        cnt += 1
        print("Position: {}/{}\nPos: {}".format(cnt, total, pos))
        if result != 'OK':
            print(result)
            append(pos)
            continue

        (bestmove, score1) = run(args, board.fen())
        bestmove = board.san(chess.Move.from_uci(bestmove))
        print("Warm-up best move: {}, score: {}".format(bestmove, score1))
        if bestmove == san:
            print("Best move already found!\n\n")
            append()
            continue

        print("Forcing best move: {}".format(san))
        board.push_san(san)
        (bestmove, score2) = run(args, board.fen())
        print("After forcing best move, score: {}\n\n".format(score2))
        append(pos if compare(score1, score2) else '')

    args.process.stdin.close()  # Make the engine to quit
    args.process.wait()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description='Run DBT test on a epd testsuite')
    p.add_argument("engine", help="Path to the chess engine")
    p.add_argument("testsuite", help="Path to the epd testsuite file")
    p.add_argument("movetime", help="Time for position in milliseconds", type=int)
    p.add_argument("--threads", help="Number of threads", type=int, default=3)
    p.add_argument("--hash", help="Hash table size in MB", type=int, default=1024)
    args = p.parse_args()

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
          "{} milliseconds.\n"
          .format(args.testsuite, args.result_epd, args.movetime))

    run_session(args)
