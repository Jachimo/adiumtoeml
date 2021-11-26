# Utility functions for processing old Adium HTML-based log files

import logging
import datetime

import conversation


def getdate(line, msg_base, filename):
    """Determine the date and time of an old-style Adium log, using a single
    line (typically the first), and the filename, and set appropriate headers
    in the message object.
    """
    # Date we can determine from the log file's filename
    logdate = filename[ filename.find("(" ) +1 : filename.find(")") ]
    logging.debug("-- Log date appears to be " + logdate)

    # We must determine time from inside the log
    if '<span class="timestamp">' in line:
        logtime = line[ line.find('<span class="timestamp">' ) +24 : line.find('</span>') ]
    if '<div class="status">' in line:
        logtime = line[ line.find(' (' ) +2 : line.find(')</div>') ]
    logging.debug("-- Logtime appears to be " + logtime)
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
    return d


def getparticipants( fi ):
    """Determine the participants in an old-style Adium HTML log, using the log
    as a file object, and return a list of strings.
    """
    local = None
    remote = None
    fi.seek(0)  # make sure we are at the beginning of the file
    while (msgfrom is None) or (msgto is None):
        line = fi.readline()
        if not line:
            break # break loop at EOF
        if '<div class="receive">' in line:
            remote = line[ line.find('<span class="sender">' ) +21 : line.find(': </span>') ]
            logging.debug("-- From username is " + remote)
        if '<div class="send">' in line:
            local = line[ line.find('<span class="sender">' ) +21 : line.find(': </span>') ]
            logging.debug("-- To username is " + local)
    logging.debug("-- Loop complete")
    return [local, remote]


def determineHTMLLogHeaders(firstline, msg_base):
    """Process Pidgin/libpurple style HTML logs, which are complete HTML documents
    beginning with a title element containing header information about the chat.
    This is not used for Adium logs.  Left in for future use.

    Returns a date object which is the time of the log, for filtering purposes.
    """
    title = firstline[firstline.find("<title>" ) +7:firstline.find("</title>")]

    logging.debug("<title>: " + title)

    # Determine the 'From' address of the chat
    #  TODO: This might be better done with a regexp?
    logfrom = title[title.find("Conversation with " ) +18:title.find(" at ")]

    logging.debug("-- From is: " + msg_base['From'])

    # Determine the 'To' address
    logto = title[title.find(" on " ) +4:]

    logging.debug("-- To is: " + msg_base['To'])

    # Now we have to deal with the date.  This is messy.
    logdate = title[title.find(" at " ) +4:title.find(" on ")]
    # Turn it into a datetime object
    logdateobj = datetime.datetime.strptime(logdate, '%m/%d/%Y %I:%M:%S %p')

    # And the message subject
    logsubj = title[0:title.find(" on ")]

    return (logfrom, logto, logdateobj, logsubj)
