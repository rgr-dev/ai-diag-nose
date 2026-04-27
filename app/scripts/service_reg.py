import os
import re
import yaml
import logging

logger = logging.getLogger(__name__)


def load_project_info_content(project_name: str, description_file: str = "README.md") -> str:
    """
    Load project information from a given path. This function can be extended to read specific files like README.md, service configuration files, etc.

    Args:
        project_name (str): The name of the project directory.

        description_file (str): The name of the file containing the project description. Defaults to "README.md".
    Returns:
        str: A string containing the loaded project information.
    """
    dest_dir = os.getenv("GIT_REPOS_PATH", "/workspace/git_repos")
    description_path = os.path.join(dest_dir, project_name, description_file)
    logger.info(f"Loading project information from {description_path}...")
    if os.path.exists(description_path):
        with open(description_path, 'r') as f:
            return f.read()
    else:
        # here find similar files by name (ignoring extension and case) and show then in a log message
        dir_path = os.path.join(dest_dir, project_name)
        if os.path.exists(dir_path):
            similar_files = [file for file in os.listdir(dir_path) if file.lower().startswith(description_file.split('.')[0].lower())]
            if similar_files:
                error_msg = f"Found similar files for {description_file}: {', '.join(similar_files)}"
                logger.warning(error_msg)
                return error_msg
    error_msg = f"No {description_file} found for project {project_name}. Please provide project information."
    logger.error(error_msg)
    return error_msg


def load_services_dict(manifest_path) -> dict[str, dict]:
    """
    Load a YAML manifest of services and return a dictionary mapping service names to their attribute dictionaries.

    Args:
        manifest_path (str): Path to the YAML file containing the services manifest.

    Returns:
        dict[str, dict]: A dictionary where each key is a service name and each value is a dict of that service's attributes.
    """
    with open(manifest_path, 'r') as f:
        data = yaml.safe_load(f)
    services = {}
    for svc in data.get('services', []):
        name = svc.get('name')
        if not name:
            continue
        # Copy all attributes except 'name' into the value dict
        attr = {k: v for k, v in svc.items() if k != 'name'}
        services[name] = attr
    return services


def load_service_troubleshooting_info(project_name: str, troubleshooting_file: str = "troubleshooting-skill.md") -> str:
    """
    Load troubleshooting information for a given project. This can include recent git activity, error logs, and project description.

    Args:
        project_name (str): The name of the project directory.

        troubleshooting_file (str): The name of the file containing the troubleshooting information. Defaults to "troubleshooting-skill".

    Returns:
        str: A string containing the loaded troubleshooting information.
    """
    dest_dir = os.getenv("GIT_REPOS_PATH", "/workspace/git_repos")
    description_path = os.path.join(dest_dir, project_name, troubleshooting_file)
    frontmatter = load_yaml_frontmatter(description_path)
    return load_md_body(description_path)



def load_yaml_frontmatter(md_path):
    """
    Loads YAML frontmatter from a markdown file and returns it as a dict.
    """
    if not os.path.exists(md_path):
        logger.warning(f"Troubleshooting file not found: {md_path}")
        return ""  
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Match YAML frontmatter: starts with --- on its own line, ends with ---
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return None
    yaml_str = match.group(1)
    return yaml.safe_load(yaml_str)


def load_md_body(md_path: str) -> str:
    """
    Loads the content of a markdown file excluding the YAML frontmatter.

    Args:
        md_path (str): Path to the markdown file.

    Returns:
        str: The markdown body after the frontmatter, or empty string if the file
             doesn't exist or has no body content.
    """
    if not os.path.exists(md_path):
        logger.warning(f"Markdown file not found: {md_path}")
        return ""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.match(r'^---\s*\n.*?\n---\s*\n?', content, re.DOTALL)
    body = content[match.end():] if match else content
    if not body.strip():
        logger.warning(f"No body content found in: {md_path}")
        return ""
    return body

