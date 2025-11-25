% a(X) :- X=1..3, not _explain(integrety_constraint_violated, msg("a{} is derived.",X)).
% :- a(X).

% #defined _explain/2.

a(X) :- X=1..3, not _explain(a_of_x_is_deduced_hence_violating_a_constraint,msg("exp depends on X={}",(X))).
:- a(X).

#defined _explain/2.
