from collections import deque

# node in the graph-structured stack (gss)
class GSSNode:
    def __init__(self, label, value):
        self.label = label # the NT of the node
        self.value = value # input position where this node was created
        self.parent_edges = [] # stores parent edges

    # adds a new parent edge to track where to continue after this node completes
    def add_parent_edge(self, parent_node, production, next_index):
        # avoid duplicate edges
        if (parent_node, production, next_index) not in self.parent_edges:
            self.parent_edges.append((parent_node, production, next_index))

    # string representation
    def __repr__(self):
        return f"({self.label},{self.value})"

# graph-structured stack (gss)
class GSS:
    def __init__(self):
        self.nodes = {}
        self.get_node("$", 0) # initialize

    # retrieves existing node or creates new one
    def get_node(self, label, value):
        key = (label, value)
        if key not in self.nodes:
            # create new node if not exists
            self.nodes[key] = GSSNode(label, value)
        return self.nodes[key]

class GLLRecognizer:
    def __init__(self, grammar, start):
        self.grammar = grammar
        self.start = start
        self.gss = GSS()
        self.U = set() # set of processed states (descriptors)
        self.P = set() # set of completed parses, i.e. pops
        self.R = deque() # queue of descriptors

        # initialize parser state:
        root = self.gss.get_node("$", 0) 
        start_node = self.gss.get_node(start, 0)
        # connect root to start symbol with empty production
        start_node.add_parent_edge(root, None, 0)
        # add initial descriptor
        self.R.append((start_node, 0, None, 0))

    # main parsing function
    def recognize(self, input_str):
        n = len(input_str)
        # process all descriptors in work queue
        while self.R:
            # get next descriptor: (current node, current position, production, index in production)
            current_node, pos, prod, prod_idx = self.R.popleft()
            key_prod = tuple(prod) if prod is not None else None
            state_key = (current_node, pos, key_prod, prod_idx)
            if state_key in self.U:
                continue  # skip already processed states
            self.U.add(state_key)  # mark as processed

            if prod is not None:
                # continue processing existing production
                self._continue_production(current_node, pos, prod, prod_idx, input_str, n)
            else:
                # start processing new non-terminal: queue all its productions
                for production in self.grammar.get(current_node.label, []):
                    self.R.appendleft((current_node, pos, production, 0))

        # check if start symbol at position 0 covers entire input
        start_node_0 = self.gss.get_node(self.start, 0)
        return (start_node_0, n) in self.P

    # processes a partially completed production rule
    def _continue_production(self, node, pos, prod, idx, input_str, max_len):
        # process symbols in production until completion or mismatch
        while idx < len(prod):
            symbol = prod[idx]
            if symbol in self.grammar:  # non-terminal
                # get/create child node for this non-terminal at current position
                child_node = self.gss.get_node(symbol, pos)
                # add parent edge to remember where to continue after child completes
                child_node.add_parent_edge(node, prod, idx + 1)
                
                # check if child already has completions
                for (n, end_pos) in self.P:
                    if n == child_node:
                        self.R.append((node, end_pos, prod, idx + 1))
                
                # prepare descriptor for child processing
                child_state = (child_node, pos, None, 0)
                if child_state not in self.U:
                    # queue child for processing if not already done
                    self.R.appendleft(child_state)
                return  # stop current production after queueing child
            
            else:  # terminal symbol or epsilon
                if symbol == "":  # epsilon production
                    idx += 1 
                elif pos < max_len and input_str[pos] == symbol: # terminal matches input 
                    pos += 1
                    idx += 1
                else: 
                    return  
        # entire production matched successfully
        if (node, pos) not in self.P:
            self.P.add((node, pos))
            # schedule parent to continue after this non-terminal
            for parent_node, prod, next_idx in node.parent_edges:
                self.R.append((parent_node, pos, prod, next_idx))

    def print_gss(self):
        print("Graph-Structured Stack (GSS):")
        for key, node in self.gss.nodes.items():
            print(f"Node {node}:")
            for parent, prod, next_idx in node.parent_edges:
                # format production for display
                prod_str = 'ε' if prod is None else ''.join(prod)
                print(f"  <- Parent: {parent} via prod: {prod_str}[{next_idx}]")