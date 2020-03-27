import re
import uuid
import base64

class STATGame:
    # initializer
    def __init__(self, level, session_id):
        self.session_id = session_id
        self.level = level
        self.progress = 0
        self.q_dropped = 0
        self.next_question = ''

    @staticmethod
    # defines the types of levels the user can play
    def level_types():
        return ['Bachelors', 'Masters', 'PhD']
    @staticmethod
    # defines the level choosing prompt to the user
    def level_selector_prompt():
        return 'Please select a level of difficulty.'


def uuid_url64():
    """Returns a unique, 16 byte, URL safe ID by combining UUID and Base64
    """
    rv = base64.b64encode(uuid.uuid4().bytes).decode('utf-8')
    return re.sub(r'[\=\+\/]', lambda m: {'+': '-', '/': '_', '=': ''}[m.group(0)], rv)