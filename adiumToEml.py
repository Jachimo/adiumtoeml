#!/usr/bin/env python

"""Convert Adium logs to RFC822-compliant '.eml' files that can be imported 
into a mail program, uploaded to Gmail, etc.

Usage: 
$ ./adiumToEml.py logfile [outputdir]

In most cases, you would probably want to call this from a script, e.g.
with `find` and `xargs` in order to run it on a bunch of logfiles.

For old-style (.AdiumHTMLLog) files, working directory must contain a header
and footer file, "header.htmlpart" and "footer.htmlpart", which are prepended
and appended to the log in order to make it into a complete HTML document.

For XML logs produced by newer versions of Adium, working directory must 
contain an XSL file used to convertfrom XML to HTML, which should be named
"chatlog_transform.xsl".

Requires Python 2.5 (but <3.0) or later and both the "lxml" and "dateutil" 
packages, available through pip.

Released under the GPL v2 or later.
"""

# These libs are pretty critical
import sys
import datetime
import os.path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# These are needed for new XML-formatted ".chatlog" but not old ".AdiumHTMLLog"
import lxml.etree       # NOT STANDARD LIBRARY, MUST INSTALL
import dateutil.parser  # NOT STANDARD LIBRARY, MUST INSTALL 

# These are for Message-ID functionality and can be easily disabled
import uuid
import socket

# RUNTIME FLAGS
global debug  # Debug, if true, produces very verbose output
debug = False
global silent  # If true, suppresses all stdout output
silent = False  
global haltOnDuplicates  # If true, throw error if output file exists already
haltOnDuplicates = False

# CONFIG OPTIONS
global configFilePath
configFilePath = ''  # empty string means working dir, for header/footer files
global myhostname
myhostname = ''  # set to false/null to determine programmatically from system FQDN
global defaultToAddr
defaultToAddr = "Tester John Doe <jdoe@myhostname.example>"  # use this as the email 'To' header if we can't determine from the log
global skipIfBeforeDate
skipIfBeforeDate = '' # skip log if date is earlier than %Y-%m-%dT%H:%M:%S%z, e.g. 2006-07-14T12:42:01-0500

