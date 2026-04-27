import hashlib
import importlib.util
import inspect
import logging
import os

try:
    from langchain_core.tools import StructuredTool, Tool
except ImportError:  # Fallback for older langchain versions
    from langchain.tools import StructuredTool, Tool

logger = logging.getLogger(__name__)

DEFAULT_SKILLS_SCRIPTS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "skills", "scripts")
)


def _resolve_skills_scripts_dir() -> str:
    env_value = os.getenv("SKILLS_SCRIPTS_DIR", "").strip()
    if not env_value:
        return DEFAULT_SKILLS_SCRIPTS_DIR

    expanded = os.path.expandvars(os.path.expanduser(env_value))
    return os.path.normpath(expanded)


def _module_prefix_for_dir(skills_dir: str) -> str:
    repo_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
    abs_skills_dir = os.path.abspath(skills_dir)
    abs_repo_root = os.path.abspath(repo_root)

    try:
        if os.path.commonpath([abs_skills_dir, abs_repo_root]) == abs_repo_root:
            rel_path = os.path.relpath(abs_skills_dir, abs_repo_root)
            rel_path = rel_path.replace(os.sep, ".").strip(".")
            if rel_path:
                return rel_path
    except ValueError:
        pass

    digest = hashlib.md5(abs_skills_dir.encode("utf-8")).hexdigest()[:8]
    return f"skills_scripts_{digest}"


def load_tools(function_names: list[str]) -> list[Tool]:
    """Build Tool instances from functions in app/skills/scripts.

    Args:
        function_names: List of function names to load.

    Returns:
        A list of Tool instances for the functions found.
    """
    if not function_names:
        return []

    skills_dir = _resolve_skills_scripts_dir()
    if not os.path.isdir(skills_dir):
        logger.error("Skills scripts directory not found: %s", skills_dir)
        return []

    requested = set(function_names)
    functions_by_name: dict[str, object] = {}
    module_prefix = _module_prefix_for_dir(skills_dir)

    for entry in os.listdir(skills_dir):
        if not entry.endswith(".py") or entry.startswith("__"):
            continue

        module_path = os.path.join(skills_dir, entry)
        module_name = f"{module_prefix}.{os.path.splitext(entry)[0]}"

        module = _load_module_from_path(module_name, module_path)
        if module is None:
            continue

        for name, func in inspect.getmembers(module, inspect.isfunction):
            if name in requested and name not in functions_by_name:
                functions_by_name[name] = func

    tools: list[Tool] = []
    for name in function_names:
        func = functions_by_name.get(name)
        if func is None:
            logger.warning("Function not found in skills scripts: %s", name)
            continue
        description = inspect.getdoc(func) or ""
        tools.append(StructuredTool.from_function(func, name=name, description=description))

    return tools


def load_tools_from_skills() -> list[Tool]:
    """Build Tool instances from scripts declared in skill files.

    Reads the SKILL.md frontmatter metadata.scripts values and loads
    the corresponding functions from the skills scripts directory.
    """
    from app.scripts.skills_loader import load_skills

    skills = load_skills()
    if not skills:
        return []

    requested: list[str] = []
    seen: set[str] = set()

    for skill_name, skill in skills.items():
        scripts = skill.get("scripts") or []
        if not isinstance(scripts, list):
            logger.warning("Invalid scripts list for skill: %s", skill_name)
            continue
        for script_name in scripts:
            if not script_name or not isinstance(script_name, str):
                continue
            if script_name in seen:
                continue
            seen.add(script_name)
            requested.append(script_name)

    return load_tools(requested)


def _load_module_from_path(module_name: str, module_path: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        logger.warning("Could not load module spec for %s", module_path)
        return None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

