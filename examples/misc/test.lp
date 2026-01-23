%a(Y) :- Y = 1..2, X=1..2, not _explain(r1, msg("for X={}",(X))).
a(Y) :- Y = 1..2, not _explain(r1, msg("this rule causes a problem {}",(Y))).
:- not a(1), not a(2).
:- a(1), a(2).
{a(1..2)}.

#defined _explain/2.
