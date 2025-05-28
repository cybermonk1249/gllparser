from collections import deque

class GSSNode:
    def __init__(self, label, value):
        self.label = label
        self.value = value
        self.parent_edges = []  # tuples: (parent_node, production, next_index)

    def add_parent_edge(self, parent_node, production, next_index):
        if (parent_node, production, next_index) not in self.parent_edges:
            self.parent_edges.append((parent_node, production, next_index))

    def __repr__(self):
        return f"({self.label},{self.value})"

class GSS:
    def __init__(self):
        self.nodes = {}
        self.get_node("$", 0)  # initialize root node

    def get_node(self, label, value):
        key = (label, value)
        if key not in self.nodes:
            self.nodes[key] = GSSNode(label, value)
        return self.nodes[key]

class GLLRecognizer:
    def __init__(self, grammar, start):
        self.grammar = grammar
        self.start = start
        self.gss = GSS()
        self.U = set()
        self.P = set()
        self.R = deque()
        self.debug = False

        root = self.gss.get_node("$", 0)
        start_node = self.gss.get_node(start, 0)
        # initialize add parent edge for initial node (root calls start symbol)
        start_node.add_parent_edge(root, None, 0)
        self.R.append((start_node, 0, None, 0))

    def recognize(self, input_str):
        n = len(input_str)
        while self.R:
            current_node, pos, prod, prod_idx = self.R.popleft()
            
            # convert production to tuple 
            key_prod = tuple(prod) if prod is not None else None
            state_key = (current_node, pos, key_prod, prod_idx)
            if state_key in self.U:
                continue
            self.U.add(state_key)

            if prod is not None:
                self._continue_production(current_node, pos, prod, prod_idx, input_str, n)
            else:
                for production in self.grammar.get(current_node.label, []):
                    self.R.appendleft((current_node, pos, production, 0))

        start_node_0 = self.gss.get_node(self.start, 0)
        # print(f'\n start_node_0 is: {start_node_0}')
        # print(f'n is: {n}')
        return (start_node_0, n) in self.P
        # return any(node.label == self.start and (node, n) in self.P 
        #           for node in self.gss.nodes.values())

    def _continue_production(self, node, pos, prod, idx, input_str, max_len):
        while idx < len(prod):
            symbol = prod[idx]
            if symbol in self.grammar:  # Non-terminal

                child_node = self.gss.get_node(symbol, pos)
                child_node.add_parent_edge(node, prod, idx + 1)
                
                
                for (n, end_pos) in self.P:
                    if n == child_node:
                        self.R.append((node, end_pos, prod, idx + 1))

                child_state = (child_node, pos, None, 0)
                if child_state not in self.U:
                    self.R.appendleft(child_state)
                    return
                child_state = (child_node, pos, None, 0)
                if child_state not in self.U:
                    self.R.appendleft(child_state)
                return  # stop processing after queueing non-terminal
            else:  # terminal or epsilon
                if symbol == "":  # handle epsilon
                    idx += 1
                elif pos < max_len and input_str[pos] == symbol:
                    pos += 1
                    idx += 1
                else:  # terminal mismatch
                    return
        
        # entire production matched
        if (node, pos) not in self.P:
            self.P.add((node, pos))
            for parent_node, prod, next_idx in node.parent_edges:
                self.R.append((parent_node, pos, prod, next_idx))

    def print_gss(self):
        print("Graph-Structured Stack (GSS):")
        for key, node in self.gss.nodes.items():
            print(f"Node {node}:")
            for parent, prod, next_idx in node.parent_edges:
                prod_str = 'ε' if prod is None else ''.join(prod)
                print(f"  <- Parent: {parent} via prod: {prod_str}[{next_idx}]")


# S -> A S d | B S | epsilon
# A -> a | c
# B -> a | b
# gamma0 = {
#     "S": [["A", "S", "d"], ["B", "S"], []],
#     "A": [["a"], ["c"]],
#     "B": [["a"], ["b"]]
# }

# input_str = "ad"

# # Test gamma0 with "ad"
# recognizer = GLLRecognizer(gamma0, 'S')
# print(recognizer.recognize(input_str)) 
# recognizer.print_gss()
# print(recognizer.P)