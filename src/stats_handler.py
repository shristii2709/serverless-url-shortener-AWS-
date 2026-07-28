import json
import os

import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


def handler(event, context):
    short_code = event["pathParameters"]["shortCode"]
    result = table.get_item(Key={"shortCode": short_code})
    item = result.get("Item")

    if not item:
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "not found"}),
        }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {
                "shortCode": item["shortCode"],
                "longUrl": item["longUrl"],
                "createdAt": int(item["createdAt"]),
                "clickCount": int(item["clickCount"]),
            }
        ),
    }