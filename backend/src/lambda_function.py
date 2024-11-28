import json
import boto3
import os
from botocore.exceptions import ClientError
from twilio.rest import Client

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
clients_table = dynamodb.Table('client_db_test')

# Initialize Secrets Manager client
secrets_client = boto3.client('secretsmanager', region_name='us-east-1')

# Environment variable for the secret name
SECRET_NAME = os.environ.get('TWILIO_SECRET_NAME', 'twilio/credentials')

# Cache for Twilio credentials
twilio_secrets_cache = {}

def get_twilio_credentials():
    """
    Retrieve Twilio credentials from AWS Secrets Manager.
    Caches the credentials to avoid multiple calls.
    """
    global twilio_secrets_cache

    if twilio_secrets_cache:
        return twilio_secrets_cache

    try:
        response = secrets_client.get_secret_value(SecretId=SECRET_NAME)
    except ClientError as e:
        print(f"Error retrieving secret {SECRET_NAME}: {e}")
        raise e

    # Parse the secret JSON
    try:
        secret = response['SecretString']
        secret_dict = json.loads(secret)
    except json.JSONDecodeError as e:
        print(f"Error decoding secret JSON: {e}")
        raise e

    # Cache the secrets
    twilio_secrets_cache = {
        'TWILIO_ACCOUNT_SID': secret_dict['TWILIO_ACCOUNT_SID'],
        'TWILIO_AUTH_TOKEN': secret_dict['TWILIO_AUTH_TOKEN'],
        'TWILIO_PHONE_NUMBER': secret_dict['TWILIO_PHONE_NUMBER']
    }

    return twilio_secrets_cache

# Retrieve Twilio credentials once and initialize Twilio client
twilio_secrets = get_twilio_credentials()
twilio_client = Client(twilio_secrets['TWILIO_ACCOUNT_SID'], twilio_secrets['TWILIO_AUTH_TOKEN'])
twilio_phone_number = twilio_secrets['TWILIO_PHONE_NUMBER']

def get_all_clients():
    print("Fetching all clients from DynamoDB.")
    try:
        response = clients_table.scan()
        clients = response.get('Items', [])
        print(f"Retrieved {len(clients)} clients.")
        return clients
    except ClientError as e:
        print(f"Error fetching clients: {e}")
        raise e

def send_message_to_all_clients(message):
    print("Sending messages to all clients.")
    clients = get_all_clients()
    print(f"Found {len(clients)} clients to send messages to.")
    
    for client in clients:
        send_sms(client['phone_number'], message)
    
    return f"Message sent to all {len(clients)} clients."

def send_message_to_selected_clients(message, clients_list):
    print(f"Sending messages to selected clients: {clients_list}")
    successful_sends = 0

    for client_id in clients_list:
        try:
            print(f"Fetching client with ID: {client_id}")
            response = clients_table.get_item(Key={'id': client_id})
            client = response.get('Item')
            if client and 'phone_number' in client:
                send_sms(client['phone_number'], message)
                successful_sends += 1
            else:
                print(f"No client found with ID: {client_id} or missing phone number.")
        except ClientError as e:
            print(f"Error fetching client {client_id}: {e}")

    return f"Message sent to {successful_sends} clients."

def send_sms(phone_number, message):
    try:
        print(f"Sending SMS to {phone_number}: {message}")
        sent_message = twilio_client.messages.create(
            body=message,
            from_=twilio_phone_number,
            to=phone_number
        )
        print(f"Message sent with SID: {sent_message.sid}")
    except Exception as e:
        print(f"Failed to send SMS to {phone_number}: {e}")

# Default headers
headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
}

def handler(event, context):
    method = event.get('httpMethod')
    print(f"Received {method} request.")

    # Handle CORS preflight request
    if method == 'OPTIONS':
        print("Handling CORS preflight request.")
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    if method == 'GET':
        try:
            clients = get_all_clients()
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(clients)
            }
        except Exception as e:
            print(f"Error during GET request: {str(e)}")
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps('Internal Server Error')
            }
    
    # Handle POST request
    if method == 'POST':
        # Ensure body is present
        if 'body' not in event or event['body'] is None:
            print("POST request missing body.")
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps('Request body is required for POST requests')
            }

        try:
            body = json.loads(event['body'])
            print("Successfully parsed request body.")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}")
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps(f'Invalid JSON in request body: {str(e)}')
            }

        # Process the POST request
        message = body.get('message')
        all_numbers = body.get('all_numbers', False)
        select_numbers = body.get('select_numbers', [])
        csv_data = body.get('csv_data', [])

        print(f"Message: {message}")
        print(f"All Numbers: {all_numbers}")
        print(f"Selected Numbers: {select_numbers}")
        print(f"CSV Data: {csv_data}")

        # Validate message
        if not message:
            print("No message provided.")
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps('Message content is required.')
            }

        # Initialize a flag to track if CSV data was processed
        csv_processed = False

        if csv_data:
            print(f"Processing CSV data with {len(csv_data)} rows.")
            for row in csv_data:
                name = row.get('name')
                phone_number = row.get('phone_number')
                email = row.get('email', '')

                if not name or not phone_number:
                    print(f"Skipping row with missing data: {row}")
                    continue  # Skip rows with missing required data

                # Put item into DynamoDB
                try:
                    print(f"Adding/updating client in DynamoDB: {phone_number}")
                    clients_table.put_item(Item={
                        'id': phone_number,  # Use phone_number as unique identifier
                        'name': name,
                        'phone_number': phone_number,
                        'email': email
                    })
                except ClientError as e:
                    print(f"Error adding/updating client {phone_number}: {e}")
            csv_processed = True

        # Send messages
        if all_numbers:
            response_message = send_message_to_all_clients(message)
        elif select_numbers:
            response_message = send_message_to_selected_clients(message, select_numbers)
        else:
            response_message = 'No recipients specified.'

        if csv_processed:
            response_message += ' CSV data processed and clients updated.'

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response_message)
        }

    # If an unsupported method is used, return a 405 Method Not Allowed
    print(f"Method {method} not allowed.")
    return {
        'statusCode': 405,
        'headers': headers,
        'body': json.dumps('Method Not Allowed')
    }
