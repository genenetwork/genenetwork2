This readme concerns the directory wqflask - an officially sanctioned fork of the main GeneNetwork
code.  It's still very early in the process - but we eventually want to port all of the code
in GeneNetwork to Flask and Jinja2.  For more information about the project in general, see
the file README.md.

For more information about the port to Flask, please keep reading.

*************************

Requirements:

* Python 2.7

* virtualenv 1.7.1.2 or later

* Other python dependencies are listed in the file wqflask/requirements.txt

**************************

Installation:

We highly recommend you create a virtual enviornment called ve27 in your home directory.

> cd ~

> virtualenv ve27

> source ~/ve27/bin/activate

> pip install -r ~/gene/wqflask/requirements.txt
(Or replace gene with the name of the directory holding your repository)
