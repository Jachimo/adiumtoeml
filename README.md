# adiumtoeml

Conversion tool to migrate Adium chat logs to RFC822 .eml files for archiving.

## Usage

From within the adiumtoeml directory:   
`$ ./adiumToEml.py chatlogfile [outputdir]`

If `outputdir` is not specified, the working directory will be used instead.

In most cases, you probably want to call this from a wrapper script, e.g. with `find` and `xargs` in order to run it on the entire Adium Logs directory.
(Usually `~/Documents/Adium/Logs` or potentially also `~/Library/Application Support/Adium/Logs`, but could be placed elsewhere.)

Most Adium logs end in either `.AdiumHTMLLog` or `.chatlog`, although the tool will also process files ending in `.html` or `.xml`.

Written and tested using Python 3.9.

### Required Libraries / Packages

A few packages not included in Python's standard library are required for operation, and can be installed using `pip`.
These are:

* `pytz` - timezone handling support
* `py-dateutil` - extensions to the python `datetime` module, including timezone-aware date parsing

### Other Options

The most up-to-date usage options can be listed by running `./adiumToEml.py -h`.
It is included here for reference:
```
usage: adiumToEml.py [-h] [--clobber] [--no-background] infilename [outdirname]

Convert Adium log files to RFC822 MIME text files (.eml)

positional arguments:
  infilename       Input file
  outdirname       Output directory (optional, defaults to cwd)

optional arguments:
  -h, --help       show this help message and exit
  --clobber        Overwrite identically-named output files
  --no-background  Strips background color from message text
```

## Known Bugs / Limitations

### Facebook Chat Logs

Adium logs of Facebook chat conversations (from the period when Facebook was using an open standards, XMPP-compatible chat service) seem to be frequently malformed.
Although the tool attempts to link Facebook user IDs to real names (stored as 'aliases' in the XML), this is only occasionally possible.
Also, some logs appear to only contain one side (usually the remote) of the conversation, for reasons that are not clear.

A possible cause is related to how Facebook handled multiple-device support: received messages were likely 'broadcast' to all signed-in devices, but transmitted messages from a device other than the computer running Adium were not re-sent out by Facebook's servers, and thus are not included in the Adium log.

### Malformed XML

It appears that some versions of Adium produced malformed XML log files.
Missing `</chat>` tags are particularly common in some periods (most are dated around early 2003, and the issue was apparently fixed by mid-2004).

### Bad Log File Names

Examples have been found of Adium HTML-based log files with strange separator characters in the date written into the filename.
(An example is `20050219` on an AdiumHTMLLog file.)
These files will cause processing errors and should be renamed by hand, replacing the non-ASCII chars with dashes.

## Licensing

See the LICENSE file for more information.

Released under the GPL v2 or later. Contains various components licensed under the GPL and MIT licenses.

Modifications and improvements are welcomed and encouraged.
Please feel free to fork this project; pull requests will be considered as long as they do not break core functionality.

This software is provided without warranty and without any representations as to its functionality for a particular purpose.
End-user support is not available. 

## Errata

#### Adium Log Formats

Adium used a variety of filename schemes for its logs over the years.
Early versions of Adium wrote `.AdiumHTMLLog` files, which contained the messages as HTML tag contents.  Occasionally, logs with an `.html` extension are seen.
Later versions used XML, either written directly to `.chatlog` files, or sometimes written to an `.xml` file hidden inside a `.chatlog` directory (which was made to appear as a file-like Package object on Mac OS X).
This tool _should_ be able to parse most of them, provided they are well-formed.
