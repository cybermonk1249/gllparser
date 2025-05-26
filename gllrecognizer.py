#!/usr/bin/env python3
import sys
from functools import lru_cache

def grammar_to_dict(text: str) -> dict[str, list[list[str]]]:
    """
    Convert a multiline CFG (e.g.
        S -> a B c | ε
        B -> b | 
    ) into a dict:
        { 'S': [['a','B','c'], []], 'B': [['b'], []] }
    An empty RHS (“ε”) is stored as [].
    """
    G = {}
    for line in filter(None, (ln.strip() for ln in text.splitlines())):
        if "->" not in line:
            raise ValueError(f"Invalid rule (missing '->'): {line}")
        lhs, rhs = (part.strip() for part in line.split("->", 1))
        # split alternatives on '|'
        prods = []
        for alt in rhs.split("|"):
            symbols = alt.strip().split()
            prods.append(symbols if symbols else [])  # [] = ε
        G[lhs] = prods
    return G

def read_file(path: str):
    """
    Reads <path>, splits at the first blank line:
      - The first block is the grammar,
      - after the blank, each line is “word label” (label 0 or 1).
    Returns (grammar_text, list[(word,int)]).
    """
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    # find first truly blank line
    sep = next(
        (i for i, ln in enumerate(lines) if ln.strip()==""), 
        None
    )
    if sep is None:
        raise ValueError("Need a blank line separating grammar and tests.")
    grammar_txt = "\n".join(lines[:sep])
    pairs = []
    for ln in lines[sep+1:]:
        ln = ln.strip()
        if not ln: 
            continue
        w, lbl = ln.rsplit(maxsplit=1)
        pairs.append((w, int(lbl)))
    return grammar_txt, pairs

class GLLRecognizer:
    """
    Top-down, recursive CFG recogniser with:
      • match_seq(prod,i,j): can prod list match inp[i:j]?
      • can(nt,i,j): can nonterminal nt generate inp[i:j]?
    Uses lru_cache and 'active' sets to break left recursion cycles.
    """
    def __init__(self, grammar: dict[str, list[list[str]]], start: str):
        self.G     = grammar
        self.start = start

    def recognize(self, inp: str) -> bool:
        n = len(inp)
        G = self.G

        # to break infinite loops on left recursion:
        active_can = set()  

        @lru_cache(maxsize=None)
        def match_seq(prod: tuple[str,...], i: int, j: int) -> bool:
            """
            prod is a tuple of symbols (each either a terminal string or a non-terminal key).
            Return True iff prod matches exactly inp[i:j].
            """
            # 1) Empty production ⇒ matches only empty substring
            if len(prod) == 0:
                return i == j

            # 2) Single‐symbol shortcut
            if len(prod) == 1:
                sym = prod[0]
                if sym in G:
                    # nonterminal ⇒ delegate to can()
                    return can(sym, i, j)
                # terminal ⇒ must exactly match one char
                return (i + 1 == j) and (i < n) and (inp[i] == sym)

            # 3) General case: split [i:j] into two parts at k, 
            #    first symbol ↔ inp[i:k], rest ↔ inp[k:j]
            first, *rest = prod
            for k in range(i, j+1):
                # match 'first' on inp[i:k]
                if first in G:
                    if not can(first, i, k):
                        continue
                else:
                    if not (i+1 == k and i < n and inp[i] == first):
                        continue
                # if that succeeded, match the remainder
                if match_seq(tuple(rest), k, j):
                    return True
            return False

        @lru_cache(maxsize=None)
        def can(nt: str, i: int, j: int) -> bool:
            """
            Return True iff nonterminal `nt` can generate exactly inp[i:j].
            We guard against left‐recursion by tracking 'active' calls.
            """
            # cycle‐break: if we're already trying can(nt,i,j), give up
            if (nt, i, j) in active_can:
                return False
            active_can.add((nt, i, j))

            # try every production of nt
            for prod in G.get(nt, []):
                if match_seq(tuple(prod), i, j):
                    active_can.remove((nt, i, j))
                    return True

            active_can.remove((nt, i, j))
            return False

        # start must cover the full string
        return can(self.start, 0, n)