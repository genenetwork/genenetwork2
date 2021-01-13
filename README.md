[![DOI](https://zenodo.org/badge/5591/genenetwork/genenetwork2.svg)](https://zenodo.org/badge/latestdoi/5591/genenetwork/genenetwork2) [![JOSS](http://joss.theoj.org/papers/10.21105/joss.00025/status.svg)](http://joss.theoj.org/papers/10.21105/joss.00025)
[![Actions Status](https://github.com/genenetwork/genenetwork2/workflows/tests/badge.svg)](https://github.com/genenetwork/genenetwork2/actions)

# GeneNetwork

This repository contains the current source code for GeneNetwork (GN)
(https://www.genenetwork.org/ (version 2). GN2 is a Web
2.0-style framework that includes data and computational tools for online genetics and genomic analysis of 
many different populations and many types of molecular, cellular, and physiological data. 
The system is used by scientists and clinians in the field of precision health care and systems genetics.
GN and its predecessors have been in operation since Jan 1994, making it one of the longest-lived web services in biomedical research (https://en.wikipedia.org/wiki/GeneNetwork, and see a partial list of publications using GN and its predecessor, WebQTL (https://genenetwork.org/references/).

## Install

The recommended installation is with GNU Guix which allows you to
deploy GN2 and dependencies as a self contained unit on any machine.
The database can be run separately as well as the source tree (for
developers).  See the [installation docs](doc/README.org).

## Run

Once having installed GN2 it can be run through a browser
interface

```sh
genenetwork2
```

(default is http://localhost:5003/). A quick example is

```sh
env GN2_PROFILE=~/opt/gn-latest SERVER_PORT=5300 GENENETWORK_FILES=~/data/gn2_data/ ./bin/genenetwork2 ./etc/default_settings.py -gunicorn-dev
```

For full examples (you may need to set a number of environment
variables), including running scripts and a Python REPL, also see the
startup script [./bin/genenetwork2](https://github.com/genenetwork/genenetwork2/blob/testing/bin/genenetwork2).

Also mariadb and redis need to be running, see
[INSTALL](./doc/README.org).

## Testing

To have tests pass, the redis and mariadb instance should be running, because of
asserts sprinkled in the code base.

Right now, the only tests running in CI are unittests. Please make
sure the existing unittests are green when submitting a PR.

See
[./bin/genenetwork2](https://github.com/genenetwork/genenetwork2/blob/testing/doc/docker-container.org)
for more details.

#### Mechanical Rob

We are building 'Mechanical Rob' automated testing using Python
[requests](https://github.com/genenetwork/genenetwork2/tree/testing/test/requests)
which can be run with:

```sh
env GN2_PROFILE=~/opt/gn-latest ./bin/genenetwork2 ./etc/default_settings.py -c ../test/requests/test-website.py -a http://localhost:5003
```

The GN2_PROFILE is the Guix profile that contains all
dependencies. The ./bin/genenetwork2 script sets up the environment
and executes test-website.py in a Python interpreter. The -a switch
says to run all tests and the URL points to the running GN2 http
server.

#### Unit tests

To run unittests, first `cd` into the genenetwork2 directory:

```sh
# You can use the coverage tool to run the tests
# You could omit the -v which makes the output verbose
runcmd coverage run -m unittest discover -v

# Alternatively, you could run the unittests using:
runpython -m unittest discover -v

# To generate a report in wqflask/coverage_html_report/:
runcmd coverage html
```

The `runcmd` and `runpython` are shell aliases defined in the following way:

```sh
alias runpython="env GN2_PROFILE=~/opt/gn-latest TMPDIR=/tmp SERVER_PORT=5004 GENENETWORK_FILES=/gnu/data/gn2_data/ ./bin/genenetwork2

alias runcmd="time env GN2_PROFILE=~/opt/gn-latest TMPDIR=//tmp SERVER_PORT=5004 GENENETWORK_FILES=/gnu/data/gn2_data/ ./bin/genenetwork2 ./etc/default_settings.py -cli"
```

Replace some of the env variables as per your use case.

## Documentation

User documentation can be found
[here](http://gn2.genenetwork.org/help).  The architecture of the
software stack is described [here](./doc/Architecture.org).  The
database schema is (still) shared with GN1 and currently described
[here](http://www.genenetwork.org/webqtl/main.py?FormID=schemaShowPage). Software
documentation is being expanded in the
[source code repository](https://github.com/genenetwork/genenetwork2/tree/master/doc).

## Contributing

Issues can be raised through
[github](https://github.com/genenetwork/genenetwork2/issues).

Contribute to GN2 source code by forking the
[github repository](https://github.com/genenetwork/genenetwork2/) with
git and sending us pull requests.

For development GN2 has a [mailing
list](http://listserv.uthsc.edu/mailman/listinfo/genenetwork-dev) and
an active IRC channel #genenetwork on freenode.net with a [web
interface](http://webchat.freenode.net/).

## License

The GeneNetwork2 source code is released under the Affero General
Public License 3 (AGPLv3). See [LICENSE.txt](LICENSE.txt).


## More information

For more information visit http://www.genenetwork.org/

## Cite

[![JOSS](http://joss.theoj.org/papers/10.21105/joss.00025/status.svg)](http://joss.theoj.org/papers/10.21105/joss.00025)

GeneNetwork was published in the Journal of Open Source Software as 'GeneNetwork: framework for web-based genetics' by Zachary Sloan, Danny Arends, Karl W. Broman, Arthur Centeno, Nicholas Furlotte, Harm Nijveen, Lei Yan, Xiang Zhou, Robert W. WIlliams and Pjotr Prins

You may also cite the software using

[![DOI](https://zenodo.org/badge/5591/genenetwork/genenetwork2.svg)](https://zenodo.org/badge/latestdoi/5591/genenetwork/genenetwork2).

## Contact

IRC on #genenetwork on irc.freenode.net.

Code and primary web service managed by Dr. Robert W. Williams and the
University of Tennessee Health Science Center, Memphis TN, USA.
