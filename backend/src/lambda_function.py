import json
import boto3
from twilio.rest import Client
from botocore.exceptions import ClientError

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
clients_table = dynamodb.Table('testing_my_phone_number')

def get_twilio_credentials(secret_name, region_name="us-east-1"):
    client = boto3.client("secretsmanager", region_name=region_name)
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        # Secrets Manager stores the secret as a JSON string
        secret = json.loads(get_secret_value_response["SecretString"])
        return secret
    except Exception as e:
        print(f"Error retrieving secret: {e}")
        raise

def verify_twilio_credentials(twilio_client, account_sid):
    """
    Try to fetch Twilio account details to verify credentials are correct.
    """
    try:
        account = twilio_client.api.accounts(account_sid).fetch()
        print(f"Twilio Account Verification: Friendly Name={account.friendly_name}, Status={account.status}")
    except Exception as e:
        print(f"Error verifying Twilio credentials: {e}")
        raise

# Set the secret name and region
secret_name = "twilio/credentials"
region_name = "us-east-1"  # Adjust to your AWS region

# Retrieve Twilio credentials
credentials = get_twilio_credentials(secret_name, region_name)

# Extract the credentials
account_sid = credentials["TWILIO_ACCOUNT_SID"]
auth_token = credentials["TWILIO_AUTH_TOKEN"]
twilio_phone_number = credentials["TWILIO_PHONE_NUMBER"]

# Initialize the Twilio client
twilio_client = Client(account_sid, auth_token)

# Quick check to ensure credentials are correct
verify_twilio_credentials(twilio_client, account_sid)

def get_all_clients():
    """
    Fetch all clients from DynamoDB.
    """
    print("Fetching all clients from DynamoDB.")
    try:
        response = clients_table.scan()
        clients = response.get('Items', [])
        print(f"Retrieved {len(clients)} clients.")
        return clients
    except ClientError as e:
        print(f"Error fetching clients: {e}")
        raise e

# Removed Twilio credential retrieval and client initialization functions

def send_message_to_all_clients(message):
    """
    Placeholder for sending messages to all clients.
    """
    print("Simulating sending messages to all clients.")
    clients = get_all_clients()
    print(f"Found {len(clients)} clients to send messages to.")
    
    for client in clients:
        # Simulate sending SMS
        send_sms(client['phone_number'], message)
        print(f"Message: {message} sent to {client['phone_number']}.")
    
    return f"Simulated message: {message} sent to all {len(clients)} clients."

def send_message_to_selected_clients(message, clients_list):
    """
    Placeholder for sending messages to selected clients based on their IDs.
    """
    print(f"Simulating sending messages to selected clients: {clients_list}")
    successful_sends = 0

    for client_id in clients_list:
        try:
            response = clients_table.get_item(Key={'id': client_id})
            client = response.get('Item')
            if client and 'phone_number' in client:
                send_sms(client['phone_number'], message)
                successful_sends += 1
            else:
                print(f"No client found with ID: {client_id} or missing phone number.")
        except ClientError as e:
            print(f"Error fetching client {client_id}: {e}")

    return f"Simulated message sent to {successful_sends} clients."

def send_sms(phone_number, message):
    try:
        message = twilio_client.messages.create(
            body=message,
            from_=twilio_phone_number,
            to=phone_number,  # Replace with the recipient's phone number
        )
        print(f"Message sent with SID: {message.sid}")
    except Exception as e:
        print(f"Error sending SMS: {e}")

    

# Default headers for HTTP responses
headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
}

def handler(event, context):
    """
    AWS Lambda handler function.
    """
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
            # Fetch all clients again after processing CSV data
            clients = get_all_clients()

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
