# Rate Limiting Implementation

**Date**: 2025-11-05
**Status**: ✅ IMPLEMENTED
**Library**: slowapi 0.1.9

## Overview

Rate limiting has been implemented across all API endpoints to prevent abuse and ensure fair resource allocation. The system uses `slowapi`, a FastAPI-compatible rate limiter with in-memory storage (upgradeable to Redis).

## Rate Limit Tiers

| Tier | Limit | Endpoints |
|------|-------|-----------|
| **General** | 100/minute | Health checks, status, static pages |
| **Query** | 30/minute | Search, chat, research, RAG queries |
| **Upload** | 10/minute | File uploads (documents, images, OCR) |
| **Compute** | 5/minute | Code execution, heavy operations |
| **Auth** | 5/minute | Authentication endpoints (future) |

## Implementation Details

### Architecture

```
Request → SlowAPIMiddleware → Rate Limiter → Route Handler
                                    ↓
                            Check IP/User Rate
                                    ↓
                            Allow or Return 429
```

### Key Files

**`src/web/middleware/rate_limiter.py`**
- Core rate limiting logic
- Custom identifier function (IP-based, extendable to user-based)
- Rate limit exceeded handler
- Preset limit configurations

**`src/web/app.py`**
- Integrates rate limiting into FastAPI app
- Calls `setup_rate_limiting(app)` during initialization

**Applied to Routers:**
- `src/web/routers/query.py`: Query endpoint (30/min)
- `src/web/routers/code.py`: Code execution (5/min)
- `src/web/routers/rag.py`: RAG upload (10/min), RAG query (30/min)
- `src/web/routers/multimodal.py`: OCR (10/min), Vision (10/min)

### Identifier Strategy

**Current**: IP-based identification
```python
def get_identifier(request: Request) -> str:
    # Handles X-Forwarded-For for proxies/load balancers
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = get_remote_address(request)
    return f"ip:{ip}"
```

**Future Enhancement**: User-based identification (requires authentication)
```python
user_id = request.state.user_id if hasattr(request.state, 'user_id') else None
if user_id:
    return f"user:{user_id}"
```

### Response Headers

Rate limit information is automatically added to response headers:

```http
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 25
X-RateLimit-Reset: 1699132800
```

### Error Response (429 Too Many Requests)

```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later.",
  "detail": "30 per 1 minute",
  "retry_after": 60
}
```

HTTP Header: `Retry-After: 60`

## Configuration

### Environment Variables

```bash
# .env or environment
RATE_LIMIT_ENABLED=true
RATE_LIMIT_STORAGE=memory://  # or redis://localhost:6379
```

### Disable Rate Limiting

For development or testing:

```bash
export RATE_LIMIT_ENABLED=false
python -m src.web.app
```

### Storage Backends

**In-Memory (Default)**
- Simple, no dependencies
- Suitable for single-server deployments
- Lost on server restart

```bash
RATE_LIMIT_STORAGE=memory://
```

**Redis (Production Recommended)**
- Persistent across restarts
- Supports multi-server deployments
- Requires Redis instance

```bash
RATE_LIMIT_STORAGE=redis://localhost:6379
# Or with authentication
RATE_LIMIT_STORAGE=redis://:password@localhost:6379/0
```

## Usage in Code

### Applying Rate Limits to Routes

```python
from src.web.middleware import limiter, get_limit

@router.post("/endpoint")
@limiter.limit(get_limit("query"))  # 30/minute
async def my_endpoint(request: Request):
    # Handler code
    pass
```

### Custom Rate Limits

```python
@router.post("/special")
@limiter.limit("5/minute")  # Custom limit
async def special_endpoint(request: Request):
    pass
```

### Multiple Limits

```python
@router.post("/strict")
@limiter.limit("10/minute")
@limiter.limit("100/hour")
@limiter.limit("1000/day")
async def strict_endpoint(request: Request):
    pass
```

## Testing Rate Limits

### Manual Testing

