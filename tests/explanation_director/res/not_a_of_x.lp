a(X) :- X=1..3, not _explain(a_of_x_is_deduced_hence_violating_a_constraint,
msg("The programming is failing because of a({}).",(X))).
:- a(X).

#defined _explain/2.
