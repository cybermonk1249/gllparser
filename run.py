import sys
from typing import List, Tuple, Dict
from gllrecognizer import GLLRecognizer

def grammar_to_dict(grammar_str: str) -> dict[str, list[list[str]]]:
    grammar: dict[str, list[list[str]]] = {}

    # Split into non-empty lines and process each one independently
    for line in filter(None, (ln.strip() for ln in grammar_str.strip().splitlines())):
        if "->" not in line:
            raise ValueError(f"Invalid rule (missing '->'): {line}")

        left, right = (part.strip() for part in line.split("->", 1))
        if not left.isalpha() or not left.isupper():
            raise ValueError(f"Left side must be a single non-terminal (capital letters): {left}")

        productions = []
        for prod in right.split("|"):
            # Remove repeated whitespace, split by spaces, and keep epsilon (empty) if desired
            symbols = prod.strip().split()
            productions.append(symbols if symbols else [])  # "" can denote ε

        grammar[left] = productions

    return grammar

def read_file(fname: str) -> Tuple[str, List[Tuple[str, int]]]:
    with open(fname, "r", encoding="utf-8") as fh:
        content = fh.read().splitlines()

    # split at first blank line
    try:
        blank_idx = content.index("")
    except ValueError:
        raise ValueError("Input file must contain a blank line separating grammar and words.")

    grammar_part = "\n".join(content[:blank_idx])
    words_part = content[blank_idx + 1 :]

    word_label_pairs: List[Tuple[str, int]] = []
    for line in filter(None, (ln.strip() for ln in words_part)):
        try:
            word, label = line.rsplit(maxsplit=1)
            word_label_pairs.append((word, int(label)))
        except ValueError:
            raise ValueError(f"Invalid word/label line: {line}")

    return grammar_part, word_label_pairs

def main(path: str):
    grammar_txt, pairs = read_file(path)
    grammar = grammar_to_dict(grammar_txt)
    # recognizer = GLLRecognizer(grammar, 'S')

    passed = 0

    print("\n=============== Test Cases ===============")
    print("  WORD".ljust(20), "EXPECTED", "ACTUAL", "OK?")
    print("-" * 40)
    for word, exp in pairs:
        recognizer = GLLRecognizer(grammar, 'S')
        ok = recognizer.recognize(word)
        outcome = 1 if ok else 0
        if outcome == exp:
            match = "Y"
            passed += 1
        else:
            match = "N"
        print(word.ljust(20), exp, "       ", outcome, "    ", match)

    print("\n=============== Summary ===============")
    print(f"Passed {passed}/{len(pairs)} tests")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 run.py <input_file>")
        sys.exit(1)
    main(sys.argv[1])