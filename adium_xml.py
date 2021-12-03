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
    logging.debug('Parsing ' + infile.name)
    dom = xml.dom.minidom.parse(infile)

    if dom.firstChild.nodeName != 'chat':  # Do some basic sanity-checking on input
        logging.critical(os.path.basename(infile.name) + ' does not appear to contain <chat> element!')
        raise ValueError('Malformed or invalid input file')

    conv = conversation.Conversation()  # instantiate Conversation object
    conv.imclient = 'Adium'  # since we are only parsing Adium logs with this module
    conv.origfilename = os.path.basename(infile.name)  # Store name of input file and store for future reference

    # If possible, determine the IM service based on the grandparent folder name if hierarchy is either:
    #  /path/to/Adium Logs/AIM.myaccountname/theiraccountname/theiraccountname (date).chatlog
    #  /path/to/Adium/Logs*/AIM.myaccountname/theiraccountname/theiraccountname (date).chatlog
    filepathlist = os.path.realpath(infile.name).split(os.path.sep)
    if os.path.splitext(conv.origfilename)[-1] == '.chatlog' \
        and ((filepathlist[-4] == 'Adium Logs') or (filepathlist[-4].find('Logs') == 0 and filepathlist[-5] == 'Adium')):
        logging.debug(f'Detected non-bundled XML .chatlog: {conv.origfilename}')
        conv.service = filepathlist[-3].split('.', 1)[0]
        conv.localaccount  = filepathlist[-3].split('.', 1)[1].lower()
        conv.remoteaccount = filepathlist[-2].lower()
    if os.path.splitext(conv.origfilename)[-1] == '.xml' \
        and ((filepathlist[-5] == 'Adium Logs') or (filepathlist[-5].find('Logs') == 0 and filepathlist[-6] == 'Adium')):
        logging.debug(f'Detected bundled .chatlog with XML file: {conv.origfilename}')
        conv.service = filepathlist[-4].split('.', 1)[0]
        conv.localaccount  = filepathlist[-4].split('.', 1)[1].lower()
        conv.remoteaccount = filepathlist[-3].lower()

    chat = dom.firstChild  # root element should always be <chat>
    conv.service = chat.getAttribute('service').strip()  # set the service (AIM, MSN, etc.)
    if not conv.remoteaccount:
        logging.debug('Could not determine local account from input path; setting from XML')
        conv.set_remote_account(chat.getAttribute('account').strip().lower())  # set remote account from XML

    logging.debug('IM service is: ' + conv.service)
    logging.debug('Local account is: ' + conv.localaccount)
    logging.debug('Remote account is: ' + conv.remoteaccount)

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
            conv.add_participant(msg.msgfrom.lower())
            ## Start debugging TODO remove me
            logging.debug(f'Added participant (msg.msgfrom) with user id: {msg.msgfrom.lower()}')
            logging.debug(f'Should {msg.msgfrom} be considered local?  {(msg.msgfrom.lower() == conv.localaccount)}')
            logging.debug(f'Should {msg.msgfrom} be considered remote?  {(msg.msgfrom.lower() == conv.remoteaccount)}')
            logging.debug(f'Participant user id list contains {conv.listparticipantuserids()}')
            for pid in conv.listparticipantuserids():
                logging.debug(f'\n  User ID: {conv.get_participant(pid).userid}'
                              f'\n  Position: {conv.get_participant(pid).position}'
                              f'\n  Is Local? {conv.userid_islocal(pid)}'
                              f'\n  Is Remote? {conv.userid_isremote(pid)}')
            ## End Debugging
            if e.hasAttribute('alias'):  # Facebook logs have an 'alias' attribute containing real name
                conv.add_realname_to_userid(msg.msgfrom, e.getAttribute('alias'))
            msg.text = get_inner_text(e)
            logging.debug('Message text is: ' + msg.text)
            if e.firstChild.nodeName == 'div':
                try:
                    msg.html = e.firstChild.firstChild.toxml()  # strip outermost <div>
                except AttributeError:  # usually this is caused by text directly inside the <div> without a <span>
                    msg.html = e.firstChild.toxml()
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
