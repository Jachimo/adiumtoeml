# Classes for instant messaging "conversations"
#  Inspired by the data model used by https://github.com/kadin2048/ichat_to_eml
#  Uses type hints and requires Python 3.6+

from datetime import datetime  # for hints


class Conversation:
    def __init__(self):
        self.service: str = ''  # messaging service: AIM, iChat, MSN, etc.
        self.participants: list = []
        self.startdate: datetime = ''
        self.enddate: datetime = ''
        self.messages: list = []
        self.hasattachments: bool = False

    def add_participant(self, participant):
        if participant not in self.participants:
            self.participants.append(participant)

    def set_service(self, service):
        self.service = service

    def add_message(self, message):
        # Might want to add some validation here
        self.messages.append(message)


class Participant:
    def __init__(self, userid):
        self.userid: str = userid
        self.realname: str = ''
        self.systemid: str = ''


class Message:
    def __init__(self, type):
        self.type: str = type  # when instantiating message, give it a type
        self.guid: str = ''
        self.msgfrom: str = ''
        self.msgto: str = ''
        self.date: datetime = ''
        self.text: str = ''
        self.textfont: str = ''
        self.textsize: str = ''
        self.html: str = ''

