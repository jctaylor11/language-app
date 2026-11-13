import argparse
import ast
import os

GENERATOR_PATH = "backend/db/seed/build_word_glosses.py"
ROUNDS_DIRECTORY = "backend/evals/word_glosses/rounds"


def read_system_prompt() -> str:
    """Parses the generator's source rather than importing it, since importing creates an Anthropic client."""
    with open(GENERATOR_PATH, "r", encoding="utf-8") as generator_file:
        generator_source = generator_file.read()

    syntax_tree = ast.parse(generator_source)
    for node in syntax_tree.body:
        if isinstance(node, ast.Assign) is False:
            continue
        if node.targets[0].id == "SYSTEM_PROMPT":
            system_prompt = ast.literal_eval(node.value)
            return system_prompt

    raise ValueError(f"SYSTEM_PROMPT not found in {GENERATOR_PATH}")


def snapshot_prompt(round_number: int) -> str:
    snapshot_path = f"{ROUNDS_DIRECTORY}/round_{round_number:02d}_prompt.txt"
    if os.path.exists(snapshot_path):       # Snapshots are the only record of each round's prompt
        raise FileExistsError(f"{snapshot_path} already exists")

    system_prompt = read_system_prompt()
    os.makedirs(ROUNDS_DIRECTORY, exist_ok=True)
    with open(snapshot_path, "w", encoding="utf-8") as snapshot_file:
        snapshot_file.write(system_prompt)

    return snapshot_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save the generator's current SYSTEM_PROMPT as a round's snapshot")
    parser.add_argument("round_number", type=int)
    arguments = parser.parse_args()

    snapshot_path = snapshot_prompt(arguments.round_number)
    print(f"Saved {snapshot_path}")