```bash
# Test query endpoint (30/min)
for i in {1..35}; do
  curl -X POST http://localhost:8000/query \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "query=test" &
done
wait
# Requests 31-35 should return 429
```

### Automated Testing

```python
import asyncio
import aiohttp

async def test_rate_limit():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(35):
            task = session.post(
                "http://localhost:8000/query",
                data={"query": "test"}
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

        status_codes = [r.status for r in responses]
        assert status_codes.count(200) == 30
        assert status_codes.count(429) == 5

asyncio.run(test_rate_limit())
```

## Monitoring

### Log Messages

Rate limit events are logged:

```
WARNING: Rate limit exceeded for ip:192.168.1.100 on /query
```

### Response Headers

Monitor `X-RateLimit-*` headers in responses to track usage patterns.

### Future: Metrics Dashboard

Consider integrating with Prometheus/Grafana:
- Track requests per endpoint
- Identify abusive IPs
- Monitor rate limit hits

## Security Considerations

### DDoS Protection

Rate limiting provides basic DDoS protection but should be combined with:
- **Reverse Proxy**: nginx/Cloudflare rate limiting
- **IP Filtering**: Block known malicious IPs
- **CDN**: Distribute load across edge servers

### Bypass Prevention

**IP Spoofing**: The system checks `X-Forwarded-For` header, which should only be trusted behind a reverse proxy. Configure your proxy to strip untrusted headers.

**Distributed Attacks**: If attacks come from many IPs, consider:
- Lowering rate limits
- Adding CAPTCHA for suspicious patterns
- IP reputation scoring

### User-Based Limits

Once authentication is added:
1. Update `get_identifier()` to use user IDs
2. Set different limits per user tier (free/premium)
3. Track usage in database for billing

## Performance Impact

**Overhead**: ~1-2ms per request (negligible)

**Memory Usage**: In-memory storage uses ~100 bytes per unique IP

**Scalability**:
- Single server: In-memory storage fine
- Multiple servers: Switch to Redis backend

## Troubleshooting

### Issue: Rate limit applied incorrectly

**Symptom**: Getting 429 when shouldn't

**Check**:
1. Verify `RATE_LIMIT_ENABLED=true`
2. Check if behind proxy sending `X-Forwarded-For`
3. Look for rate limit in logs

### Issue: Rate limit not working

**Symptom**: Can exceed limits without 429

**Check**:
1. Verify `RATE_LIMIT_ENABLED=true` in environment
2. Check `setup_rate_limiting(app)` is called in `app.py`
3. Ensure `@limiter.limit()` decorator is applied to route
4. Verify middleware is added: `app.add_middleware(SlowAPIMiddleware)`

### Issue: Lost rate limit state on restart

**Solution**: Switch to Redis backend

```bash
# Install Redis
docker run -d -p 6379:6379 redis:latest

# Update .env
RATE_LIMIT_STORAGE=redis://localhost:6379
```

## Future Enhancements

### Phase 1 (Current)
- ✅ IP-based rate limiting
- ✅ Tiered limits per endpoint type
- ✅ Custom error messages
- ✅ Response headers

### Phase 2 (Next)
- [ ] User-based identification
- [ ] Different limits per user tier
- [ ] Rate limit dashboard
- [ ] Usage analytics

### Phase 3 (Future)
- [ ] Dynamic rate limits based on server load
- [ ] IP reputation scoring
- [ ] Automatic CAPTCHA for suspicious patterns
- [ ] Webhook notifications for limit violations

## References

- **slowapi Documentation**: https://slowapi.readthedocs.io/
- **FastAPI Rate Limiting**: https://fastapi.tiangolo.com/
- **OWASP Rate Limiting**: https://owasp.org/www-community/controls/Blocking_Brute_Force_Attacks

## Related Files

- Implementation: `src/web/middleware/rate_limiter.py`
- Configuration: `.env.example`
- Security Audit: `FILE_UPLOAD_SECURITY_AUDIT.md`
- Main App: `src/web/app.py`
