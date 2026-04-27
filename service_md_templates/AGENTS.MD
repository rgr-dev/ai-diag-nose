This file is an operative guide for agents, the file structure is:

- Project purpose: A brief description of the project and its main objectives.
- Agents: Who or what will use this file, for example: AI agents, human agents, tools.
- Rules: A set of guidelines or rules that agents should follow when interacting with the service, example:
```
- Do not modify files outside `/src`
- Never commit secrets
- Ask for confirmation before deleting code
- Prefer small, incremental changes
```
- Coding Conventions: A description of the coding standards and conventions that should be followed when working on the service, for example:
```
- Use camelCase for variable names
- Use PascalCase for class names
- Include docstrings for all functions and classes
- Write unit tests for new features
```
- Project Structure: An overview of the project's directory structure, explaining the purpose of each folder and important files, for example:
```
- /src: Contains the source code of the service
- /tests: Contains unit and integration tests
- /docs: Contains documentation files
- README.md: The main documentation file for the project
```
- Error Handling: what to do if something fails.
- Security: security considerations and best practices for working with the service, for example:
```
- Do not hardcode sensitive information such as API keys or passwords
- Use environment variables to manage secrets
```