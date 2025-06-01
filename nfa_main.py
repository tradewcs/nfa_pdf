from NFA import *

nfa1 = NFA((1, 2, 3), ('a', 'b', 'c'), 1, (2,))

nfa1.add_transition(1, 'a', (2, 3))
nfa1.add_transition(2, 'b', (3,))
nfa1.add_transition(3, 'c', (3,))


nfa2 = NFA((11, 12), ('a', 'b', 'c'), 11, (12,))

nfa2.add_transition(11, 'a', (12,))
nfa2.add_transition(12, 'c', (12,))



res = NFA.concatenation(nfa1, nfa2)

res.plot()
