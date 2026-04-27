
def get_aws_secrets(secret_name):
    """Retrieves the secrets from AWS Secrets Manager for the given secret name.

    Args:
        secret_name (str): The name of the secret to retrieve. Could be the service name under analysis or a reference service.

    Returns:
        dict: A dictionary containing the secret key-value pairs, or an empty dictionary if the secret is not found or an error occurs.
    """
    import os
    import json
    import boto3
    import logging
    from botocore.exceptions import ClientError
    
    logger = logging.getLogger(__name__)
    
    region_name = os.getenv("AWS_REGION", "us-east-1")
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "test")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
    endpoint_url = os.getenv("AWS_ENDPOINT_URL", "http://localstack:4566")  # Default for LocalStack

    # Optional: aws_session_token = "YOUR_SESSION_TOKEN"

    # Create a Secrets Manager client with explicit credentials
    session = boto3.session.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        # aws_session_token=aws_session_token,  # Uncomment if using session token
        region_name=region_name
    )
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name,
        endpoint_url=endpoint_url
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        logger.error("Error retrieving secret: %s", e)
        return {}

    secret_str = get_secret_value_response.get('SecretString')
    if not secret_str:
        return {}
    try:
        logger.debug("Retrieved secret string: %s", secret_str)
        return json.loads(secret_str)
    except Exception as e:
        logger.error("Error parsing secret JSON: %s. Error: %s", secret_str, e)
        return {}

def update_aws_secret(secret_name, key, value):
    """
    Updates a single attribute in a JSON secret in AWS Secrets Manager.
    Args:
        secret_name (str): The name of the secret to update. Could be the service name under analysis or a reference service.
        key (str): The attribute key to update or add.
        value: The new value for the attribute.
    Returns:
        bool: True if update succeeded, False otherwise.
    """
    import os
    import json
    import boto3
    import logging
    from botocore.exceptions import ClientError
    
    logger = logging.getLogger(__name__)
    logger = logging.getLogger(__name__)
    region_name = os.getenv("AWS_REGION", "us-east-1")
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "test")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "test")
    endpoint_url = os.getenv("AWS_ENDPOINT_URL", "http://localstack:4566")

    session = boto3.session.Session(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region_name
    )
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name,
        endpoint_url=endpoint_url
    )

    # Retrieve the current secret value
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret_str = get_secret_value_response.get('SecretString')
        if secret_str:
            secret_dict = json.loads(secret_str)
        else:
            secret_dict = {}
    except Exception as e:
        logger.error(f"Error retrieving current secret: {e}")
        return False

    # Update the attribute
    secret_dict[key] = value

    # Store the updated secret
    try:
        client.put_secret_value(SecretId=secret_name, SecretString=json.dumps(secret_dict))
        logger.info(f"Successfully updated secret '{secret_name}' with key '{key}' and value '{value}'")
        return True
    except ClientError as e:
        logger.error(f"Error updating secret: {e}")
        return False

if __name__ == "__main__":
    secret_name = "service-b"
    # update_aws_secret(secret_name, "DB_NAME", "new_value") # devdatabase
    secret = get_aws_secrets(secret_name)
    print(type(secret))
    print(secret)