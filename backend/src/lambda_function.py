import json
import boto3

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
clients_table = dynamodb.Table('client_db_test')

def get_all_clients():
    print("Fetching all clients from DynamoDB.")
    response = clients_table.scan()
    print(f"Retrieved {len(response.get('Items', []))} clients.")
    return response.get('Items', [])

def send_message_to_all_clients(message):
    print("Sending messages to all clients.")
    # Pull all clients from DynamoDB
    response = clients_table.scan()
    clients = response.get('Items', [])
    print(f"Found {len(clients)} clients to send messages to.")
    
    # Send message to each client
    for client in clients:
        send_sms(client['phone_number'], message)
    
    return (f"Message sent to all {len(clients)} clients.")

def send_message_to_selected_clients(message, clients_list):
    print(f"Sending messages to selected clients: {clients_list}")
    # clients_list is expected to be a list of recipient IDs (phone numbers)
    for client_id in clients_list:
        # Retrieve client details from DynamoDB
        print(f"Fetching client with ID: {client_id}")
        response = clients_table.get_item(Key={'id': client_id})
        client = response.get('Item')
        if client:
            send_sms(client['phone_number'], message)
        else:
            print(f"No client found with ID: {client_id}")

    return (f"Message sent to all {len(clients_list)} clients.")

def send_sms(phone_number, message):
    # Send SMS with Twilio
    print(f"Sending SMS to {phone_number}: {message}")
    pass  # Replace with actual Twilio integration

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
                'body': json.dumps(f"Internal Server Error: {str(e)}")
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
        # Process CSV data if present
        csv_data = body.get('csv_data', [])

        print(f"Message: {message}")
        print(f"All Numbers: {all_numbers}")
        print(f"Selected Numbers: {select_numbers}")
        print(f"CSV Data: {csv_data}")

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
                print(f"Adding client to DynamoDB: {phone_number}")
                clients_table.put_item(Item={
                    'id': phone_number,  # Use phone_number as unique identifier
                    'name': name,
                    'phone_number': phone_number,
                    'email': email
                })
            csv_processed = True

        # Send messages
        if all_numbers:
            first_cond_response = send_message_to_all_clients(message)
            response_message = f'Message sent to selected clients: {first_cond_response}'
        else:
            second_cond_response = send_message_to_selected_clients(message, select_numbers)
            response_message = f'Message sent to selected clients: {second_cond_response}'

        response_message = f'Message sent to selected clients: '
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