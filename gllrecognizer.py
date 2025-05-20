from collections import deque

# node in graph-structured stack (gss) representing parser states
class GSSNode:
    def __init__(self, label, value):
        self.label = label    # non-terminal symbol this node represents
        self.value = value   # input position where node was created
        self.edges = []      # successor nodes in the gss
        self.parents = []    # predecessor nodes in the gss

    # connect nodes bidirectionally to form graph structure
    def add_edge(self, node):
        if node not in self.edges:
            self.edges.append(node)
            node.parents.append(self)

    # display format for debugging
    def __repr__(self):
        return f"({self.label},{self.value})"

# manages creation and storage of gss nodes
class GSS:
    def __init__(self):
        self.nodes = {}
        self.get_node("$", 0)  # initialize root node

    # retrieve or create node with specific label/position combination
    def get_node(self, label, value):
        key = (label, value)
        if key not in self.nodes:
            self.nodes[key] = GSSNode(label, value)
        return self.nodes[key]

# core recognizer implementing gll algorithm
class GLLRecognizer:
    def __init__(self, grammar, start):
        self.grammar = grammar  # parsing rules in cfg format
        self.start = start      # root non-terminal to recognize
        self.gss = GSS()        # graph-structured stack storage
        self.U = set()          # tracked descriptors to prevent reprocessing
        self.P = set()          # successful parse completions (node, end_pos)
        self.R = deque()        # work queue for pending operations
        self.debug = False      # toggle detailed output logging

        # seed parser with initial state: start symbol at position 0
        root = self.gss.get_node("$", 0)
        start_node = self.gss.get_node(start, 0)
        root.add_edge(start_node)
        self.R.append((start_node, 0, None, 0))  # (node, pos, prod, prod_idx)

    # main recognition driver for input string
    def recognize(self, input):
        n = len(input)
        while self.R:
            # extract next processing task from work queue
            current_node, pos, prod, prod_idx = self.R.popleft()

            # handle mid-production processing continuation
            if prod is not None:
                self._continue_production(
                    current_node, pos, prod, prod_idx, input, n
                )
                continue

            # prevent redundant processing of same state
            state_key = (current_node.label, current_node.value, pos, None, 0)
            if state_key in self.U:
                continue
            self.U.add(state_key)

            # queue all alternative productions for current non-terminal
            for production in self.grammar.get(current_node.label, []):
                self.R.appendleft((current_node, pos, production, 0))

        # successful parse if start symbol covers full input length
        return any((node, n) in self.P 
               for node in self.gss.nodes.values() 
               if node.label == self.start)

    # processes partial productions from work queue
    def _continue_production(self, node, pos, prod, idx, input, max_len):
        while idx < len(prod):
            symbol = prod[idx]
            
            # handle non-terminal symbols
            if symbol in self.grammar:
                # create new parser state node
                child_node = self.gss.get_node(symbol, pos)
                node.add_edge(child_node)

                # schedule processing of non-terminal's productions
                child_state = (child_node.label, child_node.value, pos, None, 0)
                if child_state not in self.U:
                    self.R.appendleft((child_node, pos, None, 0))

                # queue continuation after processing this non-terminal
                self.R.appendleft((node, pos, prod, idx + 1))
                return

            # handle terminal symbols
            else:
                # match terminal against input stream
                if pos < max_len and input[pos] == symbol:
                    pos += 1
                    idx += 1
                # handle empty productions (epsilon)
                elif symbol == "":
                    idx += 1
                # abort on mismatch
                else:
                    return

        # full production matched - record completion
        if (node, pos) not in self.P:
            self.P.add((node, pos))
            # propagate success to parent states
            for parent in node.parents:
                self.R.append((parent, pos, None, 0))

    # diagnostic display of gss structure
    def print_gss(self):
        print("graph-structured stack (gss):")
        root = self.gss.get_node("$", 0)
        print(f"root node: {root}")
        for (label, value), node in self.gss.nodes.items():
            if label == "$" and value == 0: continue
            edges = ", ".join([f"({w.label},{w.value})" for w in node.edges])
            parents = ", ".join([f"({p.label},{p.value})" for p in node.parents])
            print(f"node ({label},{value})")
            print(f"  edges   -> {edges}")
            print(f"  parents <- {parents}")

# test grammars and validation cases follow below...
# S -> A S d | B S | epsilon
# A -> a | c
# B -> a | b
gamma0 = {
    "S": [["A", "S", "d"], ["B", "S"], []],
    "A": [["a"], ["c"]],
    "B": [["a"], ["b"]]
}

# S -> C a | d 
# B -> epsilon | a
# C -> b | B C b | b b
gamma1 = {
    "S": [["C", "a"], ["d"]],
    "B": [[], ["a"]],
    "C": [["b"], ["B", "C", "b"], ["b", "b"]]
}

# S -> b | S S | S S S
gamma2 = {
    "S": [["b"], ["S", "S"], ["S", "S", "S"]]
}

input_str = "abbba"

# gamma0 test
input_str = "aad"
recognizer = GLLRecognizer(gamma0, 'S')
print(recognizer.recognize(input_str))  # True
# recognizer.print_gss()

# gamma1 test
input_str = "a" * 20 + "b" * 150 + "a"
recognizer = GLLRecognizer(gamma1, 'S')
print(recognizer.recognize(input_str))  # True
# recognizer.print_gss()

# Test gamma2 with "bb"
input_str = "b" * 300
recognizer = GLLRecognizer(gamma2, 'S')
print(recognizer.recognize(input_str))  # True
# recognizer.print_gss()

