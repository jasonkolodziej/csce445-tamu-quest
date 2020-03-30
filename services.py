import re
import uuid
import base64
import json


# # example of a Question
# Q_EXAMPLE_1 = {
#     "question": "What state are you in?",
#     "answer_choices": ['Texas', 'California', 'Tennessee', 'New Jersey'],
#     "answer" : "Texas"
# }

# Q_EXAMPLE_2 = {
#     "question": "What city are you in?",
#     "answer_choices": ['CStat', 'Houston', 'San Francisco', 'New York'],
#     "answer" : "CStat"
# }

# Q_EXAMPLE_3 = {
#     "question": "What is the team name are you in?",
#     "answer_choices": ['TeamSTAT', 'Poth Pirates', 'team6ix', 'other'],
#     "answer" : "TeamSTAT"
# }

# EXAMPLE_Q_LIST = [Q_EXAMPLE_1, Q_EXAMPLE_2, Q_EXAMPLE_3]
JSON_QUESTION_LIST = []
with open('./questions.json','r') as f:
    JSON_QUESTION_LIST = json.load(f)
    print(JSON_QUESTION_LIST)


# example of a map that would be loaded given the app is running
QUESTION_BANK = {}

# see last line of loading the questions list in the bank

class Question(object):
    # initializer
    def __init__(self, uid='', q=None, answer_choices=None, answer=None, good=None, fun_facts = ''):
        self.uid = uid
        self.question = q
        self.answer_choices = answer_choices
        # either the answer selected by the user or the
        # correct answer to the question
        self.answer = answer
        self.good = good
        self.fun_facts = fun_facts

    def to_user(self):
        import random
        """
            how a question and the data belonging to
            it should be represented to the user
        """
        # randomize how user sees the answers
        rand_list = self.answer_choices
        random.shuffle(rand_list)
        return {
            'question': self.question,
            # array of strings to choose from
            'answer_choices' : rand_list,
            # determines if answer was right or wrong
            'good' : self.good,
            'fun_facts' : self.fun_facts
        }
    
    def to_redis(self):
        return {
            'uid' : self.uid,
            'question' : self.question,
            'answer_choices' : self.answer_choices,
            # answer for redis has the ability to be either
            # 1 string or an array of strings
            'answer' : self.answer,
            'good' : self.good
        }
    
    @staticmethod
    def from_user(numerical_value_from_key):
        return Question(
            answer=numerical_value_from_key
            )

    @staticmethod
    def from_redis(import_from_stat_game_class):
        return Question(
            import_from_stat_game_class['uid'],
            import_from_stat_game_class['question'],
            import_from_stat_game_class['answer_choices'],
            import_from_stat_game_class['answer'],
            import_from_stat_game_class['good'],
            )

    @staticmethod
    def load_questions(question_dict_list, final_dict={}):
        """
            Load a list of question dictionaries
            to a final empty dictionary input
        """
        for q_d in question_dict_list:
            uuid = uuid_url64()
            final_dict[uuid] = Question(
                uuid,
                q=q_d['question'],
                answer_choices=q_d['answer_choices'],
                answer=q_d['answer'],
                fun_facts=q_d['fun_facts']
                )
        return final_dict


    def __repr__(self):
        return u'Question ( uid={}, question={}, answer_choices={}, answer(s)={}, good={}, fun_facts={} )'.format(
            self.uid,
            self.question,
            self.answer_choices,
            self.answer,
            self.good,
            self.fun_facts
        )
    
    def __eq__(self, user):
        if isinstance(self.answer, list):
            # during question level selection or
            # there are multiple answers
            print("multiple choices")
            return self.answer[user.answer] in self.answer_choices
        else:
            print("there is only one correct answer")
            return self.answer_choices[user.answer] == self.answer


