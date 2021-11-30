#!/usr/bin/env python3
# Utility functions for processing Adium XML-based log files

import sys
import os
import logging
import dateutil.parser
import xml.etree.ElementTree as ET  # change from lxml to xml
from typing import TextIO

import conversation


def toconv(infile: TextIO) -> conversation.Conversation:
    """Take a file-like input object containing an XML chat log, and parse to produce a Conversation object"""

    dom = ET.parse(infile)  # parse the input file and get back ElementTree
    logging.debug('Input parsed to: ' + str(dom))

    root = dom.getroot()  # get the root element, which should be <chat>
    logging.debug('Root element is: ' + str(root))

    xmlns = get_xmlns(root)  # Get the XML namespace, if there is one (usually is)
    logging.debug('XML Namespace is: ' + xmlns)

    conv = conversation.Conversation()  # instantiate Conversation object
    conv.origfilename = os.path.basename(infile.name)  # Determine name of input file and store for future reference

    conv.set_service(root.attrib['service'])  # set the service (AIM, MSN, etc.)
    logging.debug('IM service is ' + conv.service)

    conv.set_account(root.attrib['account'])
    logging.debug('IM service account is: ' + conv.account)

    for e in root.iter():  # iterate over all child elements of the root
        if e.tag == xmlns + 'event':  # Handle <event... />
            #logging.debug('Event found, type is ' + e.attrib['type'])
            msg = conversation.Message('event')
            msg.date = dateutil.parser.parse(e.attrib['time'])
            msg.msgfrom = e.attrib['sender']
            if e.attrib['type'] == "windowOpened":
                msg.text = 'Window opened by ' + e.attrib['sender']
            if e.attrib['type'] == 'windowClosed':
                msg.text = 'Window closed by ' + e.attrib['sender']
            conv.add_message(msg)
        elif e.tag == xmlns + 'status':  # Handle <status... />
            #logging.debug('Status found, type is ' + e.attrib['type'])
            msg = conversation.Message('event')
            msg.date = dateutil.parser.parse(e.attrib['time'])
            msg.msgfrom = e.attrib['sender']
            if e.attrib['type'] == "offline":
                msg.text = 'User ' + e.attrib['sender'] + ' is now offline.'
            if e.attrib['type'] == "online":
                msg.text = 'User ' + e.attrib['sender'] + ' is now online.'
            conv.add_message(msg)
        elif e.tag == xmlns + 'message':  # Handle <message>
            #logging.debug('Message found')
            msg = conversation.Message('message')
            msg.date = dateutil.parser.parse(e.attrib['time'])
            msg.msgfrom = e.attrib['sender']
            conv.add_participant(e.attrib['sender'])
            for t in e.itertext():  # Get the text of all child elements and concat into msg.text
                msg.text += t
            logging.debug('Message text is: ' + msg.text)
            for c in e.iter():  # Inspect all sub-elements of <message> recursively
                c.tag = c.tag.rpartition('}')[-1]  # strip namespace from HTML elements
                msg.html = ET.tostring(c, encoding='unicode')
            logging.debug('Message HTML is: ' + msg.html)
            conv.add_message(msg)
        # TODO handle attachments if found?
    return conv


def get_xmlns(e):
    """Determine XML namespace of supplied Element."""
    if e.tag[0] == "{":
        uri, ignore, tag = e.tag[1:].partition("}")
    else:
        uri = None
    return '{' + uri + '}'


if __name__ == "__main__":  # for test/debug purposes
    logging.basicConfig(level=logging.DEBUG)
    with open(sys.argv[1]) as fo:
        conv = toconv(fo)
        print(conv)
        print(conv.__dir__())
