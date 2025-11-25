a(X) :- X=1..3, not _explain(test,msg("depends on {}",(X))).
:- a(X).

#defined _explain/2.
