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

def handler(event, context):
    method = event.get('httpMethod')
    
    # Default headers
    headers = {
        'Access-Control-Allow-Origin': '*',
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
    
    if method == 'GET':
        clients = get_all_clients()
        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps(clients)
        }
    
    try:
        body = json.loads(event['body'])
    except Exception as e:
        print(f"Error parsing body: {e}")
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps('Invalid request body')
        }
    
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