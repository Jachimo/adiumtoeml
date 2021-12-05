# XML Conversion Extras

This directory contains some optional "extras" related to converting Adium's XML log format to HTML.
They were originally found on the now-defunct Adium Trac site (formerly hosted at `http://trac.adium.im`).

Earlier versions (pre-2.0.0) of the adiumtoeml converter used a slightly-modified version of the included XSL file to transform the XML logs to HTML in a single operation.
While fast, this was not as flexible as desired, and it was dropped during the Python3 rewrite in 2021.

The XSL file, a CSS file it includes in its output, and a shell script to process `.chatlog` files are included in case they are useful to someone in the future.
They were distributed (and are being redistributed here) under version 2 or later of the GNU GPL.
