# xpit

## Preliminary Installation Instructions during Development:

To install the project, run

```bash
pip install -e .[dev]
```

Consider using pre-commit.

## Installation

To install the project, run

```bash
pip install .
```

## Usage

Run the following for basic usage information:

```bash
xpit -h
```

To generate and open the documentation, run

```bash
mkdocs serve -o
```

Make sure to install the optional documentation dependencies via

```bash
pip install .[doc]
```

## Examples

To extract an explanation

```sh
python src/exp_director.py <encoding_file1.lp > ... <encoding_file_n.lp >  --assumpt-num=<assumption-bdget>
```

One example is given in the resources: To run it, specify use the following
command: Together with the explanation director, there is an encoding given.
You can run this with the following command (--outf=3 mutes the clingo prints):

```sh
python src/xpit/exp_director.py resources/eventschedule_orig.lp resources/art_event_orig.lp --assumpt-num=10 --outf=3
```

Instructions to install and use `nox` can be found in
[DEVELOPMENT.md](./DEVELOPMENT.md)

""" This module utilizes the standard python logging library for logging
purposes. Users are responsible for configuring logging in their application as
needed. Refer to the python logging documentation for configuration details.
"""
