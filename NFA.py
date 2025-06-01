import json
import graphviz
import random
from copy import deepcopy

class NFA:
    def __init__(self, states, alphabet, start_state, accept_states):
        self.states = set(states)
        self.alphabet = set(alphabet)
        self.transition_table = {}  # {(state, symbol): set(next_states)}
        self.start_state = start_state
        self.accept_states = set(accept_states)
        self.state_symbol = 'S'

    def add_transition(self, from_state, symbol, to_states):
        if symbol not in self.alphabet:
            raise Exception(f"Symbol {symbol} does not belong to the automata alphabet.")

        if from_state not in self.states:
            raise Exception(f"State {self.state_symbol}{from_state} does not belong to the automata.")

        for s in to_states:
            if s not in self.states:
                raise Exception(f"State {self.state_symbol}{s} does not belong to the automata.")

            if s == self.start_state:
                raise Exception(f"Transition to initial state is impossible ({self.state_symbol}{from_state} -> {self.state_symbol}{s}).")


        key = (from_state, symbol)
        if key not in self.transition_table:
            self.transition_table[key] = set()
        self.transition_table[key].update(to_states)

    def new_state(self):
        max_state = max(self.states)
        self.states.add(max_state + 1)

    def add_symbol(self, symbol):
        self.alphabet.add(symbol)

    def run(self, input_str):
        return self._run_helper(self.start_state, input_str, 0)

    def _run_helper(self, current_state, input_str, index):
        if index == len(input_str):
            if current_state in self.accept_states:
                return True

            return False

        current_symbol = input_str[index]
        for next_state in self.transition_table.get((current_state, current_symbol), []):
            if self._run_helper(next_state, input_str, index + 1):
                return True

        return False

    def to_json(self):
        return {
            "states": list(self.states),
            "alphabet": list(self.alphabet),
            "transition_table": [
                {
                    "from_state": key[0],
                    "symbol": key[1],
                    "to_states": list(value)
                }
                for key, value in self.transition_table.items()
            ],
            "start_state": self.start_state,
            "accept_states": list(self.accept_states)
        }

    @classmethod
    def from_json(cls, data):
        nfa = cls(
            set(data["states"]),
            set(data["alphabet"]),
            data["start_state"],
            set(data["accept_states"])
        )

        for trans in data["transition_table"]:
            nfa.add_transition(
                trans["from_state"],
                trans["symbol"],
                set(trans["to_states"])
            )

        return nfa

    def write_to_file(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.to_json(), f, indent=4)

    def read_from_file(self, filename):
        with open(filename, 'r') as f:
            data = json.load(f)

        nfa = NFA.from_json(data)

        self.states = nfa.states
        self.alphabet = nfa.alphabet
        self.transition_table = nfa.transition_table
        self.start_state = nfa.start_state
        self.accept_states = nfa.accept_states

    def get_unreachable(self):
        reachable_states = set()
        boundary = set()
        reachable_states.add(self.start_state)

        boundary.add(self.start_state)
        while boundary:
            s = boundary.pop()
            for symbol in self.alphabet:
                for next_state in self.transition_table.get((s, symbol), []):
                    if next_state not in reachable_states:
                        reachable_states.add(next_state)
                        boundary.add(next_state)

        return self.states - reachable_states

    def remove_unreachable(self):
        unreachable = self.get_unreachable()

        self.states -= unreachable
        self.accept_states -= unreachable
        self.transition_table = {
            k: v for k, v in self.transition_table.items() if k[0] not in unreachable
        }

    def get_with_offset(self, offset):
        new_states = {state + offset for state in self.states}
        new_start_state = self.start_state + offset
        new_accept_states = {state + offset for state in self.accept_states}

        new_transition_table = {}
        for (from_state, symbol), to_states in self.transition_table.items():
            new_transition_table[(from_state + offset, symbol)] = {s + offset for s in to_states}

        nfa = NFA(new_states, self.alphabet, new_start_state, new_accept_states)
        nfa.transition_table = new_transition_table

        return nfa

    @staticmethod
    def generate_random(states_count):
        num_symbols = random.randint(2, 3)
        num_final_states = random.randint(2, 3)

        alphabet = {chr(ord('a') + random.randint(0, 25)) for _ in range(num_symbols)}
        states = set(range(states_count))

        start_state = 0
        final_states = {random.randint(0, states_count-1) for _ in range(num_final_states)}

        transition_table = {}
        for i in range(1, states_count):
            random_state = random.randint(0, i-1)
            random_symbol = random.choice(list(alphabet))
            key = (random_state, random_symbol)
            if key not in transition_table:
                transition_table[key] = set()
            transition_table[key].add(random.randint(1, states_count-1))

        p = 0.1
        for state in states:
            for symbol in alphabet:
                for target_state in states:
                    if target_state == 0:
                        continue
                    if random.random() < p:
                        key = (state, symbol)
                        if key not in transition_table:
                            transition_table[key] = set()
                        transition_table[key].add(target_state)
                        
        nfa = NFA(states, alphabet, start_state, final_states)
        nfa.transition_table = transition_table
        return nfa

    @staticmethod
    def concatenation(nfa1, nfa2):
        offset = max(nfa1.states) + 1
        offset = 0

        # nfa2_offset = nfa2.get_with_offset(offset)
        nfa2_offset = nfa2

        new_states = nfa1.states | nfa2_offset.states
        new_alphabet = nfa1.alphabet | nfa2_offset.alphabet
        new_accept_states = set(nfa2_offset.accept_states)
        new_transition_table = deepcopy(nfa1.transition_table)

        for k, v in nfa2_offset.transition_table.items():
            if k in new_transition_table:
                new_transition_table[k].update(v)
            else:
                new_transition_table[k] = set(v)

        for accept_state in nfa1.accept_states:
            key = (accept_state, '\0')
            if key in new_transition_table:
                new_transition_table[key].add(nfa2_offset.start_state)
            else:
                new_transition_table[key] = {nfa2_offset.start_state}
        result = NFA(new_states, new_alphabet, nfa1.start_state, new_accept_states)
        result.transition_table = new_transition_table
        return result

    @staticmethod
    def alternative(nfa1, nfa2):
        offset = max(nfa1.states) + 1
        nfa2_offset = nfa2.get_with_offset(offset)
        new_start_state = max(nfa2_offset.states) + 1
        new_states = nfa1.states | nfa2_offset.states | {new_start_state}
        new_alphabet = nfa1.alphabet | nfa2_offset.alphabet
        new_accept_states = set(nfa1.accept_states) | {s for s in nfa2_offset.accept_states}
        new_transition_table = deepcopy(nfa1.transition_table)
        for k, v in nfa2_offset.transition_table.items():
            if k in new_transition_table:
                new_transition_table[k].update(v)
            else:
                new_transition_table[k] = set(v)
        # Epsilon transitions from new start to both old starts
        new_transition_table[(new_start_state, '\0')] = {nfa1.start_state, nfa2_offset.start_state}
        result = NFA(new_states, new_alphabet, new_start_state, new_accept_states)
        result.transition_table = new_transition_table
        return result

    @staticmethod
    def iteration(nfa):
        new_start_state = max(nfa.states) + 1
        new_states = set(nfa.states) | {new_start_state}
        new_alphabet = set(nfa.alphabet)
        new_accept_states = set(nfa.accept_states) | {new_start_state}
        new_transition_table = deepcopy(nfa.transition_table)
        # Epsilon from new start to old start
        new_transition_table[(new_start_state, '\0')] = {nfa.start_state}
        # Epsilon from each accept state to old start
        for accept_state in nfa.accept_states:
            key = (accept_state, '\0')
            if key in new_transition_table:
                new_transition_table[key].add(nfa.start_state)
            else:
                new_transition_table[key] = {nfa.start_state}
        result = NFA(new_states, new_alphabet, new_start_state, new_accept_states)
        result.transition_table = new_transition_table
        return result

    def plot(self, filename="nfa", format="pdf", view=False):
        dot = graphviz.Digraph(name=filename, format=format)
        dot.attr(rankdir="LR")
        # Dummy start node
        dot.node("start", shape="point")
        dot.edge("start", str(self.start_state))
        # Accept states
        for state in self.states:
            shape = "doublecircle" if state in self.accept_states else "circle"
            dot.node(str(state), shape=shape)
        # Transitions
        for (from_state, symbol), to_states in self.transition_table.items():
            for to_state in to_states:
                label = "ε" if symbol == '\0' else symbol
                dot.edge(str(from_state), str(to_state), label=label)
        dot.render(filename, view=view, cleanup=True)
