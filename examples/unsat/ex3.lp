{ a } :- not _explain(r1,msg(rule1,())).
{ b } :- not a, not _explain(r2,msg(rule2,())).
:- a, not _explain(r3,msg(rule3,())).
:- b, not _explain(r4,msg(rule4,())).
:- not a, not b, not c, not _explain(r5,msg(rule5,())).
d :- not a, not _explain(r6, msg(rule6,())).
:- not d, not _explain(r7, msg(rule7,())).
