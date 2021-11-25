# adiumtoeml

Conversion utility to migrate Adium chat logs to RFC822 .eml files for archiving.

## adiumToEml.py Description

Converts Adium logs to RFC822-compliant '.eml' files that can be imported into a mail program, uploaded to Gmail, etc.

Usage: 
`$ ./adiumToEml.py logfile [outputdir]`

If `outputdir` is not specified, the working directory will be used instead.

In most cases, you would probably want to call this from a wrapper script, e.g. with `find` and `xargs` in order to run it on a bunch of logfiles.

For old-style (`.AdiumHTMLLog`) files, the directory containing the script must contain a header and footer file, "header.htmlpart" and "footer.htmlpart", which are prepended and appended to the log in order to make it into a complete HTML document.

For XML logs produced by newer versions of Adium, the directory containing the script must contain an XSL file used to convert from XML to HTML, which should be named "chatlog_transform.xsl".

Requires Python 3 and both the "lxml" and "dateutil" packages, available through pip.

### Options

TBD

## Licensing

See the LICENSE file for more information.

Released under the GPL v2 or later. Contains various components licensed under the GPL.

Modifications and improvements are welcomed and encouraged.  Please feel free to fork this project; pull requests will be considered as long as they do not break core functionality.

This software is provided without warranty and without any representations as to its functionality for a particular purpose.  End-user support is not available. 
