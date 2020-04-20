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

JSON_MILESTONE_LIST = []
with open('./milestones.json','r') as f:
    JSON_MILESTONE_LIST = json.load(f)


# example of a map that would be loaded given the app is running
QUESTION_BANK = {}
MILESTONE_BANK = {}

# ! see last line of loading the questions list in the bank
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

    def to_user(self, randomize=True):
        import random
        """
            how a question and the data belonging to
            it should be represented to the user
        """
        # randomize how user sees the answers
        rand_list = self.answer_choices
        random.shuffle(rand_list) if randomize else None
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
    def __init__(
        self, 
        session_id, 
        level=None, 
        progress=[], 
        q_dropped=[], 
        next_question=None,
        completed_milestones=[],
        next_milestone=None
        ):
        self.session_id = session_id
        self.level = level
        self.progress = progress
        self.q_dropped = q_dropped
        self.next_question = next_question
        self.completed_milestones = completed_milestones
        self.next_milestone = next_milestone

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
            Question.from_redis(game_key_in_session['next_question']),
            game_key_in_session['completed_milestones'],
            Milestone.from_redis(game_key_in_session['next_milestone'])
            )

    def to_redis(self):
        return {
            'session_id' : self.session_id,
            'level' : self.level,
            'progress' : self.progress,
            'q_dropped': self.q_dropped,
            'next_question': self.next_question.to_redis(),
            'completed_milestones' : self.completed_milestones,
            'next_milestone' : self.next_milestone.to_redis() if self.next_milestone else self.next_milestone
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

    def to_user(self, randomize=True):
        """
            allows the front end (html)
            to be filled with data coming from a dictionary
        """
        return {
            'level': self.level,
            'progress': self.user_progress(),
            'q_dropped': self.q_dropped_count(),
            'next_question': self.next_question.to_user(randomize=randomize)
        }

    def resolve_user_choice(
        self, 
        right_hand_from_key_in_route, 
        question_bank=None, 
        milestone_bank=None
        ):
        print(f"Resolving User's choice of {right_hand_from_key_in_route}")
        u_sent = right_hand_from_key_in_route
        if u_sent == 'qdrop':
            # the user wanted to qdrop the question
            print("attempting q drop")
            # add the q dropped question to the list
            self.q_dropped.append(self.next_question.uid)
            self.load_next_question_from_bank(question_bank)
            # TODO: handle max q drops
        elif u_sent == 'nxtq':
            # user wants the next question
            if self.next_milestone:
                self.completed_milestones.append(self.next_milestone.uid)
                self.next_milestone = None
            if len(self.next_question.answer_choices) == 0:
                print("attempting next question")
                self.load_next_question_from_bank(question_bank)
            else:
                print("*"*20)
                print("Cannot run next question")
                print("*"*20)
        else:
            # user is answering a question
            if self.next_milestone:
                self.completed_milestones.append(self.next_milestone.uid)
                self.next_milestone = None
            presented_question = Question(answer=int(u_sent))
            # ! NOTE: this is the only way you are able to
            # !       run a check
            answer_ok = self.next_question == presented_question
            # check the games state, 
            # if None add the level, 
            # given the user's answer was ok
            if not self.level and answer_ok:
                self.level = STATGame.level_types()[presented_question.answer]
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
                # TODO: add logic that determines if there is a milestone needed to be shown in
                self.next_milestone_given_ctx(milestone_bank) if answer_ok else None

    def next_milestone_given_ctx(self, bank=None):
        import random as r
        # TODO: add logic that determines if there is a milestone needed
        self.next_milestone = bank[r.choice(list(bank.keys()))]
        print('+'*20)
        print(f'next milestone id: {self.next_milestone}')
        print('+'*20)


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
        return u'STATGame ( session_id={}, level={}, progress={}, q_dropped={}, next_question={}, completed_milestones={}, next_milestone={} )'.format(
            self.session_id,
            self.level,
            self.progress,
            self.q_dropped,
            self.next_question,
            self.completed_milestones,
            self.next_milestone
        )

class Milestone(object):
    # initializer
    def __init__(
        self, 
        uid='', 
        name='', 
        announcement='', 
        quote='', 
        learn_more='', 
        occurs = [],
        photo_name = ''
        ):
        '''
        Milestones can have the ability to occur during a specific time frame
        i.e. during a time in which the server is running, the server is running in
        September and it's Saturday (make sure to show the `Game Day` milestone)
        or USER CONTEXT, the user is at 90 hours it's during the Fall or Spring
        so present the `Ring Day` milestone
        :params uid: string, generated by server when loading on to server
        :params name: string, presented on the `milestone.html.j2` template as page label
        :params announcement: string, the header title that is presented on `milestone.html.j2` template
        :params quote: string, underneath the announcement for details on the Aggie Milestone
        :params lean_more: string, of an external url link that is embedded in a button on the `milestone.html.j2` template
                            for the user to learn more on the milestone
        :params occurs: list[string], first value = is first occurrence of milestone;
                                      nth value = ... a date;
                                      3rd to last value = is the last occurrence of the milestone;
                                      2nd to last value = day || week || month || exact;
                                      last value = requirements must be met by the STATGame class
                                                   before presenting
                                                   i.e. "progress>90" is the users game hours is greater than 90
        :params photo_name: string, of the photo that will be presented on the `milestone.html.j2` template 
        '''
        self.uid = uid
        self.name = name
        self.announcement = announcement
        self.quote = quote
        self.learn_more = learn_more
        self.occurs = occurs
        self.photo_name = photo_name

    def to_user(self):
        """
            how a milestone and the data belonging to
            it should be represented to the user
        """
        return {
            'uid' : self.uid,
            'name': self.name,
            'announcement' : self.announcement,
            'quote' : self.quote,
            'learn_more' : self.learn_more,
            'photo_name': self.photo_name
        }
    
    def to_redis(self):
        return {
            'uid' : self.uid,
            'name' : self.name,
            'occurs' : self.occurs,
        }
    
    # @staticmethod
    # def from_user(numerical_value_from_key):
    #     return Question(
    #         answer=numerical_value_from_key
    #         )

    @staticmethod
    def from_redis(import_from_stat_game_class):
        if import_from_stat_game_class:
            return Milestone(
                uid=import_from_stat_game_class['uid'],
                name=import_from_stat_game_class['name'],
                occurs=import_from_stat_game_class['occurs']
                )
        else:
            return None

    @staticmethod
    def load_milestones(milestone_dict_list, final_dict={}):
        """
            Load a list of question dictionaries
            to a final empty dictionary input
        """
        for m in milestone_dict_list:
            uuid = uuid_url64()
            final_dict[uuid] = Milestone(
                uuid,
                name=m['name'],
                announcement=m['announcement'],
                quote=m['quote'],
                learn_more=m['learn_more'],
                occurs=m['occurs'],
                photo_name=m['photo_name']
                )
        return final_dict


    def __repr__(self):
        return u'Milestone ( uid={}, name={}, announcement={}, learn_more={}, occurs={}, photo_name={} )'.format(
            self.uid,
            self.name,
            self.announcement,
            self.learn_more,
            self.occurs,
            self.photo_name
        )

def uuid_url64():
    """Returns a unique, 16 byte, URL safe ID by combining UUID and Base64
    """
    rv = base64.b64encode(uuid.uuid4().bytes).decode('utf-8')
    return re.sub(r'[\=\+\/]', lambda m: {'+': '-', '/': '_', '=': ''}[m.group(0)], rv)



QUESTION_BANK = Question.load_questions(JSON_QUESTION_LIST, QUESTION_BANK)

MILESTONE_BANK = Milestone.load_milestones(JSON_MILESTONE_LIST, MILESTONE_BANK)

print("Questions loaded:")
print("*"*20)
for idd, q in QUESTION_BANK.items():
    print(q)
print("*"*20)

print("Milestones loaded:")
print("*"*20)
for idd, q in MILESTONE_BANK.items():
    print(q)
print("*"*20)

