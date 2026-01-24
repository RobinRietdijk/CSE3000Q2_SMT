row(1..n).
column(1..n).

number(1..n).

0 { is_white(X, Y) : cell(X, Y, Z) } 1 :- row(X), number(Z).
0 { is_white(X, Y) : cell(X, Y, Z) } 1 :- column(Y), number(Z).

is_black(X, Y) :- not is_white(X, Y), row(X), column(Y).

:- is_black(X, Y), is_black(X, Y + 1).
:- is_black(X, Y), is_black(X + 1, Y).


is_connected(X, Y) :- is_connected(X - 1, Y), is_white(X - 1, Y).
is_connected(X, Y) :- is_connected(X + 1, Y), is_white(X + 1, Y).
is_connected(X, Y) :- is_connected(X, Y + 1), is_white(X, Y + 1).
is_connected(X, Y) :- is_connected(X, Y - 1), is_white(X, Y - 1).

:- not is_connected(X, Y), is_white(X, Y).

is_connected(n/2, n/2) :- is_white(n/2, n/2).
is_connected(n/2, n/2+1) :- is_white(n/2, n/2+1).
