# Convert a Conversation object (see conversation.py) to an email.mime.multipart object

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import hashlib
import datetime
import email.encoders
from email.utils import format_datetime
import re
import logging

import conversation


# CSS for styling the HTML part of the message
with open('converted.css', 'r') as cssfile:
    css = cssfile.read()

# Regex for matching CSS to strip when --strip-background argument is used
bgcssregex = re.compile('background-color: .*?; *')


def mimefromconv(conv: conversation.Conversation, args) -> MIMEMultipart:
    """Now we take the Conversation object and make a MIME email message out of it..."""
    # Create a base message object for the entire conversation's components
    msg_base = MIMEMultipart('related')

    # Then a sub-part for the two alternative text and HTML components
    msg_texts = MIMEMultipart('alternative')

    fakedomain = f'{conv.service.lower()}.{conv.imclient.lower()}.invalid'  # non-routable fake domain

    # Construct 'From' header
    if '@' in conv.participants[0].userid:  # For Facebook and Jabber, which have email-like userid@domain.tld
        header_from_userid = conv.participants[0].userid
    else:  # For AIM, MSN, etc. that use traditional screennames w/o @domain.tld
        header_from_userid = conv.participants[0].userid + '@' + fakedomain
    if conv.participants[0].realname:
        header_from = f'"{conv.participants[0].realname}" <{header_from_userid}>'
    else:
        header_from = f'"{header_from_userid}" <{header_from_userid}>'
    msg_base['From'] = header_from

    # Construct 'To' header
    if '@' in conv.participants[1].userid:  # For Facebook and Jabber, which have email-like userid@domain.tld
        header_to_userid = conv.participants[1].userid
    else:  # For AIM, MSN, etc. that use traditional screennames w/o @domain.tld
        header_to_userid = conv.participants[1].userid + '@' + fakedomain
    if conv.participants[1].realname:
        header_to = f'"{conv.participants[1].realname}" <{header_to_userid}>'
    else:
        header_to = f'"{header_to_userid}" <{header_to_userid}>'
    msg_base['To'] = header_to

    # Construct 'Date' and 'Subject' headers
    if conv.startdate:
        header_date = conv.startdate
    else:
        header_date = conv.getoldestmessage().date
    if conv.service:
        header_service = conv.service
    else:
        header_service = 'Conversation'
    if conv.get_realname_from_userid(conv.origfilename.split(' (')[0]):
        header_withname = conv.get_realname_from_userid(conv.origfilename.split(' (')[0])
    else:
        header_withname = conv.origfilename.split(' (')[0]

    msg_base['Date'] = format_datetime(header_date)
    msg_base['Subject'] = f'{header_service} with {header_withname} on {header_date.strftime("%a, %b %e %Y")}'

    # Determine date format to use in logs
    if (conv.getyoungestmessage().date - conv.getoldestmessage().date) > datetime.timedelta(days=1):
        datefmt = '%D %r'
    else:
        datefmt = '%r'

    # produce a text version of the messages
    text_lines = []
    for msg in conv.messages:
        line_parts = []
        if msg.type == 'message':  # formatting for most lines
            if msg.date:
                line_parts.append('(' + msg.date.strftime(datefmt) + ')')
            if msg.msgfrom:
                if conv.get_realname_from_userid(msg.msgfrom):
                    line_parts.append(f'{conv.get_realname_from_userid(msg.msgfrom)} [{msg.msgfrom}]:')
                else:
                    line_parts.append(f'{msg.msgfrom}:')
            line_parts.append(msg.text)
            text_lines.append(' '.join(line_parts))
        if msg.type == 'event':  # Don't put the msgfrom section on system messages, it looks dumb
            if msg.date:
                line_parts.append('(' + msg.date.strftime(datefmt) + ')')
            line_parts.append(msg.text)
            text_lines.append(' '.join(line_parts))
    mimetext = MIMEText('\n'.join(text_lines), 'text')
    msg_texts.attach(mimetext)  # Attach the plaintext component as one part of (multipart/alternative)

    # Construct html_lines the same way to produce HTML version
    html_lines = []
    html_lines.append('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">')
    html_lines.append('<html>')
    html_lines.append('<head>\n' + css + '\n</head>')  # see css at top of this file
    html_lines.append('<body>')
    for message in conv.messages:
        if message.type == 'event':  # this is for system messages, etc.
            line = []
            line.append('<p class="system_message">')
            if message.date:
                line.append('<span class="timestamp">')
                line.append('(' + message.date.strftime(datefmt) + ')&nbsp;')
                line.append('</span>')
            if message.html:
                # If message exists as HTML, pass it through
                line.append('<span class="message_text">')
                line.append(message.html)
                line.append('</span>')
            elif message.text:
                line.append('<span class="message_text">')
                line.append(message.text.replace('\n', '<br>'))  # convert any LFs in message text to <br>s
                line.append('</span>')
            line.append('</p>')
            html_lines.append(''.join(line))
        else:  # for regular messages
            line = []
            line.append('<p class="message">')
            if message.date:
                line.append('<span class="timestamp">')
                line.append('(' + message.date.strftime(datefmt) + ')&nbsp;')
                line.append('</span>')
            if message.msgfrom:
                if conv.userid_islocal(message.msgfrom):
                    line.append('<span class="localname">')  # if from the local user, class it appropriately
                else:
                    line.append('<span class="name">')  # otherwise, generic screenname (likely remote)
                if conv.get_realname_from_userid(message.msgfrom):
                    line.append(conv.get_realname_from_userid(message.msgfrom) + ':&ensp;')
                else:
                    line.append(message.msgfrom + ':&ensp;')
                line.append('</span>')
            if message.html:  # If message exists as HTML, pass it through
                line.append('<span class="message_text">')
                if args.no_background:  # strip background-color, e.g. "background-color: #acb5bf;"
                    line.append(re.sub(bgcssregex, '', message.html))  # see regex at top of file
                else:
                    line.append(message.html)
                line.append('</span>')
            elif message.text:  # If there's no HTML provided, create it from text and styling information
                line.append('<span')
                if message.textfont or message.textsize or message.textcolor or message.bgcolor:
                    # only if needed, we add a style attribute to the message text...
                    line.append(' style="')
                    if message.textfont:
                        line.append('font-family: ' + message.textfont + '; ')
                    if message.textsize:
                        line.append('font-size: ' + str(int(message.textsize)) + 'pt; ')
                    if message.textcolor:
                        line.append('color: ' + message.textcolor + '; ')
                    if message.bgcolor and (not args.no_background):
                        line.append('background-color: ' + message.bgcolor + '; ')
                    line.append('"')
                line.append(' class="message_text">')
                line.append(message.text.replace('\n', '<br>'))  # convert any LFs in message text to <br>s
                line.append('</span>')
            if message.attachments:  # if the message has an Attachment, then we need to process it...
                for att in message.attachments:  # in theory there could be >1 attachment per msg, but in practice rare
                    line.append('\n<br><span class="attachment">Attachment:&nbsp;<a href="cid:'
                                + att.contentid + '">' + att.name + '</a></span>')
                    if att.data:
                        attachment_part = MIMEBase('application', att.mimetype.split('/')[-1])
                        attachment_part.set_payload(att.data)
                        email.encoders.encode_base64(attachment_part)  # BASE64 for attachments (ugh)
                        attachment_part.add_header('Content-Disposition', 'attachment', filename=att.name)
                        attachment_part['Content-ID'] = '<' + att.contentid + '>'
                        msg_base.attach(attachment_part)  # attach to the top-level object, multipart/related
            line.append('</p>')
            html_lines.append(''.join(line))  # join line components without spaces
    html_lines.append('</body>')
    html_lines.append('</html>')
    mimehtml = MIMEText('\n'.join(html_lines), 'html')  # join lines with \n chars
    msg_texts.attach(mimehtml)  # Attach the html component as second half of (multipart/alternative)

    # The References header is a hash of the sorted participants list, allowing MUA to thread Conversations together
    msg_base['References'] = ('<' + hashlib.md5(
        ' '.join(sorted(conv.listparticipantuserids())).lower().encode('utf-8')).hexdigest() + '@' + fakedomain + '>')

    # Create Message-ID by hashing the text content (allows for duplicate detection); note headers are NOT hashed
    msg_base['Message-ID'] = ('<' + hashlib.md5(
        msg_base['Date'].encode('utf-8') + msg_base['Subject'].encode('utf-8')
        + '\n'.join(text_lines).encode('utf-8')).hexdigest() + '@' + fakedomain + '>')

    # Set additional headers (comment out if not desired)
    msg_base['X-Converted-On'] = datetime.datetime.now().strftime('%a, %d %b %Y %T %z')
    msg_base['X-Original-File'] = conv.origfilename

    # Attach the (multipart/related) component to the root
    msg_base.attach(msg_texts)
    return msg_base
