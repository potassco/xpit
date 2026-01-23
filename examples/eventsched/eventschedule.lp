%
% SIMPLE EVENT SCHEDULING
%
% - Sessions/topics are assigned to slots, where each slot is a period in a day.
%
% - Sessions need a specific number of slots to be scheduled.
%   eg. An art session needs 4 slots.
%
% - No session assigned to more than one day, can have an empty day in between its assigned slots.
%   (Don't break the schedule)
%
% - Some sessions must not be assigned to more than one slot in a day. (Separate to different days)
%
% - Some sessions must not be assigned to the same slot.
%   eg. Introduction to AI and AI in economics cannot share the same slot.
%

{ assign(Session,Slot) } :- session(Session), slot(Slot).

:- needs(Session,Num), Num != #count{ Slot: assign(Session,Slot) }.

% Don't break the schedule
must_assign(Session,D''):- assign(Session,(D,P)), assign(Session,(D',P')), D<D', conseq(D,D''), D''<D'.
:- must_assign(Session,D), not assign(Session,(D,_)),
   % not _explain(dont_break,msg("A session cannot be scheuled without a break day",())).
   %% not _explain(dont_break,msg("Session {} cannot be scheuled without a break day",(Session))).
   not _explain(dont_break,msg("Session {} has a gap on {}",(Session,D))).

% Don't put more than one session to the same day
:- separate_days(Session), assign(Session,(D,P)), assign(Session,(D,P')), P<P'.

% Don't use the same slot
:- no_same_slot(Session,Session'), assign(Session,Slot), assign(Session',Slot).

% Use only this day
:- only_this_day(Session,D), assign(Session,(D',_)), D!=D'.

#show.
#show assign/2.
#show must_assign/2.

#defined _explain/2.
