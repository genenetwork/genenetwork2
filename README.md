[![DOI](https://zenodo.org/badge/5591/genenetwork/genenetwork2.svg)](https://zenodo.org/badge/latestdoi/5591/genenetwork/genenetwork2) [![JOSS](http://joss.theoj.org/papers/10.21105/joss.00025/status.svg)](http://joss.theoj.org/papers/10.21105/joss.00025)
[![GeneNetwork2 CI
badge](https://ci.genenetwork.org/badge/genenetwork2.svg)](https://ci.genenetwork.org/jobs/genenetwork2)


# GeneNetwork

This repository contains the current source code for GeneNetwork (GN)
(https://www.genenetwork.org/ (version 2). GN2 is a Web
2.0-style framework that includes data and computational tools for online genetics and genomic analysis of
many different populations and many types of molecular, cellular, and physiological data.
The system is used by scientists and clinicians in the field of precision health care and systems genetics.
GN and its predecessors have been in operation since Jan 1994, making it one of the longest-lived web services in biomedical research (https://en.wikipedia.org/wiki/GeneNetwork, and see a partial list of publications using GN and its predecessor, WebQTL (https://genenetwork.org/references/).

## Install

The recommended installation is with GNU Guix which allows you to
deploy GN2 and dependencies as a self contained unit on any machine.
The database can be run separately as well as the source tree (for
developers).  See the [installation docs](doc/README.org).

## Configuration

GeneNetwork2 comes with a [default configuration file](./etc/default_settings.py)
which can be used as a starting point.

The recommended way to deal with the configurations is to **copy** this default configuration file to a location outside of the repository, say,

```sh
.../genenetwork2$ cp etc/default_settings.py "${HOME}/configurations/gn2.py"
```

then change the appropriate values in the new file. You can then pass in the new
file as the configuration file when launching the application,

```sh
.../genenetwork2$ bin/genenetwork "${HOME}/configurations/gn2.py" <command-to-run>
```

The other option is to override the configurations in `etc/default_settings.py`
by setting the configuration you want to override as an environment variable e.g.
to override the `SQL_URI` value, you could do something like:

```sh
.../genenetwork2$ env SQL_URI="mysql://<user>:<passwd>@<host>:<port>/<db_name>" \
	bin/genenetwork "${HOME}/configurations/gn2.py" <command-to-run>
```

replacing the placeholders in the angle brackets with appropriate values.

For a detailed breakdown of the configuration variables and their use, see the
[configuration documentation](doc/configurations.org)

## Run

Once having installed GN2 it can be run through a browser
interface

```sh
genenetwork2
```

A quick example is

```sh
env GN2_PROFILE=~/opt/gn-latest SERVER_PORT=5300 \
    GENENETWORK_FILES=~/data/gn2_data/ \
    GN_PROXY_URL="http://localhost:8080"\
    GN3_LOCAL_URL="http://localhost:8081"\
	SPARQL_ENDPOINT=http://localhost:8892/sparql\
    ./bin/genenetwork2 ./etc/default_settings.py -gunicorn-dev
```

For full examples (you may need to set a number of environment
variables), including running scripts and a Python REPL, also see the
startup script [./bin/genenetwork2](https://github.com/genenetwork/genenetwork2/blob/testing/bin/genenetwork2).

Also mariadb and redis need to be running, see
[INSTALL](./doc/README.org).

## Debugging

To run the application under the pdb debugger, you can add the `--with-pdb`
option when launching the application, for example:

```sh
env GN2_PROFILE=~/opt/gn-latest SERVER_PORT=5300 \
    GENENETWORK_FILES=~/data/gn2_data/ \
    GN_PROXY_URL="http://localhost:8080"\
    GN3_LOCAL_URL="http://localhost:8081"\
	SPARQL_ENDPOINT=http://localhost:8892/sparql\
    ./bin/genenetwork2 ./etc/default_settings.py --with-pdb
```

**NOTE**: This should only ever be run in development.
**NOTE 2**: You will probably need to tell pdb to continue at least once before
the system begins serving the pages.

Now, you can add the `breakpoint()` call wherever you need to debug and the
terminal where you started the application with `--with-pdb` will allow you to
issue commands to pdb to debug your application.

## Development

It may be useful to pull in the GN3 python modules locally. For this
use `GN3_PYTHONPATH` environment that gets injected in
the ./bin/genenetwork2 startup.

A continuously deployed instance of genenetwork2 is available at
[https://cd.genenetwork.org/](https://cd.genenetwork.org/). This
instance is redeployed on every commit provided that the [continuous
integration tests](https://ci.genenetwork.org/jobs/genenetwork2) pass.

## Testing

To have tests pass, the redis and mariadb instance should be running, because of
asserts sprinkled in the code base.

Right now, the only tests running in CI are unittests. Please make
sure the existing unittests are green when submitting a PR.

From the root directory of the repository, you can run the tests with something
like:

```sh
env GN_PROFILE=~/opt/gn-latest SERVER_PORT=5300 \
	SQL_URI=<uri-to-override-the-default> \
	./bin/genenetwork2 ./etc/default_settings.py \
	-c -m pytest -vv
```

In the case where you use the default `etc/default_settings.py` configuration file, you can override any setting as demonstrated with the `SQL_URI` setting in the command above.

In order to avoid having to set up a whole host of settings every time with the `env` command, you could copy the `etc/default_settings.py` file to a new location (outside the repository is best), and pass that to `bin/genenetwork2` instead.

See
[./bin/genenetwork2](https://github.com/genenetwork/genenetwork2/blob/testing/doc/docker-container.org)
for more details.

#### Mechanical Rob

We are building 'Mechanical Rob' automated testing using Python
[requests](https://github.com/genenetwork/genenetwork2/tree/testing/test/requests)
which can be run with:

```sh
env GN2_PROFILE=~/opt/gn-latest \
    ./bin/genenetwork2 \
    GN_PROXY_URL="http://localhost:8080" \
    GN3_LOCAL_URL="http://localhost:8081 "\
    ./etc/default_settings.py -c \
    ../test/requests/test-website.py -a http://localhost:5003
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
alias runpython="env GN2_PROFILE=~/opt/gn-latest TMPDIR=/tmp SERVER_PORT=5004 GENENETWORK_FILES=/gnu/data/gn2_data/ GN_PROXY_URL="http://localhost:8080" GN3_LOCAL_URL="http://localhost:8081" ./bin/genenetwork2

alias runcmd="time env GN2_PROFILE=~/opt/gn-latest TMPDIR=//tmp SERVER_PORT=5004 GENENETWORK_FILES=/gnu/data/gn2_data/ GN_PROXY_URL="http://localhost:8080" GN3_LOCAL_URL="http://localhost:8081" ./bin/genenetwork2 ./etc/default_settings.py -cli"
```

Replace some of the env variables as per your use case.

### Troubleshooting

If the menu does not pop up check your `GN2_BASE_URL`. E.g.

```
curl http://gn2-pjotr.genenetwork.org/api/v_pre1/gen_dropdown
```

check the logs. If there is ERROR 1054 (42S22): Unknown column
'InbredSet.Family' in 'field list' it may be you are trying the small
database.

### Run Scripts

As part of the profiling effort, some scripts are added to run specific parts of the system under a profiler without running the entire web-server - as such, to run the script, you could do something like:

```
env HOME=/home/frederick \
    GN2_PROFILE=~/opt/gn2-latest \
    GN3_DEV_REPO_PATH=~/genenetwork/genenetwork3 \
    SQL_URI="mysql://username:password@host-ip:host-port/db_webqtl" \
	SPARQL_ENDPOINT=http://localhost:8892/sparql\
    SERVER_PORT=5001 \
    bin/genenetwork2 ../gn2_settings.py \
    -cli python3 -m scripts.profile_corrs \
	../performance_$(date +"%Y%m%dT%H:%M:%S").profile
```

and you can find the performance metrics at the file specified, in this case, a file starting with `performance_` with the date and time of the run, and ending with `.profile`.

Please replace the environment variables in the sample command above with the appropriate values for your environment.

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
