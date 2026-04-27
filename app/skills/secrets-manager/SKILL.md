---
name: secrets-manager
description: Manages secrets for services, you can add, update, or delete secrets for a specific service.
metadata:
  scripts:
    - get_aws_secrets
    - update_aws_secret
---

# Secrets Manager Skill

## When to use this skill:
When you need to manage secrets for services, such as adding or updating secrets.

## How to manage secrets

In order to manage secrets for a service, you can use the following scripts:
- `get_aws_secrets(secret_name)`: Retrieves secrets for a specific service from AWS Secrets Manager.
- `update_aws_secret(secret_name, key, value)`: Updates a specific secret for a service in AWS Secrets Manager.


