# XML Conversion Extras

This directory contains some "extras" related to Adium log conversion.

## fix_xml_close.sh

This is a small shell script designed to repair Adium XML logs that have a malformed `</chat>` tag.

During testing, I found that some log files produced during a very specific date range (probably a single point-release of Adium) had `</?xml>` tags where they should have `</chat>` tags, which will cause minidom to error.  Depending on when you used Adium, you may or may not encounter logs like this.

The script takes as input a file containing a list of log files (such as the "failed_YYYY-MM-DD.log" file emitted by adiumToEml) and performs a find/replace on each of them to fix the malformed tag.

## format-html

This is a script and XML stylesheet written by Adium contributor "neil_mayhew" and originally posted to the official Adium bug tracker [as part of a feature request for a 'Save As' option in the Log Viewer](http://web.archive.org/web/20150919140152/https://trac.adium.im/ticket/6569).
It provides direct XML-to-HTML conversion for Adium .chatlog files, which is a particularly elegant solution if your goal is simply to have a human-readable version of your logs.  It is noted as being released under GPLv2.

## parsers

The parsers directory contains sample code for parsing Adium's XML log format using lxml or minidom.  Note that the lxml version seems to have issues with correctly parsing text nested near HTML tags inside message payloads; this can be demonstrated using the included "xmlbug" chatlog file.