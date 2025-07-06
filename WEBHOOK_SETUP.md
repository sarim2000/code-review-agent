# GitHub Webhook Setup Guide

This guide explains how to set up GitHub webhooks for automatic PR analysis.

## Overview

GitHub webhooks allow the code review agent to automatically analyze pull requests when they are opened or updated, without manual API calls.

## Setup Steps

### 1. Configure Webhook Secret (Optional but Recommended)

Add a webhook secret to your `.env` file for security:

```env
GITHUB_WEBHOOK_SECRET=your_random_secret_here
```

**Generate a secure secret:**
```bash
# Generate a random secret
openssl rand -hex 32
```

### 2. Configure GitHub Repository Webhook

1. Go to your GitHub repository
2. Navigate to **Settings** → **Webhooks**
3. Click **Add webhook**

**Webhook Configuration:**
- **Payload URL**: `https://your-domain.com/webhook/github`
- **Content type**: `application/json`
- **Secret**: (your webhook secret from step 1)
- **SSL verification**: Enable (recommended)

**Events to select:**
- ☑️ Pull requests
- ☐ Pushes (not needed)
- ☐ Everything else (not needed)

4. Click **Add webhook**

### 3. Test Webhook

After setup, GitHub will send a test ping. Check your logs to verify the webhook is working.

## Supported Events

The webhook currently supports these pull request actions:

### Triggers Analysis
- **opened** - New PR created
- **synchronize** - New commits pushed to PR
- **reopened** - Closed PR reopened

### Ignored Actions
- **closed** - PR closed/merged
- **assigned** - Assignee changed
- **labeled** - Labels modified
- **review_requested** - Reviewer requested

## Webhook Endpoint

**POST** `/webhook/github`

**Headers:**
- `X-GitHub-Event`: Event type (e.g., "pull_request")
- `X-Hub-Signature-256`: HMAC signature (if secret configured)
- `Content-Type`: application/json

**Response Format:**
```json
{
  "message": "PR analysis started for #123",
  "task_id": "abc-123-def",
  "pr_number": 123,
  "action": "opened"
}
```

## Security

### Signature Verification
When `GITHUB_WEBHOOK_SECRET` is configured, all webhook requests are verified using HMAC-SHA256 signatures.

**Security Features:**
- ✅ HMAC signature verification
- ✅ Constant-time comparison to prevent timing attacks
- ✅ Graceful handling when no secret is configured
- ✅ Proper error responses for invalid signatures

### Best Practices
1. **Always use HTTPS** for your webhook URL
2. **Set a strong webhook secret** (32+ random characters)
3. **Enable SSL verification** in GitHub settings
4. **Monitor webhook logs** for suspicious activity

## Troubleshooting

### Common Issues

**1. Webhook not triggering**
- Check the webhook URL is correct and accessible
- Verify the repository webhook is configured for "Pull requests" events
- Check your server logs for incoming requests

**2. Signature verification failed**
- Ensure `GITHUB_WEBHOOK_SECRET` matches the secret in GitHub settings
- Verify the secret doesn't have extra whitespace or characters

**3. Analysis not starting**
- Check Celery worker is running
- Verify Redis connection is working
- Check task service logs for errors

### Debug Webhook Payload

To debug webhook issues, you can log the incoming payload:

```python
# Temporarily add to webhook endpoint
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@router.post("/webhook/github")
async def github_webhook(request: Request, ...):
    payload = await request.body()
    logger.debug(f"Webhook payload: {payload.decode()}")
    # ... rest of handler
```

### Testing Locally

For local development, you can use tools like ngrok to expose your local server:

```bash
# Install ngrok
npm install -g ngrok

# Expose local server
ngrok http 8000

# Use the ngrok URL in GitHub webhook settings
# Example: https://abc123.ngrok.io/webhook/github
```

## Monitoring

### Webhook Delivery

GitHub provides webhook delivery information:
1. Go to repository **Settings** → **Webhooks**
2. Click on your webhook
3. View **Recent Deliveries** tab
4. Check delivery status and responses

### Application Monitoring

Monitor your application for:
- Webhook request volume
- Analysis task success/failure rates
- Response times
- Error patterns

## Rate Limiting

Consider implementing rate limiting for webhooks to prevent abuse:

```python
# Example rate limiting (not implemented)
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/webhook/github")
@limiter.limit("10/minute")
async def github_webhook(...):
    # ... webhook handler
```