import json
import random

INPUT_FILE = "waffles.jsonl"               
OUTPUT_FILE = "waffles_shuffled.jsonl" 
fixed_number=5
def shuffler(flat21, fixed_count=fixed_number):
    
    indices = list(range(len(flat21)))
    fixed_positions = set(random.sample(indices, fixed_count))
    fixed_map={}
    to_shuffle=[]
    for i in fixed_positions:
        fixed_map[i]=flat21[i]
    for i in indices:
        if i not in fixed_map:
            to_shuffle.append(flat21[i])
    
    random.shuffle(to_shuffle)

    shuffled = []
    shuffled_ind = 0
    for i in indices:
        if i in fixed_positions:
            shuffled.append(flat21[i])
        else:
            shuffled.append(to_shuffle[shuffled_ind])
            shuffled_ind += 1

    shuffled_str = "".join(shuffled)

    # To counter if the shuffle makes solved puzzle
    if shuffled_str == flat21:
        random.shuffle(to_shuffle)
        shuffled = []
        shuffled_ind = 0
        for i in indices:
            if i in fixed_positions:
                shuffled.append(flat21[i])
            else:
                shuffled.append(to_shuffle[shuffled_ind])
                shuffled_ind += 1
        shuffled_str = "".join(shuffled)

    return shuffled_str, sorted(list(fixed_positions))


def main():
    with open(INPUT_FILE, "r") as f:
        puzzles = [json.loads(line) for line in f]

    print(f"Loaded {len(puzzles)} solved waffles from {INPUT_FILE}")

    with open(OUTPUT_FILE, "w") as f_out:
        for i, p in enumerate(puzzles, 1):
            target_flat = p["flat21"]
            shuffled_flat, fixed_positions = shuffler(target_flat)
            entry = {
                "target_flat21": target_flat,
                "shuffled_flat21": shuffled_flat,
                "fixed_indices": fixed_positions,  # optional: to analyze later
                "target_grid": p["grid"]
            }
            f_out.write(json.dumps(entry) + "\n")

            if i <= 3:
                print(f"\nWaffle #{i}")
                print(f" Target:   {target_flat}")
                print(f" Shuffled: {shuffled_flat}")
                print(f" Fixed positions: {fixed_positions}")

    print(f"\nSaved shuffled puzzles to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()