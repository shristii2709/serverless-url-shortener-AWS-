# 🔗 Serverless URL Shortener

A production-shaped serverless URL shortener built on AWS — no servers to manage, pay-per-request billing, and a data model designed around a single access pattern instead of a relational schema.

<p>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/AWS-Lambda-FF9900?logo=awslambda&logoColor=white" alt="AWS Lambda">
  <img src="https://img.shields.io/badge/AWS-API%20Gateway-FF4F8B?logo=amazonapigateway&logoColor=white" alt="AWS API Gateway">
  <img src="https://img.shields.io/badge/AWS-DynamoDB-4053D6?logo=amazondynamodb&logoColor=white" alt="AWS DynamoDB">
  <img src="https://img.shields.io/badge/IaC-AWS%20SAM-orange?logo=amazon-aws" alt="AWS SAM">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
</p>

---

## 📖 Overview

This project demonstrates how to build a **serverless REST API** entirely on managed AWS services.

A client `POST`s a long URL to the API, and **AWS Lambda** generates a short code and stores the mapping in **DynamoDB**. Visiting the short URL triggers a second Lambda that looks up the original URL and issues a `301` redirect — with the click count incremented atomically on every hit. A third endpoint returns click statistics for any short code.

> **No servers to patch, no capacity to plan.** DynamoDB runs in on-demand billing mode and Lambda only costs money while it's actually handling a request — at low traffic this runs entirely inside the AWS free tier.

---

## 🏗️ Architecture

```
Client
  │
  ▼
API Gateway (HTTP API)
  ├─ POST /urls                   → CreateFunction   → DynamoDB (PutItem, conditional)
  ├─ GET  /{shortCode}            → RedirectFunction  → DynamoDB (UpdateItem, atomic counter) → 301
  └─ GET  /urls/{shortCode}/stats → StatsFunction     → DynamoDB (GetItem)
```

Three single-purpose Lambda functions, one DynamoDB table, no VPC, no idle compute.

---

## 🗄️ DynamoDB design

Single table, `url-shortener`:

| Attribute    | Type   | Notes                                               |
|--------------|--------|------------------------------------------------------|
| `shortCode`  | S (PK) | e.g. `aZ3xQ1k` — the only key anything looks up by  |
| `longUrl`    | S      | the redirect destination                              |
| `createdAt`  | N      | unix timestamp                                        |
| `clickCount` | N      | incremented atomically on every redirect              |
| `expiresAt`  | N      | optional unix timestamp; used as the DynamoDB TTL key |

**Design reasoning:**

- **Access pattern drives the key.** The only hot-path read is "given a short code, get the long URL," so `shortCode` is the partition key and every read is a single-digit-millisecond `GetItem`/`UpdateItem`. No secondary indexes, because nothing queries by `longUrl` or `createdAt`.
- **Uniqueness without locks.** `PutItem` with `ConditionExpression="attribute_not_exists(shortCode)"` gives a collision-free write with no separate check-then-write step. On collision, the Lambda just tries the next randomly generated code.
- **Click counting without a race condition.** `UpdateItem` with `SET clickCount = clickCount + :inc` is an atomic increment handled server-side by DynamoDB — concurrent redirects can't stomp on each other the way a naive get-then-put would.
- **Expiry without a cron job.** DynamoDB TTL deletes expired items in the background, and the redirect handler's condition expression also rejects an item past its `expiresAt` even if the TTL sweep hasn't run yet.
- **Billing mode:** `PAY_PER_REQUEST` — no capacity planning, effectively free at low volume.

---

## 🔌 API reference

| Method | Path                          | Body                                                                | Response                                              |
|--------|-------------------------------|----------------------------------------------------------------------|--------------------------------------------------------|
| POST   | `/urls`                       | `{"url": "https://...", "customCode": "optional", "ttlSeconds": 3600}` | `201 {"shortCode","shortUrl","longUrl"}`               |
| GET    | `/{shortCode}`                 | –                                                                     | `301` redirect, or `404`                                |
| GET    | `/urls/{shortCode}/stats`      | –                                                                     | `200 {"shortCode","longUrl","createdAt","clickCount"}` |

`customCode` and `ttlSeconds` are both optional.

```bash
curl -X POST "$API/urls" -H 'Content-Type: application/json' \
  -d '{"url":"https://www.anthropic.com"}'
# → {"shortCode":"aZ3xQ1k","shortUrl":"https://.../aZ3xQ1k"}
```

---

