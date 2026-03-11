# [Endpoint Name]

## Endpoint

```
METHOD /api/v1/path/to/endpoint
```

## Description

Brief description of what this endpoint does.

## Authentication

- **Required:** Yes/No
- **Type:** Bearer Token (JWT)

## Request

### Headers

```
Authorization: Bearer <token>
Content-Type: application/json
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `param1` | string | Yes | Description |

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `param1` | string | No | `default` | Description |

### Request Body

```json
{
  "field1": "value",
  "field2": 123,
  "field3": true
}
```

**Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `field1` | string | Yes | Description |
| `field2` | integer | No | Description |
| `field3` | boolean | No | Description |

## Response

### Success Response (200 OK)

```json
{
  "status": "success",
  "data": {
    "id": "123",
    "field": "value"
  }
}
```

### Error Responses

#### 400 Bad Request

```json
{
  "detail": "Validation error message"
}
```

#### 401 Unauthorized

```json
{
  "detail": "Not authenticated"
}
```

#### 429 Too Many Requests

```json
{
  "detail": "Rate limit exceeded"
}
```

## Rate Limiting

- **Limit:** X requests per minute
- **Scope:** Per user

## Example

### cURL

```bash
curl -X METHOD "http://localhost:8000/api/v1/path/to/endpoint" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "field1": "value",
    "field2": 123
  }'
```

### Python

```python
import requests

url = "http://localhost:8000/api/v1/path/to/endpoint"
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}
data = {
    "field1": "value",
    "field2": 123
}

response = requests.method(url, headers=headers, json=data)
print(response.json())
```

### JavaScript

```javascript
const response = await fetch('http://localhost:8000/api/v1/path/to/endpoint', {
  method: 'METHOD',
  headers: {
    'Authorization': 'Bearer <token>',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    field1: 'value',
    field2: 123
  })
});

const data = await response.json();
console.log(data);
```

## Notes

- Additional notes
- Important considerations

## See Also

- [Related endpoint 1](./endpoint-1.md)
- [Related endpoint 2](./endpoint-2.md)

