# Troubleshooting Guide

Common issues and solutions for the Code Review Agent.

## Celery Issues

### ValueError: Exception information must include the exception type

**Symptoms:**
```
ValueError: Exception information must include the exception type
```

**Cause:**
This occurs when Celery tasks fail but exception information isn't properly serialized to the result backend.

**Solution:**
The system now includes improved error handling:
- Proper exception metadata is included in task state updates
- Simple Exception objects are raised to avoid serialization issues
- Automatic retry logic for transient failures
- Comprehensive logging for debugging

**Prevention:**
- Monitor Celery worker logs for task failures
- Ensure Redis is properly configured and accessible
- Use proper exception handling in task code

### Celery Worker Not Starting

**Symptoms:**
- Tasks remain in PENDING state
- No worker processes visible

**Solution:**
```bash
# Check if Redis is running
redis-cli ping

# Start Celery worker with verbose logging
uv run celery -A app.core.celery_app worker --loglevel=debug

# Check for import errors
uv run python -c "from app.tasks.analysis_tasks import analyze_pr_task; print('Import successful')"
```

### Tasks Hanging or Timing Out

**Symptoms:**
- Tasks stuck in PROGRESS state
- No response from analysis endpoints

**Solution:**
- Check task time limits in `celery_app.py`
- Verify GitHub API connectivity
- Check OpenAI API rate limits
- Monitor Redis memory usage

## GitHub Integration Issues

### Invalid Repository URL

**Symptoms:**
```
ValueError: Invalid GitHub repository URL
```

**Solution:**
Ensure URLs are in the correct format:
- `https://github.com/owner/repo`
- `git@github.com:owner/repo.git`
- `github.com/owner/repo`

### GitHub API Rate Limiting

**Symptoms:**
- 403 Forbidden errors
- `X-RateLimit-Remaining: 0` headers

**Solution:**
- Provide GitHub token for higher rate limits
- Implement request caching
- Add retry logic with exponential backoff

### Webhook Signature Verification Failed

**Symptoms:**
- 403 Forbidden on webhook endpoint
- "Invalid webhook signature" errors

**Solution:**
```bash
# Verify webhook secret matches
echo "Your secret" | openssl dgst -sha256 -hmac "your_webhook_secret"

# Check environment variable
echo $GITHUB_WEBHOOK_SECRET

# Test without signature (temporarily remove secret)
unset GITHUB_WEBHOOK_SECRET
```

## OpenAI Integration Issues

### OpenAI API Authentication Failed

**Symptoms:**
```
openai.AuthenticationError: Error code: 401
```

**Solution:**
- Verify API key is correct
- Check key has sufficient credits
- Ensure key is properly set in environment

### OpenAI Rate Limiting

**Symptoms:**
- 429 Too Many Requests errors
- Slow response times

**Solution:**
- Implement request queuing
- Add exponential backoff
- Monitor usage dashboard
- Consider upgrading to higher tier

### AI Analysis Fallback

**Symptoms:**
- "AI analysis failed, falling back to rule-based" messages

**Solution:**
This is expected behavior when:
- OpenAI API is unavailable
- Rate limits are exceeded
- Invalid API responses

The system automatically falls back to rule-based analysis.

## API Issues

### FastAPI Server Won't Start

**Symptoms:**
```
Address already in use
```

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
uv run uvicorn app.main:app --port 8001
```

### CORS Issues

**Symptoms:**
- Browser console errors about CORS
- Failed requests from web applications

**Solution:**
Add CORS middleware to `app/main.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Redis Issues

### Redis Connection Failed

**Symptoms:**
```
redis.exceptions.ConnectionError
```

**Solution:**
```bash
# Check if Redis is running
redis-cli ping

# Start Redis (macOS with Homebrew)
brew services start redis

# Start Redis (Linux)
sudo systemctl start redis

# Check Redis configuration
redis-cli info
```

### Redis Memory Issues

**Symptoms:**
- Tasks failing with memory errors
- Slow task processing

**Solution:**
```bash
# Check Redis memory usage
redis-cli info memory

# Clear all keys (development only)
redis-cli flushall

# Set memory policy
redis-cli config set maxmemory-policy allkeys-lru
```

## Docker Issues

### Container Build Failures

**Symptoms:**
- Docker build errors
- Missing dependencies

**Solution:**
```bash
# Build with no cache
docker-compose build --no-cache

# Check build logs
docker-compose logs api

# Verify uv installation
docker run --rm -it python:3.12-slim which uv
```

### Container Networking Issues

**Symptoms:**
- Services can't communicate
- Redis connection refused

**Solution:**
```bash
# Check container logs
docker-compose logs redis
docker-compose logs celery-worker

# Verify network connectivity
docker-compose exec api ping redis

# Restart services
docker-compose down && docker-compose up
```

## Performance Issues

### Slow Analysis Times

**Symptoms:**
- Long task execution times
- High memory usage

**Solution:**
- Reduce file count in PR analysis
- Implement result caching
- Optimize AI prompts
- Use faster Redis configuration

### Memory Leaks

**Symptoms:**
- Increasing memory usage over time
- Worker crashes

**Solution:**
- Monitor worker memory usage
- Restart workers periodically
- Check for circular references
- Use memory profiling tools

## Monitoring and Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Monitor Task Queue

```bash
# View active tasks
uv run celery -A app.core.celery_app inspect active

# View reserved tasks
uv run celery -A app.core.celery_app inspect reserved

# Purge queue
uv run celery -A app.core.celery_app purge
```

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Redis health
redis-cli ping

# Celery worker health
uv run celery -A app.core.celery_app inspect ping
```

## Getting Help

1. Check application logs
2. Review error messages carefully
3. Test individual components
4. Create minimal reproduction case
5. Check GitHub issues for similar problems