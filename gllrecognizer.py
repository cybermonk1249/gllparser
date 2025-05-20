from collections import deque

class GSSNode:
    def __init__(self, label, value):
        self.label = label
        self.value = value
        self.edges = []
        self.parents = []

    def add_edge(self, node):
        if node not in self.edges:
            self.edges.append(node)
            node.parents.append(self)

    def __repr__(self):
        return f"({self.label},{self.value})"

class GSS:
    def __init__(self):
        self.nodes = {}
        self.get_node("$", 0)  # EOS root node

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
        
        # Initialize with start symbol connected to EOS root
        eos_root = self.gss.get_node("$", 0)
        start_node = self.gss.get_node(start, 0)
        eos_root.add_edge(start_node)
        self.R.append((start_node, 0))

    def recognize(self, input):
        n = len(input)
        while self.R:
            u, i = self.R.popleft()
            
            if (u.label, u.value, i) in self.U:
                continue
            self.U.add((u.label, u.value, i))

            for prod in self.grammar.get(u.label, []):
                self.process_production(u, i, prod, input, n)

        
        # Look for any start symbol node reaching end position
        return any((node, n) in self.P 
            for node in self.gss.nodes.values() 
            if node.label == self.start)

    def process_production(self, u, i, prod, input, max_len):
        stack = [(u, i, 0, set())]  # Use set for path tracking
            
        while stack:
            current_node, current_pos, prod_idx, path = stack.pop()
            
            if prod_idx == len(prod):
                if (current_node, current_pos) not in self.P:
                    self.P.add((current_node, current_pos))
                    for parent in current_node.parents:
                        self.R.append((parent, current_pos))
                continue

            sym = prod[prod_idx]
            if sym in self.grammar:
                new_node = self.gss.get_node(sym, current_pos)
                current_node.add_edge(new_node)
                
                # Prevent direct left recursion cycles
                if (sym, current_pos) in path:
                    continue
                    
                if (sym, current_pos, current_pos) not in self.U:
                    self.R.append((new_node, current_pos))
                
                # Pass path as new set to avoid mutation issues
                new_path = path.copy()
                new_path.add((sym, current_pos))
                stack.append((current_node, current_pos, prod_idx + 1, new_path))
                
                if [] in self.grammar[sym]:
                    stack.append((new_node, current_pos, 0, new_path))
            else:
                if current_pos < max_len and input[current_pos] == sym:
                    stack.append((current_node, current_pos + 1, prod_idx + 1, path))
                elif sym == "":
                    stack.append((current_node, current_pos, prod_idx + 1, path))

    def print_gss(self):
        print("Graph-Structured Stack (GSS):")
        eos_root = self.gss.get_node("$", 0)
        print(f"Root Node: {eos_root}")
        for (label, value), node in self.gss.nodes.items():
            if label == "$" and value == 0: continue
            edges = ", ".join([f"({w.label},{w.value})" for w in node.edges])
            parents = ", ".join([f"({p.label},{p.value})" for p in node.parents])
            print(f"Node ({label},{value})")
            print(f"  Edges   -> {edges}")
            print(f"  Parents <- {parents}")


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
input_str = "abbba"
recognizer = GLLRecognizer(gamma1, 'S')
print(recognizer.recognize(input_str))  # True
# recognizer.print_gss()

# Test gamma2 with "bb"
input_str = "bb"
recognizer = GLLRecognizer(gamma2, 'S')
print(recognizer.recognize(input_str))  # True
recognizer.print_gss()

