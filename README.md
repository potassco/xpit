this is a first prototyp.

## Installation

Create new python environment (developed on python 3.13).
Install clingo using pip: pip install clingo=5.8
Install clingexplaid using pip: pip install clingexplaid=1.4
You might need to install the constraint handler if required by your project.

## Example

To run an example, use the following command:

```sh
python exp_director.py <encoding_file1.lp > ... <encoding_file_n.lp >  --assumpt-num=<assumption-bdget>
```

Together with the explanation director, there is an encoding given. You can run this with the following command:

```sh
python exp_director.py eventschedule_orig.lp art_event_orig.lp --assumpt-num=10
```