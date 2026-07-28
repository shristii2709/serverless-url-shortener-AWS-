import os
import time

import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


def handler(event, context):
    short_code = event["pathParameters"]["shortCode"]

    try:
        result = table.update_item(
            Key={"shortCode": short_code},
            UpdateExpression="SET clickCount = clickCount + :inc",
            ConditionExpression="attribute_exists(shortCode) AND (attribute_not_exists(expiresAt) OR expiresAt > :now)",
            ExpressionAttributeValues={":inc": 1, ":now": int(time.time())},
            ReturnValues="ALL_NEW",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return {"statusCode": 404, "body": "Short URL not found or expired"}
        raise

    long_url = result["Attributes"]["longUrl"]
    return {
        "statusCode": 301,
        "headers": {"Location": long_url, "Cache-Control": "no-cache"},
        "body": "",
    }