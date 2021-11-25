#!/usr/bin/env python3

""" Convert Adium logs to RFC822-compliant '.eml' files

    For usage, run with the -h option.
"""


import sys
import logging
import datetime
import os
import argparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pytz
import hashlib

import adium_xml
import adium_html


localtz: str = 'America/New_York'


def main():
    logging.basicConfig(level=logging.DEBUG)  # change level for desired verbosity: DEBUG, INFO, WARNING, ERROR, etc.

    # Parse arguments (see https://docs.python.org/3/library/argparse.html)
    parser = argparse.ArgumentParser(description='Convert Adium log files to RFC822 MIME text files (.eml)')
    parser.add_argument('infilename', help='Input file')
    parser.add_argument('outdirname', nargs='?', default=os.getcwd(), help='Output directory (optional, defaults to cwd)')
    parser.add_argument('--clobber', action='store_true', help='Overwrite identically-named output files')
    parser.add_argument('--configdir', help='Location of support files')
    parser.add_argument('--xslfile', help='Name of XSL file to use for transform (within config dir)')
    args = parser.parse_args()

    logging.debug('Input file path is ' + args.infilename)

    if not args.infilename:
        logging.critical("No input file specified.")
        return 1
    if not os.path.isfile(args.infilename):
        logging.critical("Input must be a file.")
        return 1
    if os.path.splitext(args.infilename)[-1] not in ['.chatlog', '.xml', '.AdiumHTMLLog', '.html']:
        logging.critical("Input file suffix not one of the supported types.")
        return 1
    
    logging.debug("Output dir is " + args.outdirname)
    
    if not os.path.isdir(args.outdirname):
        logging.critical("Output dir (" + args.outdirname + ") specified but not a directory.")
        return 1

    outfilename = os.path.splitext(os.path.basename(args.infilename))[0] + '.eml'  # .mht or .mhtml also valid
    outpath = os.path.join(args.outdirname, outfilename)
    
    # Test to see if a file already exists with that name
    # In some cases this may be undesirable/annoying so we can disable with flag --clobber
    if os.path.isfile(outpath):
        if not args.clobber:
            logging.critical("Output file " + outpath + " already exists. Use --clobber to overwrite.")
            return 1
        else:
            logging.warning('Output file ' + outpath + ' exists and will be overwritten.')

    # Ensure XSL file can be read
    if not args.configdir:
        args.configdir = os.path.dirname(os.path.abspath(sys.argv[0]))
    if args.xslfile:
        logging.info('XSL transform file set to: ' + args.xslfile)
        xslpath = os.path.join(args.configdir, args.xslfile)
    else:
        xslpath = os.path.join(args.configdir, 'chatlog_transform.xsl')

    # Open input file
    try:
        fi = open(args.infilename, 'r')   # fi is a file object
        logging.debug('Opened ' + args.infilename + ' for reading.')
    except IOError:
        logging.critical("I/O Error while opening input: " + args.infilename)
        return 1

    # Create a conversation object
    conv = {}
    conv['service'] = ''
    conv['participants'] = []
    conv['html'] = ''
    
    # Newer XML-based logs can be transformed into HTML (See https://trac.adium.im/wiki/XMLLogFormat)
    if os.path.splitext(args.infilename)[-1] == '.chatlog':
        logging.debug('XML chat log detected based on file extension.')

        try:
            xslf = open(xslpath, 'r')
        except IOError:
            logging.critical('Cannot open: ' + xslpath)
            return 1

        dom = adium_xml.getdom(fi)
        xslt = adium_xml.getdom(xslf)
        conv['html'] = adium_xml.tohtml(dom, xslt).decode('us-ascii')

        conv['participants'] = adium_xml.getparticipants(dom)
        if len(conv['participants']) < 2:  # need at least 2 participants to construct headers
            conv['participants'].append('UNKNOWN')

        conv['dateobj'] = adium_xml.getdate(dom)

        conv['service'] = adium_xml.getservice(dom)

    # For old style fragementary-HTML Adium logs...
    if os.path.splitext(args.infilename)[-1] == '.AdiumHTMLLog':
        logging.debug('HTML chat log detected based on file extension.')

        try:
            header = open( os.path.join(args.configdir, 'header.htmlpart'), 'r')
            footer = open( os.path.join(args.configdir, 'footer.htmlpart'), 'r')
        except IOError:
            logging.critical('I/O Error while attempting to open header or footer file.')
            return 1
        
        # Parse the first line of the input file
        conv['dateobj'] = adium_html.getdate( fi.readline(), msg_base, args.infilename ) # Only date is set
        conv['participants'] = adium_html.getparticipants(fi)
        
        doctype = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\n'
        fi.seek(0)  # make sure we don't leave off the first line...
        conv['html'] = doctype + header.read() + fi.read() + footer.read() + '\n'  # construct message using static header/footer files

    fi.close()  # close input file, we are now done with it

    # Create a fake domain-like string for constructing URL-like identifiers such as Message-ID
    fakedomain = conv['service'].lower() + '.adium.invalid'

    # Create a base message object of type multipart/mixed
    msg_base = MIMEMultipart('mixed')

    # Set From and To using the participants list
    msg_base['From'] = ('"' + conv['participants'][0] + '" '
                        + '<' + conv['participants'][0] + '@' + fakedomain + '>')
    msg_base['To'] = ('"' + conv['participants'][1] + '" '
                      + '<' + conv['participants'][1] + '@' + fakedomain + '>')

    global localtz
    tz = pytz.timezone(localtz)
    msg_base['Date'] = conv['dateobj'].astimezone(tz).strftime('%a, %d %b %Y %T %z')  # RFC2822 format

    # Construct the Subject line from the file name, but cleaned up slightly
    msg_base['Subject'] = ('Chat with ' + args.infilename.split(' (')[0] + ' on '
                       + args.infilename[args.infilename.find("(") + 1: args.infilename.find(")")])

    # Create the message body...
    msghtml = MIMEText(conv['html'], 'html')

    msg_base['References'] = ('<' + hashlib.md5(
        ' '.join(sorted(conv['participants'])).lower().encode('utf-8')).hexdigest() + '@' + fakedomain + '>')

    # Create unique Message-ID by hashing the content (allows for duplicate detection)
    msg_base['Message-ID'] = ('<' + hashlib.md5(
        (msg_base['Date'] + msg_base['Subject'] + conv['html']).encode('utf-8')).hexdigest() + '@' + fakedomain + '>')

    # Set additional headers (comment out if not desired)
    msg_base['X-Converted-By'] = sys.argv[0].lstrip('./')
    msg_base['X-Converted-On'] = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S" + " -0500 (EST)")  # TODO fix tz
    
    # Attach the HTML to the root
    msg_base.attach(msghtml)
    
    logging.debug("Ready to flatten and write message...")

    try:
        fo = open(outpath, 'w')
        logging.debug('Opened ' + outpath + ' for writing.')
    except IOError:
        logging.critical("I/O Error while opening output: " + outpath)
        return 1

    # Write out the message
    fo.write( msg_base.as_string() )
    
    logging.debug('Finished writing ' + outpath)
    
    logging.info(args.infilename + '\t' + msg_base['Message-ID'])
    
    fo.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
