
% An extreme sudoku instance from sudoku.com

%     1 2 3   4 5 6   7 8 9
%   +-------+-------+-------+
% 1 | 8 . 9 | 4 . 7 | . . 1 |
% 2 | . . . | . 3 . | . 7 . |
% 3 | 4 . . | . 8 . | . . . |
%   +-------+-------+-------+
% 4 | 5 . . | 1 . 4 | . 2 . |
% 5 | . ? 3 | . . . | 5 . . |
% 6 | . . . | 8 . . | . . . |
%   +-------+-------+-------+
% 7 | 3 . ? | 5 . 2 | . 1 . |
% 8 | . . . | . 7 . | . . . |
% 9 | . 6 . | . . . | . . 9 |
%   +-------+-------+-------+


#const dim=3.

initial(1,1,8).
initial(3,1,9).
initial(4,1,4).
initial(6,1,7).
initial(9,1,1).
initial(5,2,3).
initial(8,2,7).
initial(1,3,4).
initial(5,3,8).
initial(1,4,5).
initial(4,4,1).
initial(6,4,4).
initial(8,4,2).
initial(3,5,3).
initial(7,5,5).
initial(4,6,8).
initial(1,7,3).
initial(4,7,5).
initial(6,7,2).
initial(8,7,1).
initial(5,8,7).
initial(2,9,6).
initial(9,9,9).

% explanation query
%% :- not sudoku(3,7,4).

% explanation query
:- not sudoku(2,5,2), not _explain(query, msg("2 cannot be placed at (2,5)",())).


