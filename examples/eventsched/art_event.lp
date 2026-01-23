%
% Art event scheduling
% This instance has no solutions.
%

% #theory explanation {
%     constant { - : 0, unary };
%     &explanation/0:constant,any
% }.

% We have 3 days and 2 sessions (morning and afternoon) in each day.
slot((day1,m)).
slot((day1,a)).
slot((day2,m)).
slot((day2,a)).
slot((day3,m)).
slot((day3,a)).

conseq(day1,day2).
conseq(day2,day3).

% Sessions are education, future trends, and community building.
session(edu).
session(fut).
session(comu).
% needs(edu,3).
needs(edu,2).
needs(fut,2).
needs(comu,2).

% separate to different days: fut and comu
separate_days(comu) :- not _explain(separate_days,msg("Session {} cannot be separeted",("comu",))).
separate_days(edu) :- not _explain(separate_days,msg("Session {} cannot be separeted",("edu",))).

% don't assign edu to the same slot with others
no_same_slot(edu,comu) :- not _explain(not_in_same_slot,msg("Sessions {} and {} cannot be scheduled without sharing a slot",("edu", "comu"))).
no_same_slot(edu,fut) :- not _explain(not_in_same_slot,msg("Sessions {} and {} cannot be scheduled without sharing a slot",("edu", "fut"))).

% Use only day1 for fut
only_this_day(fut,day2).
