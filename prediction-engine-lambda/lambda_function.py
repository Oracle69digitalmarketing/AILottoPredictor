import boto3
import json
import csv
from datetime import datetime

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    bucket = 'ai-lotto-predictor-data'
    key = 'results/babaijeburesults.csv'
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
    except s3.exceptions.NoSuchKey:
        return {
            'statusCode': 404,
            'body': json.dumps(f"Error: The file '{key}' does not exist in the bucket '{bucket}'.")
        }

    lines = response['Body'].read().decode('utf-8').splitlines()
    reader = csv.DictReader(lines)
    draws = list(reader)[-10:]
    if not draws:
        return {
            'statusCode': 400,
            'body': json.dumps('Error: The CSV file is empty or has no data.')
        }

    formatted_draws = "\n".join([
        f"{i+1}. {row['Date']}: {row['Winning Numbers']}"
        for i, row in enumerate(draws)
    ])
    prompt = f"""
Here are the last 10 draws of the '{draws[-1]['Game']}' game:
{formatted_draws}
Based on this data, what are the 5 most likely numbers to appear in the next draw?
Return your answer as JSON with keys: numbers, probabilities.
"""

    bedrock = boto3.client(service_name='bedrock-runtime', region_name='eu-central-1')

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "temperature": 0.7,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    })

    modelId = 'anthropic.claude-3-sonnet-20240229-v1:0'
    accept = 'application/json'
    contentType = 'application/json'

    try:
        response = bedrock.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)
        response_body = json.loads(response.get('body').read())

        predictions_text = response_body.get('content')[0].get('text')
        predictions = json.loads(predictions_text)

        # Store predictions to DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('LottoPredictions')
        table.put_item(Item={
            'GameName': draws[-1]['Game'],
            'PredictionDate': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'TopNumbers': predictions['numbers'],
            'Probabilities': {str(k): str(v) for k, v in predictions['probabilities'].items()},
            'ModelVersion': 'Claude 3 Sonnet (Bedrock)'
        })
        return {'statusCode': 200, 'body': json.dumps(predictions)}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps(f"Error invoking model or processing response: {str(e)}")}