def main():
    global myhostname 
    
    # Use the first argument as the input file
    global filename
    try:
        if sys.argv[1]:
            filename = sys.argv[1]
    except IndexError:
        sys.stderr.write("No input file specified. Terminating.\n")
        return 1
    else:
        if os.path.isfile(filename) is not True:
            sys.stderr.write("Input file (" + filename + ") appears invalid. Terminating.\n")
            return 1
    
    if debug:
        sys.stderr.write("output dir is " + sys.argv[2] + '\n')
    
    # Second arg, if present, is the output dir
    try:
        outputdir = sys.argv[2]  # Note that this will throw IndexError if not specified
    except IndexError:
        # which we catch here and fix by setting to zero-length string, i.e. the working directory
        outputdir = ''
    else:
        if os.path.isdir(outputdir) is not True:
            sys.stderr.write("Output dir (" + outputdir + ") specified but not a directory. Terminating.\n")
            return 1
    
    # output file name is based on input; we take the input basename, append .eml, then prefix the output dir
    outfilename = os.path.basename(filename) + '.eml'
    outpath = os.path.join(outputdir, outfilename)
    
    # DEBUG
    if debug:
        print "-- Reading from " + filename
        print "-- Writing to " + outpath
    
    # Test to see if the output file already exists (prevents duplicate processing)
    # In some cases this may be undesirable/annoying so we can disable with flag haltOnDuplicates
    if os.path.isfile(outpath) and haltOnDuplicates:
        sys.stderr.write("Output file " + outpath + " already exists. Terminating.\n")
        return 1
    
    # Test to make sure the file suffix is one of the types we can process
    if filename.split('.')[-1] not in ['xml', 'AdiumHTMLLog']:
        sys.stderr.write("Input file suffix not one of supported types.  Terminating.\n")
        return 1
    
    # Open the in and out files
    try:
        fi = open(filename, 'r')   # fi is a file object
    except IOError:
        sys.stderr.write("I/O Error while opening input: " + filename + "\n")
        return 1
    
    try:
        fo = open(outpath, 'w')
    except IOError:
        sys.stderr.write("I/O Error while opening output: " + outpath + "\n")
        return 1
    
    # Create a message object
    msg_base = MIMEMultipart('mixed')
    
    # For new XML-based Adium logs (have to be run through a XML transform)
    # Ref. <https://trac.adium.im/wiki/XMLLogFormat>
    if filename.split('.')[-1] == 'xml':
        # TODO Adium XML logs should always be contained in directories with the same basename but extension '.chatlog'
        #  MacOS treats these directories like 'packages' which might or might not cause issues...
        try:
            xslt = lxml.etree.parse( os.path.join(configFilePath, 'chatlog_transform.xsl') )
        except IOError:
            sys.stderr.write("I/O Error while attempting to open " + os.path.join(configFilePath, 'chatlog_transform.xsl') + '\n')
            return 1
        
        # Use lxml to transform XML (TODO: might want to put this in a function...)
        # See <http://stackoverflow.com/questions/16698935/how-to-transform-an-xml-file-using-xslt-in-python>
        dom = lxml.etree.parse(fi)
        transform = lxml.etree.XSLT(xslt)
        html_dom = transform(dom)
        ht = lxml.etree.tostring(html_dom, pretty_print='True') # at this point we have well-formed HTML
        
        try:
            d = determineAdiumXMLHeaders( filename, fi, dom, msg_base )
        except:
            sys.stderr.write("Error while determining headers of " + filename + "\n")
            raise
    
    # For old style fragementary-HTML Adium logs...
    if filename.split('.')[-1] == 'AdiumHTMLLog':
        try:
            header = open( os.path.join(configFilePath, 'header.htmlpart'), 'r')
            footer = open( os.path.join(configFilePath, 'footer.htmlpart'), 'r')
        except IOError:
            sys.stderr.write('I/O Error while attempting to open header or footer file.\nBe sure both header.htmlpart and footer.htmlpart exist in the working dir.\n')
            return 1
        
        # Parse the first line of the input file
        fi.seek(0)  # make sure we're really at the first line
        try:
            d = determineAdiumHTMLDateTime( fi.readline(), msg_base, filename ) # Only date is set
        except:
            sys.stderr.write('Error while determining date/time of ' + filename + '\n')
            raise
        
        try:
            determineAdiumHTMLToFrom( fi, msg_base ) # To and From headers
        except:
            sys.stderr.write('Error while determining to/from of ' + filename + '\n')
            raise
            
        msg_base['Subject'] = 'Chat with ' + msg_base['From'] + ' on ' + filename[ filename.find("(")+1 : filename.find(")") ]
        
        doctype = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\n'
        fi.seek(0)  # make sure we don't leave off the first line...
        ht = doctype + header.read() + fi.read() + footer.read() + '\n'  # construct message using static header/footer files
    
    # See if we should process the message based on date filter
    if skipIfBeforeDate:
        if debug:
            print "Date filtering enabled, cutoff date is " + skipIfBeforeDate
        try:
            dcutoff = dateutil.parser.parse(skipIfBeforeDate)
        except:
            sys.stderr.out("Error while parsing cutoff date configuration parameter.\n")
            raise
        if d < dcutoff:
            if not silent:
                sys.stderr.write("File " + filename + " skipped due to skipIfBeforeDate constraint.\n")
            return 0  # skip the file and stop processing with normal exit
    
    # Create the message body...
    msghtml = MIMEText(ht, 'html')
    
    # determine system FQDN, but only if not specified above
    if myhostname == '':
        myhostname = socket.getfqdn()
    
    # Create message ID
    msguuid = uuid.uuid1()  # note this uses machine's MAC addr.  uuid.uuid4() is totally random if it matters
    msgid = str(msguuid) + '@' + myhostname  # this is per RFC822 and RFC2822
    msg_base['Message-ID'] = msgid
    
    # Set additional headers (comment out if not desired)
    msg_base['X-Converted-By'] = sys.argv[0].lstrip('./')
    msg_base['X-Converted-On'] = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S" + " -0500 (EST)")
    
    if debug:
        print "-- Headers are..."
        for key, value in msg_base.items():
            print key + ": " + value
    
    # Attach the HTML to the root
    msg_base.attach(msghtml)
    
    if debug:
        print "-- Ready to flatten and write message..."
    
    # Write out the message
    fo.write( msg_base.as_string() )
    
    if debug:
        print "-- Complete."
    if not silent:
        # If not in silent mode, write input filename and Message-ID to stdout
        # When run inside a wrapper script, we can use this to make a nice logfile
        print filename + '\t' + msgid
    
    fo.close()
    return 0


def determineAdiumXMLHeaders( filename, fi, dom, msg_base ):
    """Determine email headers for a new-style Adium XML .chatlog, using
    a combination of the file object (fi) and also the parsed DOM of the
    log itself.  Sets headers on msg_base, which is a MIMEMultipart object.
    
    Returns a datetime object which is the time of the log.
    
    Requires lxml.etree.
    """
    # If DOM is empty (not parsed yet), parse:
    if not dom:
        dom = lxml.etree.parse(fi)
    
    # Determine log time
    if len(dom.xpath('//@time')) == 0:
        raise ValueError("Log does not appear to contain any timestamps!")
        # TODO fall back to filename?
    times = dom.xpath('//@time')  # should return a list
    try:
        # We can't use datetime.datetime.strptime() here due to timezone, have to use dateutil
        d = dateutil.parser.parse(times[0])
    except ValueError:
        # if we get a malformed time, try next one in the log, then give up
        d = dateutil.parser.parse(times[1])
    # Then write it out to RFC822 format
    #  TODO: We assume we are always in EST, which is dumb but most MUAs convert.
    msg_base['Date'] = d.strftime("%a, %d %b %Y %H:%M:%S" + " -0500 (EST)")
    
    # Determine IM account used for 'From' field (local end of log)
    if len( dom.xpath('//@account') ) == 0:
        raise ValueError("Log does not appear to contain an 'account' element!")
    msg_base['From'] = dom.xpath('//@account')[0]
    
    # Determine IM account used for 'To' field (remote end of log)
    #  This doesn't seem to be recorded in the logs, have to use filename
    msg_base['To'] = os.path.basename(filename).split(' ')[0]
    
    return d


def determineAdiumHTMLDateTime(line, msg_base, filename):
    """Determine the date and time of an old-style Adium log, using a single
    line (typically the first), and the filename, and set appropriate headers
    in the message object.
    
    The global variable 'debug' enables debugging output, if True.
    """
    # Date we can determine from the log file's filename
    logdate = filename[ filename.find("(")+1 : filename.find(")") ]
    if debug:
        print "-- Log date appears to be " + logdate
    
    # We must determine time from inside the log
    if '<span class="timestamp">' in line:
        logtime = line[ line.find('<span class="timestamp">')+24 : line.find('</span>') ]
    if '<div class="status">' in line:
        logtime = line[ line.find(' (')+2 : line.find(')</div>') ]
    if debug:
        print "-- Logtime appears to be " + logtime
    # Turn it into a datetime object
    try:
        d = datetime.datetime.strptime(logdate + ' ' + logtime, '%Y-%m-%d %I:%M:%S %p')
    except ValueError:
        # if that date format (most common) doesn't work, try differently:
        try:
            d = datetime.datetime.strptime(logdate + ' ' + logtime, '%Y|%m|%d %H:%M:%S')
        except ValueError:
            # if that doesnt work either, try a 3rd time, this time without AM/PM flag
            d = datetime.datetime.strptime(logdate + ' ' + logtime, '%Y-%m-%d %H:%M:%S')
    # Then write it out to RFC822 format
    #  TODO: We assume we are always in EST, which is dumb.
    msg_base['Date'] = d.strftime("%a, %d %b %Y %H:%M:%S" + " -0500 (EST)")
    
    return d

def determineAdiumHTMLToFrom( fi, msg_base ):
    """Determine the To and From fields for an old-style Adium HTML log, using the log
    as a file object, and set appropriate headers in the message object.
    
    The global variable 'debug' enables debugging output, if True.
    """
    fi.seek(0)  # make sure we are at the beginning of the file
    msgfrom = None
    msgto = None
    
    while msgfrom is None or msgto is None:
        line = fi.readline()
        if not line:
            break # break loop at EOF
        if '<div class="receive">' in line:
            msgfrom = line[ line.find('<span class="sender">')+21 : line.find(': </span>') ]
            if debug:
                print "-- From username is " + msgfrom
        if '<div class="send">' in line:
            msgto = line[ line.find('<span class="sender">')+21 : line.find(': </span>') ]
            if debug:
                print "-- To username is " + msgto
        if debug:
            print "-- Loop complete"
    if not msgfrom:
        if debug:
            print "-- Could not determine FROM field using log contents, falling back to filename."
        msgfrom = os.path.basename(filename).split(' ')[0]
    if not msgto:
        if debug:
            print "-- Could not determine TO field using log contents, falling back to default."
        msgto = defaultToAddr
    if not msgfrom or not msgto:
        sys.stderr.write('Could not determine from or to field while processing ' + filename + '\n')
        return 1
    msg_base['From'] = msgfrom
    msg_base['To'] = msgto

def determineHTMLLogHeaders(firstline, msg_base):
    """Process Pidgin/libpurple style HTML logs, which are complete HTML documents
    beginning with a title element containing header information about the chat.
    This is not used for Adium logs.  Left in for future use.
    
    Returns a date object which is the time of the log, for filtering purposes.
    """
    title = firstline[firstline.find("<title>")+7:firstline.find("</title>")]
    
    if debug:
        print "<title>: " + title
    
    # Determine the 'From' address of the chat
    #  TODO: This would be better done with a regexp but I was lazy
    msg_base['From'] = title[title.find("Conversation with ")+18:title.find(" at ")]
    
    if debug:
        print "-- From is: " + msg_base['From']
    
    # Determine the 'To' address
    msg_base['To'] = title[title.find(" on ")+4:]
    
    if debug:
        print "-- To is: " + msg_base['To']
    
    # Now we have to deal with the date.  This is messy.
    logdate = title[title.find(" at ")+4:title.find(" on ")]
    # Turn it into a datetime object
    d = datetime.datetime.strptime(logdate, '%m/%d/%Y %I:%M:%S %p')
    # Then write it out to RFC822 format
    #  TODO: This is a naive/stupid way of handling timezone!
    msg_base['Date'] = d.strftime("%a, %d %b %Y %H:%M:%S" + " -0500 (EST)")
    
    # And the message subject
    msg_base['Subject'] = title[0:title.find(" on ")]
    
    return d


if __name__ == "__main__":
    sys.exit( main() )

