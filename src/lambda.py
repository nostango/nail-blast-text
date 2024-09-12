import boto3
import os
import json

def lambda_handler(event, context):
    message = event.get('message', 'No message provided')
    print("something")
    print(f"Received message: {message}")
    return {
        'statusCode': 200,
        'body': json.dumps(f'Message logged: {message}')
    }