## 🚀 Deploy

Requires the [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) and AWS credentials configured (`aws configure`).

```bash
sam build
sam deploy --guided
```

`sam deploy --guided` asks for a stack name and region, then saves the answers to `samconfig.toml` so future deploys are just `sam deploy`. By default this deploys to the standard `execute-api.amazonaws.com` URL.

**Test it:**

```bash
API=$(aws cloudformation describe-stacks --stack-name <your-stack> \
  --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" --output text)

curl -X POST "$API/urls" -H 'Content-Type: application/json' \
  -d '{"url":"https://www.anthropic.com"}'

curl -i "$API/aZ3xQ1k"          # 301 Location: https://www.anthropic.com
curl "$API/urls/aZ3xQ1k/stats"  # {"clickCount":1,...}
```

---

## 🌐 Optional: custom domain via Route 53

By default the API is reachable at the standard `execute-api.amazonaws.com` URL, at no extra cost. To use a custom domain like `short.yourdomain.com` instead:

1. **Have a Route 53 hosted zone** for the domain (~$0.50/month, plus normal domain registration if you don't already own it).
2. **Request an ACM certificate**, in the *same region* as your stack:
   ```bash
   aws acm request-certificate \
     --domain-name short.yourdomain.com \
     --validation-method DNS \
     --region <your-region>
   ```
   Add the DNS validation CNAME ACM gives you to your hosted zone, then wait for `ISSUED` status.
3. **Uncomment the `Domain:` block** in `template.yaml` under the `HttpApi` resource and fill in your values:
   ```yaml
   HttpApi:
     Type: AWS::Serverless::HttpApi
     Properties:
       Domain:
         DomainName: short.yourdomain.com
         CertificateArn: arn:aws:acm:...
         Route53:
           HostedZoneId: Z0123456789ABCDEF
   ```
4. **Redeploy:** `sam build && sam deploy`.

Ongoing cost is just the ~$0.50/month hosted zone fee — API Gateway custom domain mappings and ACM public certificates are free.

---

## 🎓 What this teaches

- **REST API design** — resource-oriented routes, correct status codes (`201`, `301`, `404`, `409`), idempotency considerations for custom codes.
- **NoSQL data modeling** — designing a table around one access pattern instead of normalizing like a relational schema; conditional writes and atomic counters instead of locks.
- **Serverless architecture** — pay-per-use pricing, IAM least-privilege policies scoped to a single table, infrastructure as code with SAM/CloudFormation.

---

## 🔭 Natural extensions

- QR code generation endpoint for each short URL.
- An `ownerId` attribute + GSI, so users can list "my links" — a good next NoSQL lesson in adding an access pattern after the fact.
- Move click counting off the hot path with DynamoDB Streams → a separate aggregator Lambda.
- CloudFront in front of the API for edge caching and a global anycast IP.

---

## 🐛 Challenges & lessons learned

Three real issues came up during deployment — each a genuine AWS/CloudFormation gotcha rather than a typo:

- **Circular dependency between Lambda and API Gateway.** Setting a `BASE_URL` environment variable via `!Sub 'https://${HttpApi}...'` made every Lambda depend on the API (to read its ID) — but the API also depends on the Lambdas (to wire up routes via `Events:`). CloudFormation correctly refused the loop. **Fix:** derive the base URL at runtime from `event.requestContext.domainName` instead of baking it into the infrastructure.
- **SAM's `Fn::If` can't conditionally omit a whole resource property block.** Tried to make custom domain config optional via a `Conditions:`-gated `Fn::If`. But `AWS::Serverless::HttpApi`'s `Domain` property is expanded by the SAM transform macro *before* CloudFormation resolves conditions — so it saw an unresolved structure and rejected it as incomplete. **Fix:** keep the domain config out of the template by default, as a commented block to uncomment only when needed.
- **Case-sensitive Lambda runtime vs. case-insensitive local filesystem.** Deploying from Windows/WSL, the source files ended up as `CreateHandler.py` while the template's `Handler:` pointed at `create_handler.py`. Invisible locally (WSL doesn't care about case) but Lambda runs on Linux, which does — producing `Runtime.ImportModuleError` with no other symptoms. Diagnosed via `sam logs -n <FunctionName> --stack-name <stack>` and confirmed by inspecting `.aws-sam/build/<FunctionName>/` directly.

---

## 📄 License

MIT — do whatever you want with this.#   s e r v e r l e s s - u r l - s h o r t e n e r - A W S -  
 