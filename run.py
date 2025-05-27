import sys
import glob
from typing import List, Tuple
from gllrecognizer import GLLRecognizer

def grammar_to_dict(grammar_str: str) -> dict[str, list[list[str]]]:
    grammar: dict[str, list[list[str]]] = {}

    for line in filter(None, (ln.strip() for ln in grammar_str.strip().splitlines())):
        if "->" not in line:
            raise ValueError(f"Invalid rule (missing '->'): {line}")

        left, right = (part.strip() for part in line.split("->", 1))
        if not left.isalpha() or not left.isupper():
            raise ValueError(f"Left side must be a single non-terminal (capital letters): {left}")

        productions = []
        for prod in right.split("|"):
            symbols = prod.strip().split()
            productions.append(symbols if symbols else [])

        grammar[left] = productions

    return grammar

def read_file(fname: str) -> Tuple[str, List[Tuple[str, int]]]:
    with open(fname, "r", encoding="utf-8") as fh:
        content = fh.read().splitlines()

    try:
        blank_idx = content.index("")
    except ValueError:
        raise ValueError("Input file must contain a blank line separating grammar and words.")

    grammar_part = "\n".join(content[:blank_idx])
    words_part = content[blank_idx + 1 :]

    word_label_pairs: List[Tuple[str, int]] = []
    for raw in words_part:
        if raw == "":
            continue
        parts = raw.rsplit(None, 1)
        if len(parts) == 1:
            word = ""
            label = parts[0]
        else:
            word, label = parts
        word_label_pairs.append((word, int(label)))

    return grammar_part, word_label_pairs

def truncate(s: str, width: int = 20) -> str:
    if len(s) <= width:
        return s
    return s[: width - 3] + "..."

def main(path: str, verbose: bool = False) -> bool:
    grammar_txt, pairs = read_file(path)
    grammar = grammar_to_dict(grammar_txt)
    passed = 0

    if verbose:
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
        if verbose:
            print(truncate(word, 20).ljust(20), exp, "       ", outcome, "    ", match)
    if verbose:
        print("\n=============== Summary ===============")
        print(f"Passed {passed}/{len(pairs)} tests")
    return len(pairs) == passed

if __name__ == "__main__":
    if len(sys.argv) == 1:
        files = sorted(glob.glob("test-*.txt"))
        if not files:
            print("No test files found...")
            sys.exit(1)
        n_passed = 0
        for f in files:
            if main(f):
                n_passed += 1
            else:
                print("Failed on " + f + "!")
        if n_passed == len(files):
            print("SUCCESS! Passed every testfile... :)")
    elif len(sys.argv) == 2:
        main(sys.argv[1], True)
    else:
        print("Usage:")
        print("  python3 run.py         # runs all test-*.txt in here")
        print("  python3 run.py file.txt  # runs only file.txt")
        sys.exit(1)