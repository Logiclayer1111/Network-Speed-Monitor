# Network Speed Monitor – API Documentation

Base URL: `http://localhost:8000/api`

All endpoints return JSON.  
The API is served by a FastAPI server and works together with the poller service.

---

## Health & Info

### `GET /`

General API information.

**Response:**

```json
{
  "name": "Network Speed Monitor API",
  "version": "1.0.0",
  "endpoints": [
    "/api/daily/{date}",
    "/api/week",
    "/api/worst-times",
    "/api/stats",
    "/api/health"
  ]
}
```
