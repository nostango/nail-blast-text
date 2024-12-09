import json
import boto3
import hashlib
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
    try:
        account = twilio_client.api.accounts(account_sid).fetch()
        print(f"Success")
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

def get_all_clients():
    print("Fetching all clients from DynamoDB.")
    try:
        response = clients_table.scan()
        clients = response.get('Items', [])
        return clients
    except ClientError as e:
        print(f"Error fetching clients: {e}")
        raise e

def send_message_to_all_clients(message):
    clients = get_all_clients()
    
    for client in clients:
        # Simulate sending SMS
        send_sms(client['phone_number'], message)
    
    return f"Simulated message: {message} sent to all {len(clients)} clients."

def send_message_to_selected_clients(message, clients_list):
    successful_sends = 0

    for client_id in clients_list:
        try:
            response = clients_table.get_item(Key={'id': client_id})
            client = response.get('Item')
            if client and 'phone_number' in client:
                send_sms(client['phone_number'], message)
                successful_sends += 1
            else:
                print(f"No client found with ID or missing phone number.")
        except ClientError as e:
            print(f"Error fetching client: {e}")

def upload_csv_data(csv_data):
    for row in csv_data:
        first_name = row.get('First Name') or row.get('name')  # Adjust based on CSV columns
        last_name = row.get('Last Name') or ""  # If applicable
        phone = row.get('phone_number') or row.get('phone') or ""
        email = row.get('Email', '')
        notes = row.get('Notes', '')
        days_since_last_appointment = row.get('Days Since Last Appointment', '')

        # Ensure required fields are present:
        if not first_name or not phone:
            print(f"Skipping row with missing required data: {row}")
            continue  # Skip this row

        # Construct the DynamoDB id:
        raw_id_string = (first_name.strip().lower() + "_" + last_name.strip().lower())

        # Generate a SHA-256 hash and take a portion of it
        hash_object = hashlib.sha256(raw_id_string.encode('utf-8'))
        id_val = hash_object.hexdigest()
        id_val = id_val[:10]

        try:
            # Check if the item already exists:
            existing_item_response = clients_table.get_item(Key={'id': id_val})
            existing_item = existing_item_response.get('Item', None)

            if existing_item:
                # If the item exists, preserve its opt_in setting
                opt_in = existing_item.get('opt_in', 'N')
                # Update the existing item if needed
                clients_table.update_item(
                    Key={'id': id_val},
                    UpdateExpression="set first_name=:f, last_name=:l, phone_number=:p, email=:e, notes=:n, days_since_last_appointment=:d",
                    ExpressionAttributeValues={
                        ':f': first_name,
                        ':l': last_name,
                        ':p': phone,
                        ':e': email,
                        ':n': notes,
                        ':d': days_since_last_appointment,
                    }
                )
            else:
                # If it's a new item, set opt_in to 'N'
                opt_in = 'N'

                clients_table.put_item(Item={
                    'id': id_val,
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone_number': phone,
                    'email': email,
                    'notes': notes,
                    'days_since_last_appointment': days_since_last_appointment,
                    'opt_in': opt_in
                })
        except ClientError as e:
            print(f"Error adding/updating client: {e}")

    return f"CSV data processed and clients updated."

# Default headers for HTTP responses
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

        # Determine the action
        action = body.get('action')

        if action == 'upload_csv':
            csv_data = body.get('csv_data', [])
            if not csv_data:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps('csv_data is required for upload_csv action.')
                }
            try:
                upload_result = upload_csv_data(csv_data)
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps(upload_result)
                }
            except Exception as e:
                print(f"Error uploading CSV data: {str(e)}")
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps('Internal Server Error while uploading CSV data.')
                }

        elif action == 'send_message':
            # Process sending messages as per existing logic
            # Ensure message is present
            message = body.get('message')
            if not message:
                print("No message provided.")
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps('Message content is required.')
                }

            all_numbers = body.get('all_numbers', False)
            select_numbers = body.get('select_numbers', [])
            csv_data = body.get('csv_data', [])

            csv_processed = False

            if csv_data:
                try:
                    upload_csv_result = upload_csv_data(csv_data)
                    csv_processed = True
                except Exception as e:
                    print(f"Error processing CSV data: {str(e)}")
                    return {
                        'statusCode': 500,
                        'headers': headers,
                        'body': json.dumps('Internal Server Error while processing CSV data.')
                    }

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

        else:
            print(f"Unsupported action: {action}")
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps('Unsupported action.')
            }

    # If an unsupported method is used, return a 405 Method Not Allowed
    print(f"Method {method} not allowed.")
    return {
        'statusCode': 405,
        'headers': headers,
        'body': json.dumps('Method Not Allowed')
    }
