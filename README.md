# adiumtoeml

Conversion tool to migrate Adium chat logs to RFC822 .eml files for archiving.

## Usage

From within the adiumtoeml directory:   
`$ ./adiumToEml.py chatlogfile [outputdir]`

If `outputdir` is not specified, the working directory will be used instead.

In most cases, you would probably want to call this from a wrapper script, e.g. with `find` and `xargs` in order to run it on a bunch of logfiles.

Most Adium logs end in either `.AdiumHTMLLog` or `.chatlog`, although the tool will also process files ending in `.html` or `.xml`, in case you want to edit either type of file by hand in an external editor.

Requires Python 3 and both the "dateutil" package, available through pip.

Written and tested using Python 3.7.1.

### Required Libraries / Packages

A few packages not included in Python's standard library are required for operation, and can be installed using `pip`.
These are:

* `pytz` - timezone handling support
* `py-dateutil` - extensions to the python `datetime` module, including timezone-aware date parsing

### Options

TBD

## Licensing

See the LICENSE file for more information.

Released under the GPL v2 or later. Contains various components licensed under the GPL and MIT licenses.

Modifications and improvements are welcomed and encouraged.  Please feel free to fork this project; pull requests will be considered as long as they do not break core functionality.

This software is provided without warranty and without any representations as to its functionality for a particular purpose.  End-user support is not available. 
