#!/usr/bin/env python3
# Utility functions for processing Adium XML-based log files

import sys
import logging
import dateutil.parser
import xml.etree.ElementTree as ET  # change from lxml to xml

import conversation


def toconv(infile):
    """Take a file-like input object and parse to produce a Conversation object"""
    conv = conversation.Conversation()  # instantiate Conversation object

    dom = ET.parse(infile)  # parse the input file and get back ElementTree
    logging.debug('Input parsed to: ' + str(dom))

    root = dom.getroot()  # get the root element, which should be <chat>
    logging.debug('Root element is: ' + str(root))

    xmlns = get_xmlns(root)  # Get the XML namespace, if there is one (usually is)
    logging.debug('XML Namespace is: ' + xmlns)

    conv.set_service(root.attrib['service'])  # set the service (AIM, MSN, etc.)
    logging.debug('IM service is ' + conv.service)

    for e in root.iter():  # iterate over all child elements of the root
        if e.tag == xmlns + 'event':  # Handle <event... />
            logging.debug('Event found, type is ' + e.attrib['type'])
            msg = conversation.Message('event')
            msg.date = dateutil.parser.parse(e.attrib['time'])
            if e.attrib['type'] == "windowOpened":
                msg.text = 'Window opened by ' + e.attrib['sender']
            if e.attrib['type'] == 'windowClosed':
                msg.text = 'Window closed by ' + e.attrib['sender']
            conv.add_message(msg)
        if e.tag == xmlns + 'message':  # Handle <message>
            logging.debug('Message found')
            msg = conversation.Message('message')
            msg.date = dateutil.parser.parse(e.attrib['time'])
            for child in e:
                msg.text += ET.tostring(child, encoding='unicode')  # TODO this leaves messy XML namespace stuff...
            logging.debug('Message text is: ' + msg.text)
            conv.add_message(msg)
    return conv


def get_xmlns(e):
    if e.tag[0] == "{":
        uri, ignore, tag = e.tag[1:].partition("}")
    else:
        uri = None
    return '{' + uri + '}'


def getstartdate(dom):
    """Parse XML log and determine date.  Returns a datetime object."""
    # Determine log time
    if len(dom.xpath('//@time')) == 0:
        raise ValueError("Log does not appear to contain any timestamps!")
    times = dom.xpath('//@time')  # should return a list
    try:
        # We can't use datetime.datetime.strptime() here due to timezone, have to use dateutil
        d = dateutil.parser.parse(times[0])
    except ValueError:
        # if first time won't parse, try the one after that, then give up
        d = dateutil.parser.parse(times[1])
    return d


def getenddate(dom):
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


if __name__ == "__main__":  # for test/debug purposes
    logging.basicConfig(level=logging.DEBUG)
    with open(sys.argv[1]) as fo:
        input = fo
        conv = toconv(input)
        print(conv)
