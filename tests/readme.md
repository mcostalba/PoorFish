*** Tests Results ***

This directory contains DBT tests results. Files have following naming convention:

foo.epd           -> Original foo.epd testsuite
foo_xxsec.epd     -> DBT test of xx+xx seconds with 3 threads, 1024 GB hash
foo...result.txt  -> Log of the corresponding DBT test
foo_vincent...epd -> Repeated 3 runs at medium TC, high core count by Vincent Lejeune
foo_xx_yy...epd   -> Concatenation of tests xx + yy + ...

The resulting epd file has the failed positions removed, the succesful ones are
kept in the original place, so to easy lookup through test concatenation, in
particular line number of a given position is preserved and corresponds to
the same line number in the original testsuite.

DBT stands for "Double Blind Test" where a normal search is first performed to
get a baseline score, then, if the best move is still not found, the best move
is forced and the position researched, if after the second search the score is
still lower than the former baseline, then the test is considered passed.
