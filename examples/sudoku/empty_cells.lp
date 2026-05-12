
:- sudoku(X,Y,V), not initial(X,Y,_), pos(X,Y), val(V),
   not _explain(place(X,Y,V),msg("{} should be placed at ({},{})",(V,X,Y))).
