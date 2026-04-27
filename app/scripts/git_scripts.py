
import os
import subprocess
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def git_clone_or_pull_repo(repo_url):
	"""
	Clone or update a Git repository using HTTPS with embedded credentials.

	This function will either clone a new repository or pull the latest changes
	for an existing one. It injects the Bitbucket App Password into the HTTPS URL
	in the format:
		https://username:password@bitbucket.org/...

	Args:
		repo_url (str): The HTTPS repository URL, including the username (e.g.,
			'https://user@bitbucket.org/owner/repo.git').

	Environment Variables:
		BITBUCKET_TOKEN: The Bitbucket App Password to use for authentication.
		GIT_REPOS_PATH: (Optional) Destination directory for cloned repositories.
			Defaults to '/workspace/git_repos'.

	Returns:
		bool: True if the operation succeeded, False otherwise.

	Notes:
		- Only HTTPS URLs with embedded username are supported.
		- If the repository already exists at the destination, a 'git pull' is performed.
		- If the repository does not exist, a 'git clone' is performed.
		- Logs errors and prints user/home info for debugging.
	"""

	dest_dir = os.getenv("GIT_REPOS_PATH", "/workspace/git_repos")


	# 🔹 Inject credentials ONLY for HTTPS
	if repo_url.startswith("https://"):
		app_password = os.getenv("BITBUCKET_TOKEN", "")

		if not app_password:
			logger.error("BITBUCKET_TOKEN not set")
			return False
		# https://user@bitbucket.org/... → insert password
		if "@" in repo_url:
			prefix, rest = repo_url.split("@", 1)
			username = prefix.replace("https://", "")
			repo_url = f"https://{username}:{app_password}@{rest}"
		else:
			logger.error("URL must include username (https://user@...)")
			return False

	repo_name = repo_url.rstrip('.git').split('/')[-1]
	dest_path = Path(dest_dir) / repo_name

	if dest_path.exists():
		logger.info(f"Directory {dest_path} exists. Pulling latest changes...")
		try:
			subprocess.run(
				["git", "-C", str(dest_path), "pull"],
				check=True
			)
		except subprocess.CalledProcessError as e:
			logger.error(f"Error pulling repo: {e}")
			return False
	else:
		logger.info(f"Cloning into {dest_path}...")
		try:
			subprocess.run(
				["git", "clone", repo_url, str(dest_path)],
				check=True
			)
		except subprocess.CalledProcessError as e:
			logger.error(f"Error cloning repo: {e}")
			return False

	return True


def git_last_touched_files(repo_name):
	"""
	Get the list of files changed in the last commit.

	Returns:
		list[str]: List of file paths changed in the last commit (HEAD).
	"""
	logger = logging.getLogger(__name__)
	dest_dir = os.getenv("GIT_REPOS_PATH", "/workspace/git_repos")
	try:
		result = subprocess.run(
			["git", "-C", f'{dest_dir}/{repo_name}', "diff", "--name-only", "HEAD~1", "HEAD"],
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			check=True,
			text=True
		)
		files = result.stdout.strip().split('\n')
		logger.info(f"Files changed in last commit: {files}")
		return [f for f in files if f]
	except subprocess.CalledProcessError as e:
		logger.error("Error running git command: %s", e.stderr)
		return []


def git_last_diff_for_file(filename):
	"""
	Get the diff of the last commit that affected a specific file.

	Args:
		filename (str): The path to the file to check.

	Returns:
		str: The diff output as a string. Empty string if no diff is found.
	"""
	current_dir = os.getcwd()
	try:
		os.chdir('/workspace')
		# Ejecutamos el comando
		result = subprocess.run(
			["git", "log", "-p", "-1", "--", filename],
			capture_output=True, # Versión moderna de stdout=PIPE y stderr=PIPE
			text=True,
			check=True
		)
		
		# Si el archivo es nuevo o no tiene cambios previos, el stdout podría estar vacío
		if not result.stdout:
			logger.info("No se encontró historial de commits para: %s", filename)
			return ""
		os.chdir(current_dir)
		return result.stdout

	except FileNotFoundError:
		logger.error("Error: El comando 'git' no está instalado o no se encuentra en el PATH.")
		return ""
	except subprocess.CalledProcessError as e:
		logger.error("Error ejecutando git log para %s: %s", filename, e.stderr)
		return ""


if __name__ == "__main__":
	import sys
	if len(sys.argv) == 1:
		files = git_last_touched_files()
		print(files)
	elif len(sys.argv) == 2:
		arg = sys.argv[1]
		if arg.startswith('git@') or arg.startswith('https://'):
			# Assume it's a repo URL
			git_clone_or_pull_repo(arg)
		else:
			filename = arg
			diff = git_last_diff_for_file(filename)
			print(diff)
	elif len(sys.argv) == 3:
		arg1 = sys.argv[1]
		arg2 = sys.argv[2]
		if arg1.startswith('git@') or arg1.startswith('https://'):
			git_clone_or_pull_repo(arg1, arg2)
		else:
			print("Usage: python git_scripts.py [filename] or python git_scripts.py <repo_ssh_url> [dest_dir]")
	else:
		print("Usage: python git_scripts.py [filename] or python git_scripts.py <repo_ssh_url> [dest_dir]")
