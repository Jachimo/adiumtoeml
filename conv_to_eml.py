# Convert a Conversation object (see conversation.py) to an email.mime.multipart object

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
import hashlib
import datetime
import email.encoders

import conversation


# CSS for styling the HTML part of the message
with open('converted.css', 'r') as cssfile:
    css = cssfile.read()

# Nonroutable domain (or domain you own) to use in constructing URL-like objects
#  DO NOT USE AN ACTUAL DOMAIN YOU DO NOT OWN/CONTROL
#  Default is 'imservice.improgram.invalid' e.g. 'aim.adium.invalid'
domain: str = 'adium.invalid'


def mimefromconv(conv: conversation.Conversation) -> MIMEMultipart:
    """Now we take the Conversation object and make a MIME email message out of it..."""

    # Create a base message object for the entire conversation's components
    msg_base = MIMEMultipart('related')
    # Then a sub-part for the two alternative text and HTML components
    msg_texts = MIMEMultipart('alternative')

    # Create a fake domain-like string for constructing URL-like identifiers such as Message-ID
    if conv.service:
        fakedomain = conv.service.lower() + '.' + domain
    else:
        fakedomain = domain

    # Set From and To using the participants list (makes emails seem directional)
    #  If there are real names associated with userids, we include them, but if not we just use userids
    if conv.participants[0].realname and conv.participants[1].realname:
        msg_base['From'] = ('"' + conv.participants[0].realname + '" ' 
                            + '<' + conv.participants[0].userid + '@' + fakedomain + '>')
        msg_base['To'] = ('"' + conv.participants[1].realname + '" ' 
                          + '<' + conv.participants[1].userid + '@' + fakedomain + '>')
    else:
        msg_base['From'] = ('"' + conv.participants[0].userid + '" ' 
                            + '<' + conv.participants[0].userid.replace('@', '[at]') + '@' + fakedomain + '>')
        msg_base['To'] = ('"' + conv.participants[1].userid + '" ' 
                          + '<' + conv.participants[1].userid.replace('@', '[at]') + '@' + fakedomain + '>')

    # If the Conversation has startdate set (from filename) we use it, otherwise use oldest Message date
    if conv.startdate:
        msg_base['Date'] = conv.startdate.strftime('%a, %d %b %Y %T %z')  # RFC2822 format
    else:
        msg_base['Date'] = conv.getoldestmessage().date.strftime('%a, %d %b %Y %T %z')

    # Construct the Subject line from the file name, but cleaned up slightly
    msg_base['Subject'] = ('Chat with ' + conv.origfilename.split(' (')[0] + ' on '
                           + conv.origfilename[conv.origfilename.find(" (") + 2: conv.origfilename.find(")")])

    # produce a text version of the messages
    text_lines = []
    for msg in conv.messages:
        line_parts = []
        if msg.type == 'message':  # formatting for most lines
            if msg.date:
                line_parts.append('(' + msg.date.time().strftime('%r') + ')')
            if msg.msgfrom:
                line_parts.append(msg.msgfrom + ':')
            line_parts.append(msg.text)
            text_lines.append(' '.join(line_parts))
        if msg.type == 'event':  # Don't put the msgfrom section on system messages, it looks dumb
            if msg.date:
                line_parts.append('(' + msg.date.time().strftime('%r') + ')')
            line_parts.append(msg.text)
            text_lines.append(' '.join(line_parts))
    mimetext = MIMEText('\n'.join(text_lines), 'text')
    msg_texts.attach(mimetext)  # Attach the plaintext component as one part of (multipart/related)

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
                line.append('(' + message.date.strftime('%r') + ')&nbsp;')
                line.append('</span>')
            if message.html:
                # If message exists as HTML, pass it through
                line.append('<span class="message_text">')
                line.append(message.html)
                line.append('</span>')
            elif message.text:
                # If there's no HTML provided, create it from text and any styling information provided
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
                line.append('(' + message.date.strftime('%r') + ')&nbsp;')
                line.append('</span>')
            if message.msgfrom:
                line.append('<span class="screenname">')
                line.append(message.msgfrom + ':&ensp;')
                line.append('</span>')
            if message.html:
                # If message exists as HTML, pass it through
                line.append('<span class="message_text">')
                line.append(message.html)
                line.append('</span>')
            elif message.text:
                # If there's no HTML provided, create it from text and any styling information provided
                line.append('<span')
                if (message.textfont) or (message.textsize) or (message.textcolor) or (message.bgcolor):
                    # only if needed, we add a style attribute to the message text...
                    line.append(' style="')
                    if message.textfont:
                        line.append('font-family: ' + message.textfont + '; ')
                    if message.textsize:
                        line.append('font-size: ' + str(int(message.textsize)) + 'pt; ')
                    if message.textcolor:
                        line.append('color: ' + message.textcolor + '; ')
                    if message.bgcolor:
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
                        email.encoders.encode_base64(attachment_part)  # BASE64 for attachments (still needed as of 2021)
                        attachment_part.add_header('Content-Disposition', 'attachment', filename=att.name)
                        attachment_part['Content-ID'] = '<' + att.contentid + '>'
                        msg_base.attach(attachment_part)  # attach to the top-level object, multipart/related
            line.append('</p>')
            html_lines.append(''.join(line))
    html_lines.append('</body>')
    html_lines.append('</html>')
    mimehtml = MIMEText('\n'.join(html_lines), 'html')  # TODO might need to fix encoding to prevent BASE64ing of UTF8
    msg_texts.attach(mimehtml)  # Attach the html component as second half of (multipart/related)

    # The References header is a hash of the sorted participants list, allowing MUA to thread Conversations together
    msg_base['References'] = ('<' + hashlib.md5(
        ' '.join(sorted(conv.listparticipantuserids())).lower().encode('utf-8')).hexdigest() + '@' + fakedomain + '>')

    # Create Message-ID by hashing the text content (allows for duplicate detection); note headers are NOT hashed
    msg_base['Message-ID'] = ('<' + hashlib.md5(
        msg_base['Date'].encode('utf-8') + msg_base['Subject'].encode('utf-8')
        + '\n'.join(text_lines).encode('utf-8')).hexdigest() + '@' + fakedomain + '>')

    # Set additional headers (comment out if not desired)
    msg_base['X-Converted-On'] = datetime.datetime.now().strftime('%a, %d %b %Y %T %z')

    # Attach the (multipart/related) component to the root
    msg_base.attach(msg_texts)
    return msg_base
