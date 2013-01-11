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


Get into your home directory
> cd ~

Create a virtual environment
> virtualenv ve27

Activate the environment
> source ~/ve27/bin/activate

Install dependencies
> pip install -r ~/gene/wqflask/requirements.txt
(Or replace gene with the name of the directory holding your repository)

**************************

Running the program:

Assuming your enviornment is activated (source ~/ve27/bin/activate) just run:

> python ~/gene/wqflask/runserver.py

The program as configured runs on port 5000 and does not serve static files.

You'll have to run a webserver to serve pages on port 80 and to server the static files (or
flask could also be configured to serve the static pages).

A sample configuration file for nginx is in the directory: wqflask/other_config/nginx.conf
