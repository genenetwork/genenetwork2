[![DOI](https://zenodo.org/badge/5591/genenetwork/genenetwork2.svg)](https://zenodo.org/badge/latestdoi/5591/genenetwork/genenetwork2) [![JOSS](http://joss.theoj.org/papers/10.21105/joss.00025/status.svg)](http://joss.theoj.org/papers/10.21105/joss.00025)
[![GeneNetwork2 CI
badge](https://ci.genenetwork.org/badge/genenetwork2.svg)](https://ci.genenetwork.org/jobs/genenetwork2)


# GeneNetwork

This repository contains the current source code for GeneNetwork (GN2) https://genenetwork.org/ (version 2). GN2 is a Web 2.0-style framework that includes data and computational tools for online genetics and genomic analysis of many different populations and many types of molecular, cellular, and physiological data. The system is used by scientists and clinicians in the field of precision health care and systems genetics. GN and its predecessors have been in operation since Jan 1994, making it one of the longest-lived web services in biomedical research (https://en.wikipedia.org/wiki/GeneNetwork, and see a partial list of publications using GN and its predecessor, WebQTL https://genenetwork.org/references/).

## Install

The recommended installation is with GNU Guix which allows you to deploy GN2 and dependencies as a self contained unit on any machine. The database can be run separately as well as the source tree (for developers).  See the [installation docs](doc/README.org).

## Documentation

User documentation can be found [here](https://genenetwork.org/help).  The architecture of the software stack is described [here](./doc/Architecture.org).  The database schema is (still) shared with GN1 and currently described [here](http://www.genenetwork.org/webqtl/main.py?FormID=schemaShowPage). Software documentation is being expanded in the [source code repository](https://github.com/genenetwork/genenetwork2/tree/master/doc).

## Contributing

Issues can be raised through
[github](https://issues.genenetwork.org/).

Contribute to GN2 source code by forking the
[github repository](https://github.com/genenetwork/genenetwork2/) with
git and sending us pull requests.

For development GN2 has a room on matrix. Ask us for an invitation.

## Installing development snapshots with Guix

The Genenetwork repository can be used as a Guix “channel”.  To do that, change
~/.config/guix/channels.scm along these lines:

  (append (list (channel
                 (name 'genenetwork2)
                 (url "https://github.com/genenetwork/genenetwork2.git")))
   %default-channels)

  Once that is done, run ‘guix pull’.  This will give you additional ‘genenetwork2’
  packages with higher version numbers:

    guix package -A genenetwork2

    You can then install it with ‘guix install genenetwork2’ or similar.

## License

The GeneNetwork2 source code is released under the Affero General
Public License 3 (AGPLv3). See [LICENSE.txt](LICENSE.txt).


## More information

For more information visit https://genenetwork.org/

## Cite

[![JOSS](http://joss.theoj.org/papers/10.21105/joss.00025/status.svg)](http://joss.theoj.org/papers/10.21105/joss.00025)

GeneNetwork was published in the Journal of Open Source Software as 'GeneNetwork: framework for web-based genetics' by Zachary Sloan, Danny Arends, Karl W. Broman, Arthur Centeno, Nicholas Furlotte, Harm Nijveen, Lei Yan, Xiang Zhou, Robert W. WIlliams and Pjotr Prins

## Contact

E-mail: pjotr.public729@thebird.nl

Code and primary web service managed by Drs. Robert W. Williams and Pjotr Prins at the University of Tennessee Health Science Center, Memphis TN, USA.