class STATGame(object):
    """
        This python class is a class that will handle
        conjioning server-side session data
        and user input data.
    """

    # initializer
    def __init__(self, session_id, level=None, progress=[], q_dropped=[], next_question=None):
        self.session_id = session_id
        self.level = level
        self.progress = progress
        self.q_dropped = q_dropped
        self.next_question = next_question

    @staticmethod
    # defines the types of levels the user can play
    def level_types():
        return ['Bachelors', 'Masters', 'PhD']

    @staticmethod
    # defines the level choosing prompt to the user
    def level_selector_prompt():
        return 'Please select a level of difficulty.'

    @staticmethod
    def from_redis(game_key_in_session):
        return STATGame(
            game_key_in_session['session_id'],
            game_key_in_session['level'],
            game_key_in_session['progress'],
            game_key_in_session['q_dropped'],
            Question.from_redis(game_key_in_session['next_question'])
            )

    def to_redis(self):
        return {
            'session_id' : self.session_id,
            'level' : self.level,
            'progress' : self.progress,
            'q_dropped': self.q_dropped,
            'next_question': self.next_question.to_redis()
        }
    
    def new_game(self):
        """ adds the static prompts to next_question
        """
        self.next_question = Question(
                q=STATGame.level_selector_prompt(), 
                answer_choices=STATGame.level_types(),
                answer=STATGame.level_types()
                )
    
    def user_progress(self):
        # defines the length of uids completed
        return len(self.progress)
    
    def q_dropped_count(self):
        """ 
            for the user to know
            how many questions they dropped
        """
        return len(self.q_dropped)

    def to_user(self):
        """
            allows the front end (html)
            to be filled with data coming from a dictionary
        """
        return {
            'level': self.level,
            'progress': self.user_progress(),
            'q_dropped': self.q_dropped_count(),
            'next_question': self.next_question.to_user()
        }

    def resolve_user_choice(self, right_hand_from_key_in_route, question_bank=None):
        print(f"Resolving User's choice of {right_hand_from_key_in_route}")
        u_sent = right_hand_from_key_in_route
        if u_sent == 'qdrop':
            # the user wanted to qdrop the question
            print("attempting q drop")
            # add the q dropped question to the list
            self.q_dropped.append(self.next_question.uid)
            self.load_next_question_from_bank(question_bank)
            # TODO: handle max q drops
            # TODO: handle if nxtq gets called concurrently
        elif u_sent == 'nxtq':
            # user wants the next question
            print("attempting next question")
            self.load_next_question_from_bank(question_bank)
        else:
            user = Question(answer=int(u_sent))
            # ! NOTE: this is the only way you are able to
            # !       run a check
            answer_ok = self.next_question == user
            # check the games state, if None add the level, given the user's answer was ok
            if not self.level and answer_ok:
                self.level = STATGame.level_types()[user.answer]
                # load the first question
                self.load_next_question_from_bank(question_bank)  
            else:
            # update the good field we currently have for the question
            # this is to show the user they got it wrong
                print('letting the user know their choice was good / bad')
                # if user got the question right they are not allowed to see the question again
                self.progress.append(self.next_question.uid) if answer_ok else None
                # update if the users input was good or not
                self.next_question.good = answer_ok
                # remove the choices so they can't fool the system
                self.next_question.answer_choices = []


    def load_next_question_from_bank(self, bank=None):
        import random as r
        print("called load")
        print(f"Question UIDs in bank: {bank.keys()}")
        # union set of any q drops, or the ones the user have progressed through
        qd_and_prog = set(self.progress) | set(self.q_dropped) if len(self.progress) > 0 or len(self.q_dropped) > 0 else None
        print(f"Question UIDs not available: {qd_and_prog}")
        # the uids that are available
        items_avail = list(set(list(bank.keys())) - qd_and_prog) if qd_and_prog else list(bank.keys())
        print(f"Question UIDs available: {items_avail} {r.choice(items_avail)}")
        # set the next question to a random value
        self.next_question = bank[r.choice(items_avail)]


    def __repr__(self):
        return u'STATGame ( session_id={}, level={}, progress={}, q_dropped={}, next_question={} )'.format(
            self.session_id,
            self.level,
            self.progress,
            self.q_dropped,
            self.next_question
        )

def uuid_url64():
    """Returns a unique, 16 byte, URL safe ID by combining UUID and Base64
    """
    rv = base64.b64encode(uuid.uuid4().bytes).decode('utf-8')
    return re.sub(r'[\=\+\/]', lambda m: {'+': '-', '/': '_', '=': ''}[m.group(0)], rv)



QUESTION_BANK = Question.load_questions(JSON_QUESTION_LIST, QUESTION_BANK)

print("Questions loaded:")
print("*"*20)
for idd, q in QUESTION_BANK.items():
    print(q)
print("*"*20)

