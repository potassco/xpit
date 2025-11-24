% a(X) :- X=1..3, not _explain(integrety_constraint_violated, msg("a{} is derived.",X)).
% :- a(X).

% #defined _explain/2.

a(X) :- X=1..3, not _explain(test,msg("depends on {}",(X))).
:- a(X).

#defined _explain/2.
