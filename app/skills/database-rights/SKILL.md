---
name: database-rights
description: Just adds access to table/function/view for a given user or role (don't add database rights).
metadata:
  scripts:
    - database_scripts_executor
---

# Database Rights Management Skill

## When to use this skill:
When you need to grant specific permissions to a user or role in the database to allow them to perform certain operations, such as querying a table, executing a function, or accessing a view.

## How to give rights

In order to add access rights to a user or role, you can use the following SQL commands:
- For tables:
  - `GRANT SELECT ON TABLE table_name TO user_name;`
  - `GRANT INSERT ON TABLE table_name TO user_name;`
  - `GRANT UPDATE ON TABLE table_name TO user_name;`
- For functions:
  - `GRANT EXECUTE ON FUNCTION function_name TO user_name;`
- For views:
  - `GRANT SELECT ON VIEW view_name TO user_name;`

Use the script `database_scripts_executor` to execute the SQL commands in the database. The script receives the host, port, username, password, database, and the SQL command to be executed.

