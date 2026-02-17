
a(Y) :- Y = 1..2, not _explain(r1(Y), msg("this rule causes a problem",())).
b(Y) :- Y = 1..2, not _explain(r1, msg("this rule causes a problem",())).

:- not a(1), not a(2).
:- a(1), a(2).
{a(1..2)}.

#defined _explain/2.
