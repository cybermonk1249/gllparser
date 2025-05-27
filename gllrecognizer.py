from functools import lru_cache

class GLLRecognizer:
    def __init__(self, grammar: dict[str, list[list[str]]], start: str):
        self.G = grammar
        self.start = start

    def recognize(self, inp: str) -> bool:
        n = len(inp)
        G = self.G
        active = set()

        @lru_cache(maxsize=None)
        def match_seq(prod: tuple[str, ...], i: int, j: int) -> bool:
            if not prod:
                return i == j
            if len(prod) == 1:
                sym = prod[0]
                if sym in G:
                    return can(sym, i, j)
                return (i + 1 == j) and i < n and inp[i] == sym
            first, *rest = prod
            for k in range(i, j + 1):
                if first in G:
                    if not can(first, i, k):
                        continue
                else:
                    if not (i + 1 == k and i < n and inp[i] == first):
                        continue
                if match_seq(tuple(rest), k, j):
                    return True
            return False

        @lru_cache(maxsize=None)
        def can(nt: str, i: int, j: int) -> bool:
            # guard against left recursion
            if (nt, i, j) in active:
                return False
            active.add((nt, i, j))
            for prod in G.get(nt, []):
                if match_seq(tuple(prod), i, j):
                    active.remove((nt, i, j))
                    return True
            active.remove((nt, i, j))
            return False

        return can(self.start, 0, n)