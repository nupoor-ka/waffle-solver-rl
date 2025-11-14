#!/usr/bin/env python3
"""
waffle_generator.py

Generate "Waffle" puzzles (5x5 with the 4 inner-corner holes) such that:
 - Rows 1,3,5 (0,2,4) are valid 5-letter words (w0, w2, w4)
 - Columns a,c,e (0,2,4) are valid 5-letter words (w1, w3, w5)
 - All intersections match exactly (see code for exact constraint mapping)

Usage:
 - Put sgb-words.txt (or your words.txt) in same folder.
 - Run: python waffle_generator.py
"""

import random
import json
from collections import defaultdict

# ---- Configuration ----
WORDLIST_PATH = "words.txt"   # your sgb list (one 5-letter word per line)
OUTPUT_JSONL = "waffles.jsonl"  # saved waffles
VALID_MASK = [                   # 1 = letter cell, 0 = hole
    [1,1,1,1,1],
    [1,0,1,0,1],
    [1,1,1,1,1],
    [1,0,1,0,1],
    [1,1,1,1,1],
]

# ---- Load words ----
def load_words(path=WORDLIST_PATH):
    with open(path, "r") as fh:
        raw = [w.strip().lower() for w in fh if w.strip()]
    # Filter to only length-5 alphabetic words
    words = [w for w in raw if len(w) == 5 and w.isalpha()]
    words.sort()
    return words

# ---- Precompute positional indices for fast filtering ----
def build_pos_index(words):
    # pos_index[(pos, letter)] -> list of word indices (or words)
    pos_index = defaultdict(list)
    for w in words:
        for pos, ch in enumerate(w):
            pos_index[(pos, ch)].append(w)
    return pos_index

# ---- Candidate filtering helper ----
def candidates_with_constraints(words, pos_index, constraints, used=set()):
    """
    constraints: dict {pos:int -> letter: 'a'..'z'}
      pos is 0..4 (index in word)
    used: set of words to exclude (already selected)
    Returns a shuffled list of candidate words (strings).
    """
    if not constraints:
        cand = [w for w in words if w not in used]
        random.shuffle(cand)
        return cand

    # Start from the smallest posting list to reduce work
    posting_lists = []
    for pos, ch in constraints.items():
        posting_lists.append(pos_index.get((pos, ch), []))
    if not posting_lists:
        return []

    # Choose smallest list as base
    posting_lists.sort(key=len)
    base = posting_lists[0]
    rest = posting_lists[1:]

    result = []
    for w in base:
        if w in used:
            continue
        ok = True
        for pos, ch in constraints.items():
            if w[pos] != ch:
                ok = False
                break
        if ok:
            result.append(w)

    random.shuffle(result)
    return result

# ---- Waffle construction/backtracking ----
def build_waffle(words, pos_index, max_attempts_per_level=2000):
    """
    Attempt to build one solved waffle (6 words).
    Returns (grid, across_words, down_words) or None if failed.
    Words are lowercase strings.
    """

    used = set()

    # Step order: w0 (row0), w1 (col0), w2 (row2), w3 (col2), w4 (row4), w5 (col4)
    # Constraints (derived from intersections):
    # w1[0] == w0[0]
    # w2[0] == w1[2]
    # w3[0] == w0[2]; w3[2] == w2[2]
    # w4[0] == w1[4]; w4[2] == w3[4]
    # w5[0] == w0[4]; w5[2] == w2[4]; w5[4] == w4[4]

    # Precompute full list copy
    all_words = list(words)

    # Step 0: choose w0 randomly from all words
    w0 = random.choice(all_words)
    used.add(w0)

    # Step 1: choose w1 with w1[0] == w0[0]
    for _ in range(max_attempts_per_level):
        c1 = candidates_with_constraints(all_words, pos_index, {0: w0[0]}, used)
        if not c1:
            # cannot find any w1 given w0 — restart
            return None
        # iterate through candidates for w1 with backtracking
        for w1 in c1:
            used.add(w1)
            # Step 2: choose w2 with w2[0] == w1[2]
            c2 = candidates_with_constraints(all_words, pos_index, {0: w1[2]}, used)
            if not c2:
                used.remove(w1)
                continue

            for w2 in c2:
                used.add(w2)
                # Step 3: w3 with w3[0] == w0[2] and w3[2] == w2[2]
                c3 = candidates_with_constraints(all_words, pos_index, {0: w0[2], 2: w2[2]}, used)
                if not c3:
                    used.remove(w2)
                    continue

                for w3 in c3:
                    used.add(w3)
                    # Step 4: w4 with w4[0] == w1[4] and w4[2] == w3[4]
                    c4 = candidates_with_constraints(all_words, pos_index, {0: w1[4], 2: w3[4]}, used)
                    if not c4:
                        used.remove(w3)
                        continue

                    for w4 in c4:
                        used.add(w4)
                        # Step 5: w5 with three constraints:
                        # w5[0] == w0[4]; w5[2] == w2[4]; w5[4] == w4[4]
                        c5 = candidates_with_constraints(all_words, pos_index,
                                                         {0: w0[4], 2: w2[4], 4: w4[4]}, used)
                        if not c5:
                            used.remove(w4)
                            continue

                        # Found candidate(s) for w5; choose first (randomized within candidates)
                        w5 = c5[0]
                        used.add(w5)

                        # Success: assemble grid
                        grid = [[None]*5 for _ in range(5)]
                        # fill across rows
                        for c in range(5):
                            grid[0][c] = w0[c]
                            grid[2][c] = w2[c]
                            grid[4][c] = w4[c]
                        # fill columns (remaining cells)
                        # col0 -> w1
                        for r in range(5):
                            grid[r][0] = w1[r]
                            grid[r][2] = w3[r]
                            grid[r][4] = w5[r]
                        # grid now contains letters in all 25 positions; we will mask corners later
                        across = (w0, w2, w4)
                        down = (w1, w3, w5)
                        return grid, across, down

                    used.remove(w3)
                used.remove(w2)
            used.remove(w1)
        # if loop exhausted without returning, restart by picking a new w0
        # but here we simply return None so outer driver can retry new w0
        return None

    return None

