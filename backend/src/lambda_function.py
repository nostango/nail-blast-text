import json
import boto3

# this is a test to make sure the lambda really does get uploaded to AWS
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
clients_table = dynamodb.Table('client_db_test')

def get_all_clients():
    response = clients_table.scan()
    return response.get('Items', [])

def send_message_to_all_clients(message):
    # Pull all clients from DynamoDB
    response = clients_table.scan()
    clients = response.get('Items', [])
    
    # Send message to each client
    for client in clients:
        send_sms(client['phone_number'], message)

def send_message_to_selected_clients(message, clients_list):
    # clients_list is expected to be a list of recipient IDs (phone numbers)
    for client_id in clients_list:
        # Retrieve client details from DynamoDB
        response = clients_table.get_item(Key={'id': client_id})
        client = response.get('Item')
        if client:
            send_sms(client['phone_number'], message)

def send_sms(phone_number, message):
    # Send SMS with Twilio
    print(f"Sending SMS to {phone_number}: {message}")
    pass

# Default headers
headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
}

def handler(event, context):
    method = event.get('httpMethod')
    
    # Handle CORS preflight request
    if method == 'OPTIONS':
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
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps(f"Internal Server Error: {str(e)}")
            }
    
    # Handle POST request
    if method == 'POST':
        # Ensure body is present
        if 'body' not in event or event['body'] is None:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps('Request body is required for POST requests')
            }

        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError as e:
            # If the body cannot be parsed as JSON, return a 400 error
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

        # Process CSV data if present
        if csv_data:
            for row in csv_data:
                name = row.get('name')
                phone_number = row.get('phone_number')
                email = row.get('email', '')

                if not name or not phone_number:
                    print(f"Skipping row with missing data: {row}")
                    continue  # Skip rows with missing required data

                # Put item into DynamoDB
                clients_table.put_item(Item={
                    'id': phone_number,  # Use phone_number as unique identifier
                    'name': name,
                    'phone_number': phone_number,
                    'email': email
                })

        # Send messages
        if all_numbers:
            send_message_to_all_clients(message)
        else:
            send_message_to_selected_clients(message, select_numbers)

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps('Message sent successfully')
        }

    # If an unsupported method is used, return a 405 Method Not Allowed
    return {
        'statusCode': 405,
        'headers': headers,
        'body': json.dumps('Method Not Allowed')
    }