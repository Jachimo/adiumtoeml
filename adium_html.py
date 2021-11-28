# Utility functions for processing old Adium HTML-based log files

import logging
import datetime
import os

import conversation


doctype = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\n'


def toconv(fi, header, footer):
    """Convert old-style .AdiumHTMLLog file to a Conversation object

    header and footer are files containing the pre-<body> and post-<body> sections of HTML document
    """
    conv = conversation.Conversation()

    filename = os.path.basename(fi.name)  # Determine basename of input file from file object
    conv.origfilename = filename  # Set it on the Conversation object for future reference

    # Parse the first line of the input file for start date
    conv.startdate = getdate(fi.readline(), filename)  # Only start date is set

    participants = getparticipants(fi)
    for p in participants:
        conv.add_participant(p.strip())

    # THE OLD WAY: Generate a complete HTML document by slamming all the parts together
    #conv.html = doctype + header.read() + fi.seek(0).read() + footer.read() + '\n'

    # THE NEW WAY: Actually step through lines and generate Message objects
    fi.seek(0)
    for line in fi:
        if 'class="receive"' in line:  # probably a received message
            msg = conversation.Message('message')  # Create Message object
            logtime = line[line.find('<span class="timestamp">') + 24: line.find('</span>')]  # note this is time ONLY
            msg.date = makemsgtimefromlogtime(logtime, conv.startdate)  # create datetime object for message
            msg.msgfrom = line[line.find('<span class="sender">') + 21: line.find(': </span>')]
        if 'class="send"' in line:  # probably a transmitted message
            msg = conversation.Message('message')
            logtime = line[line.find('<span class="timestamp">') + 24: line.find('</span>')]
            msg.date = makemsgtimefromlogtime(logtime, conv.startdate)
            msg.msgfrom = line[line.find('<span class="sender">') + 21: line.find(': </span>')]
        if 'class="status"' in line:  # probably a status message
            msg = conversation.Message('event')
            logtime = line[line.find(' (') + 2: line.find(')</div>')]  # Status msgs use different timestamp format
            msg.date = makemsgtimefromlogtime(logtime, conv.startdate)
            msg.msgfrom = 'System Message'


def makemsgtimefromlogtime(logtime, convdateobj):
    """Take a time-only string (like '12:01:48 AM') and combine with date from conv.startdate to produce datetime"""
    # TODO may not handle logs that cross midnight very well, check and correct; maybe timedelta needed?
    time = datetime.datetime.strptime(logtime, '%I:%M:%S %p')  # format is usually '12:01:48 AM'
    dt = datetime.datetime.combine(convdateobj.date(), time.time())
    return dt


def getdate(line, filename):
    """Determine the date and time of an old-style Adium log, using a single
    line (typically the first), and the filename.
    """
    # Date we can determine from the log file's filename
    logdate = filename[filename.find("(") + 1: filename.find(")")]
    logging.debug("Log date appears to be " + logdate)

    # We must determine time from inside the log
    if '<span class="timestamp">' in line:
        logtime = line[line.find('<span class="timestamp">') + 24: line.find('</span>')]
    if '<div class="status">' in line:
        logtime = line[line.find(' (') + 2: line.find(')</div>')]
    logging.debug("Logtime appears to be " + logtime)

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


def getparticipants(fi):
    """Determine the participants in an old-style Adium HTML log, using the log
    as a file object, and return a list of strings.
    """
    participants = []
    fi.seek(0)  # make sure we are at the beginning of the file

    for line in fi:
        if '<div class="receive">' in line:
            participants.append(line[line.find('<span class="sender">') + 21: line.find(': </span>')])
        if '<div class="send">' in line:
            participants.append(line[line.find('<span class="sender">') + 21: line.find(': </span>')])
    return participants
