# 🔗 Serverless URL Shortener

A production-style **Serverless URL Shortener** built using **AWS Lambda, API Gateway, DynamoDB, and AWS SAM**. The application creates short URLs, redirects users using HTTP 301 responses, and tracks click statistics—all without managing servers.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange?logo=awslambda)
![API Gateway](https://img.shields.io/badge/API-Gateway-red)
![DynamoDB](https://img.shields.io/badge/DynamoDB-blue)
![AWS SAM](https://img.shields.io/badge/AWS-SAM-yellow)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🚀 Features

- Generate short URLs
- HTTP 301 redirection
- Click analytics
- Serverless architecture
- DynamoDB storage
- Infrastructure as Code with AWS SAM

---

## 🏗️ Architecture

```text
Client
   │
   ▼
API Gateway
   │
   ├── POST /urls ─────────► Create Lambda
   ├── GET /{shortCode} ───► Redirect Lambda
   └── GET /stats ─────────► Stats Lambda
                │
                ▼
           DynamoDB
```

---

## 🛠️ Tech Stack

- Python 3.12
- AWS Lambda
- Amazon API Gateway
- Amazon DynamoDB
- AWS SAM
- AWS CloudFormation
- IAM

---

## 📂 Project Structure

```text
Serverless-URL-shortener/
│
├── src/
│   ├── create_handler.py
│   ├── redirect_handler.py
│   ├── stats_handler.py
│
├── template.yaml
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 📌 API Endpoints

| Method | Endpoint | Description |
|---------|----------|-------------|
| POST | `/urls` | Create Short URL |
| GET | `/{shortCode}` | Redirect to Original URL |
| GET | `/urls/{shortCode}/stats` | Get URL Statistics |

---

## 🚀 Deployment

```bash
aws configure

sam build

sam deploy --guided
```

---

## 🧪 Testing

Create a Short URL

```bash
curl -X POST "$API/urls" \
-H "Content-Type: application/json" \
-d '{"url":"https://www.example.com"}'
```

Redirect

```bash
curl -i "$API/<shortCode>"
```

Get Statistics

```bash
curl "$API/urls/<shortCode>/stats"
```

---

## 📸 Screenshots

Add screenshots here after deployment.

- AWS Lambda
- API Gateway
- DynamoDB Table
- CloudFormation Stack
- Working API Demo

---

## 💡 Key Learnings

- Building REST APIs with AWS Lambda
- Infrastructure as Code using AWS SAM
- Single-table DynamoDB design
- Atomic counters for click tracking
- Serverless deployment with CloudFormation

---

## 🔮 Future Improvements

- Custom short codes
- QR Code generation
- User authentication
- Custom domain support
- Analytics dashboard
- CloudFront integration

---

## 📄 License

This project is licensed under the **MIT License**.