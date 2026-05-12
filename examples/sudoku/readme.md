
# Explanation in a Sudoku puzzle

Here we have some Sudoku instances.
We may think an empty cell should have a specific number, but it may not be a correct filling.
In such a case we are interested in the question why that specific cell cannot have that number.

This type of explanation can be achieved via the use of xpit.
There are various ways to approach this explanation problem and in turn various resulting explanations.

Let's say we have a hard Sudoku instance; particularly `extreme_instance.lp` is one from sudoku.com.
We want to know why we cannot have 2 at cell (2,5).

- Tag all rules related to the Sudoku constraints in the finest granular way.

For instance, the follow tagged rule is about the constraint stating no number can appear more than once in a row.
Check the encoding file `sudoku.lp`.

```prolog
:- sudoku(X,Y,V), sudoku(X',Y,V), X != X',
   not _explain(same_num_in_row(Y,V,X,X'),msg("{} cannot appear twice in row {} and columns {},{}",(V,Y,X,X'))).
```

We have a run script that utilizes xpit. Let's run it.

```bash
$ python run_xpit_run1.py extreme_instance.lp sudoku.lp
Explanation #1
"5 cannot appear twice in row 4 and columns 5,1"
"3 cannot appear twice in row 5 and columns 6,3"
"2 cannot appear twice in row 4 and columns 8,5"
"6 cannot appear in sub-grid 4 due to 5,5 and 5,4"
"9 cannot appear in sub-grid 4 due to 5,5 and 5,4"
"2 cannot appear twice in column 6 and rows 7,5"
"6 cannot appear in sub-grid 4 due to 6,5 and 5,4"
"7 cannot appear twice in column 6 and rows 5,1"
"9 cannot appear in sub-grid 4 due to 6,5 and 5,4"
"6 cannot appear in sub-grid 4 due to 6,5 and 5,5"
"8 cannot appear in sub-grid 4 due to 4,6 and 5,4"
"9 cannot appear in sub-grid 4 due to 6,5 and 5,5"
"1 cannot appear in sub-grid 4 due to 5,4 and 4,4"
"8 cannot appear in sub-grid 4 due to 4,6 and 5,5"
"5 cannot appear twice in row 5 and columns 7,5"
"2 cannot be placed at (2,5)"
"3 cannot appear twice in column 5 and rows 4,2"
"2 cannot appear twice in row 5 and columns 5,2"
"3 cannot appear twice in column 5 and rows 5,2"
"1 cannot appear in sub-grid 4 due to 5,5 and 4,4"
"1 cannot appear in sub-grid 4 due to 6,5 and 4,4"
"4 cannot appear in sub-grid 4 due to 5,5 and 6,4"
"4 cannot appear in sub-grid 4 due to 6,5 and 6,4"
"7 cannot appear twice in column 5 and rows 8,4"
"8 cannot appear in sub-grid 4 due to 4,6 and 6,5"
"5 cannot appear twice in row 5 and columns 7,6"
"7 cannot appear twice in column 5 and rows 8,5"
"4 cannot appear in sub-grid 4 due to 6,4 and 5,4"
```

It seems like there are many related constraints concerning sub-grid 4 (i.e., the center sub-cell).
First, we can focus on constraints about the number 2, since we want to explain why 2 cannot be filled at (2,5).

```bash
$ python run_xpit_run2.py extreme_instance.lp sudoku.lp
"2 cannot appear twice in row 4 and columns 8,5"
"2 cannot be placed at (2,5)"
"2 cannot appear twice in row 5 and columns 5,2"
"2 cannot appear twice in column 6 and rows 7,5"
```

It is easy to see that 2 cannot be filled in cells (5,4), (5,5) and (6,5) in the center sub-cell.
It seems like we can explain our query using the center sub-cell.
But, it seems like cells (4,5), (5,6), and (6,6) have some forced values and they are not appearing the eMUS.
We can query their values using an additional program-base explainer and the following constraint.

```prolog
:- sudoku(X,Y,V), not initial(X,Y,_), pos(X,Y), val(V),
   not _explain(place(X,Y,V),msg("{} should be placed at ({},{})",(V,X,Y))).
```

The following is our next run.

```bash
$ python run_xpit_run3.py extreme_instance.lp sudoku.lp -n 0
...
Explanation #2
"7 should be placed at (4,5)"
Explanation #3
"5 should be placed at (5,6)"
Explanation #4
"3 should be placed at (6,6)"
Explanation #5
...
```

These explanations state that all these cells should have unique forced values.
For instance, cell (4,5) has the value 7.
We can have a detailed explanation for this cell, for instance using the following run.
It is easy to see that 7's in cells (5,8) and (6,1) causes (4,5) be the only empty cell in the center sub-grid filled with 7.

```bash
$ python run_xpit_run4.py extreme_instance.lp sudoku.lp --fact-sig initial/3 -n 0
...
Explanation #10
"Fact initial(4,4,1) is related to the no solutions result"
"Fact initial(4,6,8) is related to the no solutions result"
"Fact initial(5,8,7) is related to the no solutions result"
"7 should be placed at (4,5)"
"Fact initial(6,1,7) is related to the no solutions result"
...
```

Returning back to our original query, we now know that there is no place to fill 2 in the center sub-cell.