# ---- Utilities for printing and storage ----
def grid_to_masked(grid):
    """Return 5x5 grid with '#' for holes (corners)."""
    out = []
    for r in range(5):
        row = []
        for c in range(5):
            if VALID_MASK[r][c]:
                row.append(grid[r][c])
            else:
                row.append("#")
        out.append(row)
    return out

def masked_to_flat21(masked_grid):
    """Return the 21-letter string reading row-major order skipping '#'."""
    chars = []
    for r in range(5):
        for c in range(5):
            if masked_grid[r][c] != "#":
                chars.append(masked_grid[r][c])
    return "".join(chars)

def waffle_to_example(grid, across, down):
    masked = grid_to_masked(grid)
    example = {
        "grid": masked,
        "across": list(across),
        "down": list(down),
        "flat21": masked_to_flat21(masked),
    }
    return example

def print_masked(masked_grid):
    for r in masked_grid:
        print(" ".join(ch.upper() if ch != "#" else "#" for ch in r))

# ---- RL-friendly encoders (suggestions) ----
LETTER2IDX = {c:i+1 for i,c in enumerate("abcdefghijklmnopqrstuvwxyz")}  # 0 reserved for padding/empty
IDX2LETTER = {i:c for c,i in LETTER2IDX.items()}

def encode_flat21_to_ints(flat21):
    """Return a list of 21 ints 1..26 mapping letters; useful as state input."""
    return [LETTER2IDX[ch] for ch in flat21]

def valid_cell_mask21():
    """Return boolean mask of length 21: True where cell exists (always all True here)."""
    # fixed order consistent with masked_to_flat21 reading
    mask = []
    for r in range(5):
        for c in range(5):
            if VALID_MASK[r][c]:
                mask.append(1)
    return mask  # length 21

# ---- Main generator loop ----
def generate_many(n, outpath=OUTPUT_JSONL, max_tries=100000):
    words = load_words()
    print(f"Loaded {len(words)} words.")
    pos_index = build_pos_index(words)
    examples = []
    tries = 0
    successes = 0

    with open(outpath, "w") as outf:
        while successes < n and tries < max_tries:
            tries += 1
            # keep trying until build_waffle returns a solution
            attempt = build_waffle(words, pos_index)
            if attempt is None:
                continue
            grid, across, down = attempt
            masked = grid_to_masked(grid)
            example = waffle_to_example(grid, across, down)
            outf.write(json.dumps(example) + "\n")
            successes += 1
            if successes % 10 == 0 or successes < 10:
                print(f"Saved waffle #{successes}: across={across}, down={down}")
        print(f"Done. {successes} waffles generated in {tries} tries. Output -> {outpath}")

# ---- If run directly, prompt user ----
if __name__ == "__main__":
    words = load_words()
    print(f"Wordlist size: {len(words)}")
    num_gen = input("number of waffles to generate: ")
    try:
        num_gen = int(num_gen)
    except:
        print("Please enter an integer.")
        raise SystemExit(1)

    generate_many(num_gen)