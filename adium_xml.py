# Utility functions for processing Adium XML-based log files

import logging
import dateutil.parser
import lxml.etree as ET


def tohtml(dom, xslt):
    """Convert an Adium XML log (.chatlog) to HTML via an XSL transform.  Returns HTML string."""
    # See http://stackoverflow.com/questions/16698935/how-to-transform-an-xml-file-using-xslt-in-python
    transform = ET.XSLT(xslt)
    html_dom = transform(dom)
    ht = ET.tostring(html_dom, pretty_print='True')  # at this point we have well-formed HTML
    return ht


def getdom(fi):
    """Parse the input file and return a DOM object."""
    return ET.parse(fi)


def getdate(dom):
    """Parse XML log and determine date.  Returns a datetime object."""

    # Determine log time
    if len(dom.xpath('//@time')) == 0:
        raise ValueError("Log does not appear to contain any timestamps!")

    times = dom.xpath('//@time')  # should return a list
    try:
        # We can't use datetime.datetime.strptime() here due to timezone, have to use dateutil
        d = dateutil.parser.parse(times[-1])
    except ValueError:
        # if last time won't parse, try the one before that, then give up
        d = dateutil.parser.parse(times[-2])

    return d


def getaccount(dom):
    """Determine IM account used for 'From' field (local end of log)"""
    if len(dom.xpath('//@account')) == 0:
        raise ValueError("Log does not appear to contain an 'account' element!")
    return dom.xpath('//@account')[0]


def getservice(dom):
    """Determine IM service (AIM, MSN, etc.)"""
    if len(dom.xpath('//@service')) == 0:
        raise ValueError("Log does not appear to contain an 'account' element!")
    return dom.xpath('//@service')[0]


def getparticipants(dom):
    """Determine participants in conversation.  Returns a list."""
    if len(dom.xpath('//@sender')) == 0:
        raise ValueError("Log does not appear to contain any 'sender' elements!")
    participants = []
    for a in dom.xpath('//@sender'):
        if a not in participants:
            logging.debug('Found new participant:' + a)
            participants.append(a)
    return participants
