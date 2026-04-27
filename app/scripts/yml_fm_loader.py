import sys
import yaml
import re

def load_yaml_frontmatter(md_path):
    """
    Loads YAML frontmatter from a markdown file and returns it as a dict.
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Match YAML frontmatter: starts with --- on its own line, ends with ---
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return None
    yaml_str = match.group(1)
    return yaml.safe_load(yaml_str)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python read_frontmatter.py <markdown_file.md>")
        sys.exit(1)
    md_file = sys.argv[1]
    frontmatter = load_yaml_frontmatter(md_file)
    if frontmatter is None:
        print("No YAML frontmatter found.")
    else:
        print(frontmatter)