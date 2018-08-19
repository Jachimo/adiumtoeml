# adiumtoeml

Conversion utility to migrate Adium chat logs to RFC822 .eml files for archiving.

Based on SVN version `r1034 | 2014-12-31 03:15:45 -0500 (Wed, 31 Dec 2014)` with minor updates before uploading to Github.  Further updates are not expected unless contributed by the community, as I am (sadly) no longer using Adium regularly. 

## adiumToEml.py Description

Converts Adium logs to RFC822-compliant '.eml' files that can be imported into a mail program, uploaded to Gmail, etc.

Usage: 
`$ ./adiumToEml.py logfile [outputdir]`

If `outputdir` is not specified, the working directory will be used instead.

In most cases, you would probably want to call this from a wrapper script, e.g. with `find` and `xargs` in order to run it on a bunch of logfiles.  A sample wrapper script is provided in the `/samples` directory.

For old-style (`.AdiumHTMLLog`) files, working directory must contain a header and footer file, "header.htmlpart" and "footer.htmlpart", which are prepended and appended to the log in order to make it into a complete HTML document.

For XML logs produced by newer versions of Adium, working directory must contain an XSL file used to convertfrom XML to HTML, which should be named "chatlog_transform.xsl".

Requires Python 2.5 (but <3.0) or later and both the "lxml" and "dateutil" packages, available through pip.

### Options

There are several options which can be set in the source code; see lines 49-57 in `adiumToEml.py`. These include an optional override of programmatic determination of the system hostname from its FQDN (useful on systems where this is not possible, or if you are processing logs on a system other than where they were created, so the hostname would be wrong); a manual path to look for the header and footer HTML files, if you don't have them in the working dir; a default "TO" address, in case one cannot be determined from a particular log file; and perhaps most importantly, a `skipIfBeforeDate` option, which prevents processing of log files if their date is prior to a specified date.

This last option is very handy if you are using Adium regularly, and want to update the converted logs without creating duplicates of ones already converted. 

### Debugging

A debug flag can be set on line 43 of `adiumToEml.py` which will enable very verbose output.  It may be helpful when trying to diagnose problems or odd behavior.

## Licensing

See the LICENSE file for more information.

Released under the GPL v2 or later. Contains various components licensed under the GPL.

Modifications and improvements are welcomed and encouraged.  Please feel free to fork this project; pull requests will be considered as long as they do not break core functionality.

This software is provided without warranty and without any representations as to its functionality for a particular purpose.  End-user support is not available. 
