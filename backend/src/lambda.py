import json
import boto3

# Authorized phone number
cassidy = '+15555555555'
dynamodb = boto3.resource('dynamodb')
clients_table = dynamodb.Table('client_db')

def send_message_to_all_clients(message):
    # Pull all clients from DynamoDB
    response = clients_table.scan()
    clients = response.get('Items', [])
    
    # Send message to each client
    for client in clients:
        send_sms(client['phone_number'], message)

def send_message_to_selected_clients(message, clients_list):
    # Send message to selected clients
    for client in clients_list:
        send_sms(client, message)

def send_sms(phone_number, message):
    # Integration with Twilio or another SMS service
    pass

def handler(event, context):
    # Get HTTP method
    method = event.get('httpMethod')
    
    # Default headers
    headers = {
        'Access-Control-Allow-Origin': '*',  # or specify your domain
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
    }
    
    # Handle CORS preflight request
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    # Parse incoming message
    body = json.loads(event['body'])
    message = body.get('message')
    phone_number = body.get('phone_number')
    confirm = body.get('confirm')
    send_to = body.get('send_to', 'all')
    
    # Check if the phone number is authorized
    if phone_number != cassidy:
        return {
            'statusCode': 401,
            'headers': headers,
            'body': json.dumps('Unauthorized')
        }
    else:
        # Confirmation message logic
        if confirm == "yes":
            # Send message to all or selected clients
            if send_to == 'all':
                send_message_to_all_clients(message)
            else:
                send_message_to_selected_clients(message, send_to)
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps('Message sent successfully')
            }
        else:
            # Ask for confirmation
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps('Is this what you want to send?')
            }