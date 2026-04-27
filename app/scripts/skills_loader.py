import os
import logging

from app.scripts.service_reg import load_yaml_frontmatter, load_md_body

logger = logging.getLogger(__name__)

SKILLS_DIR = os.path.join(os.path.dirname(__file__), '..', 'skills')
IGNORED_FOLDERS = {'scripts'}


def load_skills() -> dict[str, dict]:
    """
    Scan the app/skills directory and return a dictionary of all available skills.

    Each skill is identified either by a subfolder containing a SKILL.md file,
    or by a standalone .md file in the skills root directory.
    The 'scripts' folder is ignored.

    Returns:
        dict[str, dict]: Mapping of skill name to a dict with keys:
            - description (str)
            - content (str): The markdown body (excluding frontmatter)
            - scripts (list[str]): List of script signatures from metadata
    """
    skills = {}
    skills_dir = os.path.normpath(SKILLS_DIR)

    if not os.path.isdir(skills_dir):
        logger.error(f"Skills directory not found: {skills_dir}")
        return skills

    for entry in os.listdir(skills_dir):
        if entry in IGNORED_FOLDERS:
            continue

        entry_path = os.path.join(skills_dir, entry)

        if os.path.isdir(entry_path):
            skill_file = os.path.join(entry_path, 'SKILL.md')
            if not os.path.isfile(skill_file):
                logger.warning(f"No SKILL.md found in skill folder: {entry_path}")
                continue
            skill = _parse_skill_file(skill_file)
            if skill:
                skills[skill['name']] = skill

        elif entry.endswith('.md'):
            skill = _parse_skill_file(entry_path)
            if skill:
                skills[skill['name']] = skill

    logger.info(f"Loaded {len(skills)} skill(s): {list(skills.keys())}")
    return skills


def _parse_skill_file(md_path: str) -> dict | None:
    """
    Parse a single skill markdown file and extract its metadata and body.

    Args:
        md_path (str): Absolute path to the markdown skill file.

    Returns:
        dict | None: A dict with name, description, content, and scripts,
                     or None if the file has no valid frontmatter.
    """
    frontmatter = load_yaml_frontmatter(md_path)
    if not frontmatter or not isinstance(frontmatter, dict):
        logger.warning(f"Skipping skill file with missing/invalid frontmatter: {md_path}")
        return None

    name = frontmatter.get('name')
    if not name:
        logger.warning(f"Skipping skill file without a name: {md_path}")
        return None

    description = frontmatter.get('description', '')
    metadata = frontmatter.get('metadata', {}) or {}
    scripts = metadata.get('scripts', []) or []
    content = load_md_body(md_path)

    return {
        'name': name,
        'description': description,
        'content': content,
        'scripts': scripts,
    }
