import inspect

class State(object):

    def __init__(self, name="", initial=False):
        self._name = name
        self._inital = initial
        self._completed = False
        self._error_state = False

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = self._name

    @property
    def completed(self):
        return self._completed

    @completed.setter
    def completed(self, value):
        self._completed = value

    @property
    def error_state(self):
        return self._error_state

    @error_state.setter
    def error_state(self, value):
        self._error_state = value


class StateMachine(State):

    def __init__(self, states=[]):
        assert (len(states) != 0), 'Empty State Definition'

        self.__state_names = states
        self.__states = dict()
        self.__transitions = []
        self.__triggers = set()
        self.__current_state = None
        self.__state_lock = False
        self.__transition_lock = False
        self.__set_default_states()
        self.__create_states()

    def __set_default_states(self):
        self.__states['start'] = State('start', initial=True)
        self.__states['error'] = State('error')
        self.__states['end'] = State('end')

    def __check_duplicate_states(self):
        return len(self.__state_names) != len(set(self.__state_names))

    def __check_default_states(self):
        return ("start" in self.__state_names or
                "error" in self.__state_names or
                "end" in self.__state_names)

    def __create_states(self):

        assert (self.__check_default_states() == False), 'Do Not Use "start / end / error" states.'

        for s in self.__state_names:
            self.__states[s] = State(s)

        self.__set_default_transitions()

    def __get_state(self, value):
        state = None
        for k, v in self.__states.items():
            if value in [k]:
                state = v
                break
        else:
            assert (), 'Invalid State {}'.format(value)

        return state

    def __get_transition_template(self):
        return {
            'trigger': '',
            'source': '',
            'target': '',
            'on_enter': '',
            'on_process': '',
            'on_exit': ''
        }

    def __set_default_transitions(self):
        for s in self.__state_names:
            tt = self.__get_transition_template()
            tt['trigger'] = 'on_' + s + '_error'
            tt['source'] = s
            tt['target'] = 'error'
            tt['on_enter'] = ''
            tt['on_process'] = 'on_error_state'
            tt['on_exit'] = ''

            self.__transitions.append(tt)
            # add to trigger tables
            self.__triggers.add(tt['trigger'])

            attach_method = self.__create_method()
            setattr(self, tt['trigger'], attach_method)

    def __create_method(self, **kwargs):
        def method_template(**kwargs):
            caller = inspect.stack()[1][4][0].split(".")[1].split("(")[0]
            transition_list = [x for x in self.__transitions if x['trigger'] == caller]
            assert (len(transition_list) != 0), 'Invalid transition object'
            assert (self.state_lock == False), 'State is Locked'
            src = self.__get_state(transition_list[0]['source'])
            tar = self.__get_state(transition_list[0]['target'])
            assert (src.completed == False), 'State {} already completed'.format(src.name)
            assert (tar.completed == False), 'State {} already completed'.format(tar.name)

            if transition_list[0]['on_enter'] != '':
                getattr(self, transition_list[0]['on_enter'])()

            if transition_list[0]['on_process'] != '':
                getattr(self, transition_list[0]['on_process'])()
                src.completed = True

            if transition_list[0]['on_exit'] != '':
                getattr(self, transition_list[0]['on_exit'])()

        return method_template
       

    @property
    def current_state(self):
        return self.__current_state

    @current_state.setter
    def current_state(self, value):
        assert (self.state_lock == False), 'State Changes are Locked'

        is_state_found = False
        for d in self.__states:
            if value not in d:
                continue
            else:
                is_state_found = True

        if is_state_found:
            self.__current_state = value
        else:
            assert (), 'Invalid State {}'.format(value)

    @property
    def state_lock(self):
        return self.__state_lock

    @state_lock.setter
    def state_lock(self, value):
        if self.__state_lock == False and value == True:
            self.__state_lock = True
        else:
            self.__state_lock = False
            
    @property
    def transition_lock(self):
        return self.__transition_lock
    
    @transition_lock.setter
    def transition_lock(self, value):    
        if self.__transition_lock == False:
            self.__transition_lock = True
            
    def set_transition_lock(self):
        self.transition_lock = True

    def is_transistion_valid(self, transition):
        is_valid = True
        if any( transition['trigger'] in d['trigger'] for d in self.__transitions ):
            is_valid = False
        else:
            for d in self.__transitions:                
                if d['source'] == transition['source'] and d['target'] == transition['target']:
                    is_valid = False
                    break
        return is_valid

    def add_transition(self, trigger='', source='', target='', on_enter='', on_exit='', on_process=''):
        
        assert (self.transition_lock == False), 'No more Transisitons'
        
        params = locals().copy()

        assert (self.is_transistion_valid(params) == True), 'Transition already exists'

        method_list = [func[0] for func in inspect.getmembers(self, predicate=inspect.isroutine)
                       if callable(getattr(self, func[0]))]

        state = self.__get_state(source)
        state = self.__get_state(target)

        transition = self.__get_transition_template()
        for obj in transition.keys():
            transition[obj] = locals()[obj]

        if on_enter != '':
            assert (on_enter in method_list), 'Method {} not implemented'.format(on_enter)

        if on_process != '':
            assert (on_process in method_list), 'Method {} not implemented'.format(on_process)
        else:
            assert (), 'on_process cannot be EMPTY'

        if on_exit != '':
            assert (on_exit in method_list), 'Method {} not implemented'.format(on_exit)

        self.__transitions.append(transition)

        attach_method = self.__create_method()

        setattr(self, transition['trigger'], attach_method)
               
        

    def on_error_state(self):
        self.current_state = 'error'
        self.state_lock = True
        
        