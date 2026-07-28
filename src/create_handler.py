import json
import os
import random
import string
import time

import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

ALPHABET = string.ascii_letters + string.digits  # base62
CODE_LENGTH = 7
MAX_ATTEMPTS = 5


def generate_code(length=CODE_LENGTH):
    return "".join(random.choices(ALPHABET, k=length))


def handler(event, context):
    domain_name = event.get("requestContext", {}).get("domainName", "")
    base_url = f"https://{domain_name}" if domain_name else ""

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"error": "invalid JSON body"})

    long_url = body.get("url")
    if not long_url or not long_url.startswith(("http://", "https://")):
        return _response(400, {"error": "url must be a valid http(s) URL"})

    custom_code = body.get("customCode")
    ttl_seconds = body.get("ttlSeconds")  # optional auto-expiry
    now = int(time.time())

    item = {
        "shortCode": None,  # set per attempt below
        "longUrl": long_url,
        "createdAt": now,
        "clickCount": 0,
    }
    if ttl_seconds:
        item["expiresAt"] = now + int(ttl_seconds)

    codes_to_try = [custom_code] if custom_code else [generate_code() for _ in range(MAX_ATTEMPTS)]

    for code in codes_to_try:
        item["shortCode"] = code
        try:
            table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(shortCode)",
            )
            return _response(
                201,
                {"shortCode": code, "shortUrl": f"{base_url}/{code}", "longUrl": long_url},
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                if custom_code:
                    return _response(409, {"error": "custom code already taken"})
                continue  # try next generated code
            raise

    return _response(500, {"error": "could not generate a unique code, please retry"})


def _response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }