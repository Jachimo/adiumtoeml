# adiumtoeml

Conversion utility to migrate Adium chat logs to RFC822 .eml files for archiving.

## adiumToEml.py Description

Converts Adium logs to RFC822-compliant '.eml' files that can be imported into a mail program, uploaded to Gmail, etc.

Usage: 
`$ ./adiumToEml.py logfile [outputdir]`

If `outputdir` is not specified, the working directory will be used instead.

In most cases, you would probably want to call this from a wrapper script, e.g. with `find` and `xargs` in order to run it on a bunch of logfiles.

Requires Python 3 and both the "dateutil" package, available through pip.

Written and tested using Python 3.7.1.

### Options

TBD

## Licensing

See the LICENSE file for more information.

Released under the GPL v2 or later. Contains various components licensed under the GPL.

Modifications and improvements are welcomed and encouraged.  Please feel free to fork this project; pull requests will be considered as long as they do not break core functionality.

This software is provided without warranty and without any representations as to its functionality for a particular purpose.  End-user support is not available. 
