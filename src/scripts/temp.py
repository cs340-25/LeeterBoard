import re

# Define common words to remove for normalization.
COMMON_STOP_WORDS = {"university", "college", "institute", "school", "of", "the", "and"}

def normalize_name(name: str) -> str:
    """
    Given a university name (with trailing state info in parentheses),
    remove the state info, lowercase the text, split into tokens,
    remove common stop words, and rejoin the remaining tokens.
    If removal leaves fewer than two tokens, the full lowercased name (without state) is used.
    """
    # Remove trailing state info (anything in parentheses at the end)
    name_no_state = re.sub(r'\s*\(.*?\)$', '', name).strip()
    # Lowercase the name
    name_lower = name_no_state.lower()
    # Split into tokens
    tokens = re.split(r'\s+', name_lower)
    # Remove common stop words
    filtered_tokens = [token for token in tokens if token not in COMMON_STOP_WORDS]
    # Fallback: if too few tokens remain, use the full lowercased name
    if len(filtered_tokens) < 2:
        return name_lower
    return " ".join(filtered_tokens)

def generate_university_aliases(input_filename: str, output_filename: str):
    # Read the giant text file containing the university list.
    with open(input_filename, "r", encoding="utf-8") as infile:
        lines = infile.read().splitlines()

    uni_map = {}
    for line in lines:
        # Skip empty lines.
        if not line.strip():
            continue
        # The standard name is the line with state info removed.
        standard_name = re.sub(r'\s*\(.*?\)$', '', line).strip()
        key = normalize_name(line)
        uni_map[key] = standard_name

    # Write the mapping to the output file in Python dictionary format.
    with open(output_filename, "w", encoding="utf-8") as outfile:
        outfile.write("# Auto-generated university aliases\n")
        outfile.write("university_aliases = {\n")
        for k, v in uni_map.items():
            outfile.write(f"    {repr(k)}: {repr(v)},\n")
        outfile.write("}\n")

if __name__ == "__main__":
    # Change the file names as needed.
    input_file = "../data/all-colleges.txt"   # your giant text file
    output_file = "output.py"  # the file to generate
    generate_university_aliases(input_file, output_file)
    print(f"Generated {output_file} successfully.")
