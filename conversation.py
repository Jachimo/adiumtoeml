# Classes for instant messaging "conversations"
#  Inspired by the data model used by https://github.com/kadin2048/ichat_to_eml
#  Uses type hints and requires Python 3.6+

from datetime import datetime  # for hints
import hashlib


class Conversation:
    """Top-level class for holding instant messaging Conversations"""
    def __init__(self):
        self.origfilename: str = ''  # Originating file name (where conversation was parsed from)
        self.service: str = ''  # messaging service: AIM, iChat, MSN, etc.
        self.account: str = ''  # userid of local IM account (set BEFORE populating participants list!)
        self.participants: list = []  # List of Participant objects
        self.startdate: datetime = False
        self.enddate: datetime = False
        self.messages: list = []  # List of Message objects
        self.hasattachments: bool = False  # Flag to indicate that 1 or more message contains an attachment

    def add_participant(self, userid):
        if userid.lower() not in self.listparticipantuserids():  # if userid is not in any existing Participant.userid
            p = Participant(userid.lower())
            self.participants.append(p)
        if userid.lower() == self.account.lower():  # if the userid we are adding is the local account, mark it as such
            self.set_local_account(userid.lower())

    def listparticipantuserids(self):
        userids = []
        for p in self.participants:
            userids.append(p.userid)
        return userids

    def add_realname_to_userid(self, userid, realname):
        for p in self.participants:
            if p.userid.lower() == userid.lower():
                p.realname = realname

    def add_systemid_to_userid(self, userid, systemid):
        for p in self.participants:
            if p.userid.lower() == userid.lower():
                p.systemid = systemid

    def set_account(self, account):
        self.account = account.lower()

    def set_service(self, service):
        self.service = service

    def add_message(self, message):
        # Might want to add some validation here
        self.messages.append(message)

    def getoldestmessage(self):
        try:
            return sorted(self.messages)[0]
        except:  # TODO figure out what exception this throws and catch specifically
            raise
            #return False

    def getyoungestmessage(self):
        try:
            return sorted(self.messages)[-1]
        except:  # TODO figure out what exception this throws and catch specifically
            raise
            #return False

    def set_local_account(self, userid):
        for p in self.participants:
            if p.userid.lower() == userid.lower():
                p.position = 'local'

    def set_remote_account(self, userid):
        for p in self.participants:
            if p.userid.lower() == userid.lower():
                p.position = 'remote'

    def userid_islocal(self, userid):
        for p in self.participants:
            if (p.userid.lower() == userid.lower()) and (p.position == 'local'):
                return True
        return False


class Participant:
    """Represents a single participant in a conversation; conversations may have 1 to many participants"""
    def __init__(self, userid):
        self.userid: str = userid
        self.realname: str = ''
        self.systemid: str = ''
        self.position: str = ''  # either 'local' or 'remote'


class Message:
    """Represents a single message sent by one Participant to another in a Conversation"""
    def __init__(self, type):
        self.type: str = type  # types: 'message' or 'event'
        self.guid: str = ''
        self.msgfrom: str = ''
        self.msgto: str = ''
        self.date: datetime = ''
        self.text: str = ''  # text version of the message
        self.textfont: str = ''  # font to display text version
        self.textsize: str = ''  # size to display text version
        self.textcolor: str = ''  # color to display text version
        self.bgcolor: str = ''  # background/highlight color to display text version
        self.html: str = ''  # HTML version of the message
        self.attachments: list = []  # List of Attachment objects (optional)

    def __eq__(self, other):
        """Define equality for purposes of sorting"""
        if self.guid and other.guid:  # if GUIDs are present on both, depend on them for equivalency
            return self.guid == other.guid
        else:
            return self.__dict__ == other.__dict__  # Otherwise, look at dictionaries

    def __lt__(self, other):
        """Define less-than for purposes of sorting Message lists (sorted by date)"""
        return self.date < other.date  # Default sort by message date/time


class Attachment:
    """Represents an optional attachment that can be carried by a Message"""
    def __init__(self):
        self.name: str = ''
        self.data = b''
        self.contentid: str = ''
        self.mimetype: str = ''

    def gen_contentid(self):
        """Generate a contentID hash from the attachment data, should be called after attachment payload changed"""
        # We want the ContentID to be deterministic based on content, not random (for dupe checking/filtering)
        self.contentid = hashlib.md5(self.data).hexdigest()

    def set_payload(self, bindata):
        """Set the binary payload of the attachment"""
        self.data = bindata
        self.gen_contentid()
