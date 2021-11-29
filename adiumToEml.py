#!/usr/bin/env python3

""" Convert Adium logs to RFC822-compliant '.eml' files

    For usage, run with the -h option.
"""


import sys
import logging
import os
import argparse

import conversation  # data model
import adium_xml  # for newer XML based .chatlog files
import adium_html  # for older HTML based .AdiumHTMLLog files
import conv_to_eml  # for output as MIME .eml file/message


def main() -> int:
    logging.basicConfig(level=logging.DEBUG)  # change level for desired verbosity: DEBUG, INFO, WARNING, ERROR, etc.

    # Parse arguments (see https://docs.python.org/3/library/argparse.html)
    parser = argparse.ArgumentParser(description='Convert Adium log files to RFC822 MIME text files (.eml)')
    parser.add_argument('infilename', help='Input file')
    parser.add_argument('outdirname', nargs='?', default=os.getcwd(), help='Output directory (optional, defaults to cwd)')
    parser.add_argument('--clobber', action='store_true', help='Overwrite identically-named output files')
    parser.add_argument('--configdir', help='Location of support files')
    parser.add_argument('--xslfile', help='Name of XSL file to use for transform (within config dir)')
    args = parser.parse_args()

    if not args.infilename:
        logging.critical("No input file specified.")
        return 1
    if not os.path.isfile(args.infilename):
        logging.critical("Input must be a file.")
        return 1
    if os.path.splitext(args.infilename)[-1] not in ['.chatlog', '.xml', '.AdiumHTMLLog', '.html']:
        logging.critical("Input file suffix not one of the supported types.")
        return 1
    if not os.path.isdir(args.outdirname):
        logging.critical("Output dir (" + args.outdirname + ") specified but not a directory.")
        return 1

    outfilename = os.path.splitext(os.path.basename(args.infilename))[0] + '.eml'  # .mht or .mhtml also valid
    outpath = os.path.join(args.outdirname, outfilename)
    
    # Test to see if a file already exists with that name and stop if so
    # In some cases this may be undesirable/annoying so we can disable with flag --clobber
    if os.path.isfile(outpath):
        if not args.clobber:
            logging.critical("Output file " + outpath + " already exists. Use --clobber to overwrite.")
            return 1
        else:
            logging.warning('File ' + outpath + ' exists and will be overwritten.')

    # Open input file
    try:
        fi = open(args.infilename, 'r')   # fi is a file object
        logging.debug('Opened ' + args.infilename + ' for reading.')
    except IOError:
        logging.critical("I/O Error while opening input: " + args.infilename)
        return 1
    
    # Newer Adium logs are XML
    if os.path.splitext(args.infilename)[-1] in ['.chatlog', '.xml']:
        logging.debug('XML chat log detected based on file extension.')
        conv = adium_xml.toconv(fi)

    # Older logs are HTML "tag soup" (basically just HTML <body> contents), 1 msg per line
    if os.path.splitext(args.infilename)[-1] in ['.AdiumHTMLLog', '.html']:
        logging.debug('HTML chat log detected based on file extension.')
        conv = adium_html.toconv(fi)

    fi.close()  # close input file, we are now done with it

    eml = conv_to_eml.mimefromconv(conv)  # produce MIME message from Conversation (and any attachments)

    # Set additional headers (comment out if not desired)
    eml['X-Converted-By'] = sys.argv[0].lstrip('./')

    logging.debug("Ready to flatten and write message...")
    try:
        fo = open(outpath, 'w')
        logging.debug('Opened ' + outpath + ' for writing.')
    except IOError:
        logging.critical("I/O Error while opening output: " + outpath)
        return 1
    fo.write(eml.as_string())  # Write out the message
    logging.debug('Finished writing ' + outpath)
    fo.close()
    print(args.infilename + '\t' + eml['Message-ID'] + '\x1e')  # fuck 'em if they can't take a joke

    return 0  # exit successfully


if __name__ == "__main__":
    sys.exit(main())
