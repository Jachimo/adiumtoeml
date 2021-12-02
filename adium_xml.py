#!/usr/bin/env python3
# Utility functions for processing Adium XML-based log files

import sys
import os
import logging
import dateutil.parser
import xml.dom.minidom
from typing import TextIO

import conversation
import adium_html


def toconv(infile: TextIO) -> conversation.Conversation:
    """Take a file-like input object containing an XML chat log, and parse to produce a Conversation object"""

    dom = xml.dom.minidom.parse(infile)

    if dom.firstChild.nodeName != 'chat':  # Do some basic sanity-checking on input
        logging.critical(os.path.basename(infile.name) + ' does not appear to contain <chat> element!')
        raise ValueError('Malformed or invalid input file')

    chat = dom.firstChild  # root element should always be <chat>

    conv = conversation.Conversation()  # instantiate Conversation object
    conv.origfilename = os.path.basename(infile.name)  # Store name of input file and store for future reference
    conv.imclient = 'Adium'  # since we are only parsing Adium logs with this module
    conv.set_service(chat.getAttribute('service').strip())  # set the service (AIM, MSN, etc.)
    conv.set_account(chat.getAttribute('account').strip())  # set conv.account to the local userid

    logging.debug('IM service is ' + conv.service)
    logging.debug('Local account is: ' + conv.account)

    for e in chat.childNodes:
        if (e.nodeName == 'event') or (e.nodeName == 'status'):  # Handle <event... /> and <status... />
            msg = conversation.Message('event')
            msg.date = dateutil.parser.parse(e.getAttribute('time'))
            msg.msgfrom = e.getAttribute('sender')
            if e.getAttribute('type') == 'windowOpened':
                msg.text = 'Window opened by ' + e.getAttribute('sender')
            if e.getAttribute('type') == 'windowClosed':
                msg.text = 'Window closed by ' + e.getAttribute('sender')
            if e.getAttribute('type') in ['offline', 'online', 'idle', 'available']:
                msg.text = 'User ' + e.getAttribute('sender') + ' is now ' + e.getAttribute('type') + '.'
            conv.add_message(msg)
        elif e.nodeName == 'message':  # Handle <message>
            msg = conversation.Message('message')
            msg.date = dateutil.parser.parse(e.getAttribute('time'))
            msg.msgfrom = e.getAttribute('sender')
            conv.add_participant(msg.msgfrom)
            ## Start debugging TODO remove me
            logging.debug(f'Should {msg.msgfrom} be considered local?  {(msg.msgfrom == conv.account)}')
            logging.debug(f'Added participant (msg.msgfrom) with user id: {msg.msgfrom}')
            for pid in conv.listparticipantuserids():
                logging.debug(f'Participant user id list contains {conv.listparticipantuserids()}')
                logging.debug(f'\n  User ID: {conv.get_participant(pid).userid},'
                              f'\n  Position: {conv.get_participant(pid).position},'
                              f'\n  Is Local? {conv.userid_islocal(pid)}')
            ## End Debugging
            if e.hasAttribute('alias'):  # Facebook logs have an 'alias' attribute containing real name
                conv.add_realname_to_userid(msg.msgfrom, e.getAttribute('alias'))
            msg.text = get_inner_text(e)
            logging.debug('Message text is: ' + msg.text)
            if e.firstChild.nodeName == 'div':
                msg.html = e.firstChild.firstChild.toxml()  # strip outermost <div>
            else:
                msg.html = e.firstChild.toxml()
            logging.debug('Message HTML is: ' + msg.html)
            conv.add_message(msg)
            logging.debug('End of message processing\n')  # TODO remove me

    # Get date from filename, if present; otherwise use timestamp from first message
    if (conv.origfilename.find('(') != -1) and (conv.origfilename.find(')') != -1):
        filenamedatestr = adium_html.getlinecontent(conv.origfilename, '(', ')')
        try:
            filenamedate = dateutil.parser.parse(filenamedatestr.replace('.', ':'))
            conv.startdate = filenamedate
        except dateutil.parser.ParserError:
            logging.debug('Dateutil parser unable to parse: ' + filenamedatestr)
    else:
        conv.startdate = conv.getoldestmessage().date

    # If there are less than two Participants in the Conversation, pad it with 'UNKNOWN' to prevent errors later
    if len(conv.participants) < 2:
        conv.add_participant('UNKNOWN')
        conv.add_realname_to_userid('UNKNOWN', 'Unknown User')

    return conv


def get_inner_text(node):
    """Get all text associated with node and its children"""
    # Thanks to Manlio Perillo on python-list@python.org
    textlist = ['']
    for n in node.childNodes:
        if n.nodeName == '#text':
            textlist.append(n.data)
        else:
            textlist.append(get_inner_text(n))
    return ''.join(textlist)


if __name__ == "__main__":  # for test/debug purposes
    logging.basicConfig(level=logging.DEBUG)
    with open(sys.argv[1]) as fo:
        conv = toconv(fo)
        print(conv)
