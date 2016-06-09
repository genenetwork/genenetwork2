[![DOI](https://zenodo.org/badge/5591/genenetwork/genenetwork2.svg)](https://zenodo.org/badge/latestdoi/5591/genenetwork/genenetwork2)

# GeneNetwork

This repository contains the source code for the GeneNetwork (GN)
server http://gn2.genenetwork.org/ (version 2 aka GN2). GN is a Web
2.0 style framework with included tools for doing genetics online
using high-throughput data. GN is used for a wide range of studies. An
exhaustive list of publications mentioning GN and its previous
incarnation WebQTL can be found
[here](http://www.genenetwork.org/reference.html).

## Install

The recommended installation is with GNU Guix which allows you to
deploy GN2 and dependencies as a self contained unit on any machine.
The database can be run separately as well as the source tree (for
developers).  See the [installation docs](doc/README.org).

## Test

Once installed GN2 can be run online through a browser interface

```sh
./bin/genenetwork2
```

(default is http://localhost:5003/). We are building up automated
testing using [mechanize](https://github.com/genenetwork/genenetwork2/tree/master/test/lib) which can be run with

```sh
./bin/test-website
```

## Documentation

User documentation can be found
[here](http://gn2.genenetwork.org/help).  The database schema is
shared with GN1 and described
[here](http://www.genenetwork.org/webqtl/main.py?FormID=schemaShowPage). Software
documentation is being expanded in the [source code repository](https://github.com/genenetwork/genenetwork2/tree/master/doc).

## Contributing

Issues can be raised through
[github](https://github.com/genenetwork/genenetwork2/issues).

Contribute to GN2 source code by forking the
[github repository](https://github.com/genenetwork/genenetwork2/) with
git and sending us pull requests.

For development GN2 has a
[mailing list](http://listserv.uthsc.edu/mailman/listinfo/genenetwork-dev)
and an active IRC channel #genenetwork on freenode.net with a
[web interface](http://webchat.freenode.net/).

## License

The GeneNetwork2 source code is released under the Affero General
Public License 3 (AGPLv3). See [LICENSE.txt](LICENSE.txt).


## More information

For more information visit http://www.genenetwork.org/

## Cite

You can cite this software using
[![DOI](https://zenodo.org/badge/5591/genenetwork/genenetwork2.svg)](https://zenodo.org/badge/latestdoi/5591/genenetwork/genenetwork2). 

## Contact

IRC on #genenetwork on irc.freenode.net.

Code and primary web service managed by Dr. Robert W. Williams and the
University of Tennessee Health Science Center, Memphis TN, USA. 

