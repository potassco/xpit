
% define dim in the instance program
val(1..dim*dim).
pos(X,Y) :- val(X), val(Y).

subgrid(X,Y,(((X-1)/dim)*dim+((Y-1)/dim))) :- pos(X,Y).

1 { sudoku(X,Y,V) : val(V) } 1 :- pos(X,Y).
   %% not _explain(cannot_fill(X,Y),msg("{}x{} cannot be filled",(X,Y))).

% no same number in a row
:- sudoku(X,Y,V), sudoku(X',Y,V), X != X',
   %% not initial(X',Y,V), not initial(X,Y,V).
   not _explain(same_num_in_row(Y,V,X,X'),msg("{} cannot appear twice in row {} and columns {},{}",(V,Y,X,X'))).
   %% not _explain(same_num_in_row(Y,V,X),msg("{} cannot be placed in row {} and column {}",(V,Y,X))).
   %% not _explain(same_num_in_row(Y,V),msg("{} cannot be placed in row {}",(V,Y))).
   %% not _explain(same_num_in_row(Y),msg("Same number cannot repeat in row {}",(Y,))).
   %% not _explain(cannot_fill_at(V,X,Y),msg("{} cannot be placed at ({},{}) due to {} constraint", (V,X,Y,row,X'))).

% no same number in a column
:- sudoku(X,Y,V), sudoku(X,Y',V), Y != Y',
   %% not initial(X,Y',V), not initial(X,Y,V).
   not _explain(same_num_in_column(X,V,Y,Y'),msg("{} cannot appear twice in column {} and rows {},{}",(V,X,Y,Y'))).
   %% not _explain(same_num_in_column(X,V,Y),msg("{} cannot be placed in column {} and row {}",(V,X,Y))).
   %% not _explain(same_num_in_column(X,V),msg("{} cannot be placed in column {}",(V,X))).
   %% not _explain(same_num_in_column(X),msg("Same number cannot repeat in column {}",(X,))).
   %% not _explain(cannot_fill_at(V,X,Y),msg("{} cannot be placed at ({},{}) due to {} constraint", (V,X,Y,column,Y'))).

% no same number in a sub-grid
:- sudoku(X,Y,V), sudoku(X',Y',V), subgrid(X,Y,S), subgrid(X',Y',S), (X,Y)!=(X',Y'),
   %% not initial(X',Y',V), not initial(X,Y,V).
   not _explain(same_num_in_subgrid(S,V,X,Y,X',Y'),msg("{} cannot appear in sub-grid {} due to {},{} and {},{}",(V,S,X,Y,X',Y'))).
   %% not _explain(same_num_in_subgrid(S,V,X,Y),msg("{} cannot be placed in sub-grid {} at ({},{})",(V,S,X,Y))).
   %% not _explain(same_num_in_subgrid(S,V),msg("{} cannot be placed in sub-grid {}",(V,S))).
   %% not _explain(same_num_in_subgrid(S),msg("Same number cannot repeat in sub-grid {}",(S,))).
   %% not _explain(cannot_fill_at(V,X,Y),msg("{} cannot be placed at ({},{}) due to {} constraint", (V,X,Y,subgrid,X',Y'))).

sudoku(X,Y,V) :- initial(X,Y,V).

#show sudoku/3.
#show subgrid/3.
