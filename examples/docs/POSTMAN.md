# Postman Collections for Servicekit Examples

This directory contains Postman Collection v2.1 JSON files that you can import directly into Postman to test Servicekit services.

## Available Collections

### Core Collections

#### core_api.postman_collection.json
**User CRUD Operations**
- Complete user lifecycle (Create, Read, Update, Delete)
- Pagination examples
- Schema introspection
- Auto-captured user IDs
- Seed data on startup

### Authentication Collections

#### auth_basic.postman_collection.json
**API Key Authentication Workflow**
- Multiple API key sources (file, environment, secrets)
- Authentication failures (missing/invalid keys)
- Full CRUD workflow with auth
- Key rotation examples
- RFC 9457 error responses

### Infrastructure Collections

#### monitoring_api.postman_collection.json
**Prometheus Metrics & System Info**
- Health checks
- Prometheus metrics endpoint
- System information
- OpenTelemetry integration

## How to Import

### Option 1: Import via Postman UI

1. Open Postman
2. Click **Import** button (top-left)
3. Select **Upload Files** tab
4. Choose one or more `.postman_collection.json` files
5. Click **Import**

### Option 2: Import via URL (if hosted on GitHub)

1. Open Postman
2. Click **Import** → **Link**
3. Paste the raw GitHub URL to the JSON file
4. Click **Continue** → **Import**

Example URL:
```
https://raw.githubusercontent.com/winterop-com/servicekit/main/examples/docs/core_api.postman_collection.json
```

### Option 3: Drag and Drop

1. Open Postman
2. Drag the `.postman_collection.json` file into the Postman window
3. Collection will be imported automatically

## Collection Structure

Each collection is organized into logical folders:

```
Collection
├── 1. Health & System Info
│   ├── Check Service Health
│   └── Get System Information
├── 2. User Management (CRUD)
│   ├── Create User
│   ├── List All Users
│   ├── List Users (Paginated)
│   ├── Get User by ID
│   ├── Update User
│   ├── Delete User
│   └── Get User Schema
├── 3. Authentication Tests (auth collections)
│   ├── Access Without Auth (401)
│   ├── Access With Invalid Key (401)
│   └── Access With Valid Key (200)
└── 4. Custom Operations
    └── Heavy Processing Job
```

## Collection Variables

Each collection includes pre-configured variables:

| Variable | Default Value | Description |
|----------|--------------|-------------|
| `baseUrl` | `http://127.0.0.1:8000` | API base URL |
| `user_id` | (auto-set) | User ID from create |
| `job_id` | (auto-set) | Job ID from async operations |
| `api_key` | `sk_dev_abc123` | API key for authenticated requests |

**Auto-set variables:** Test scripts automatically capture IDs from responses and store them in collection variables for subsequent requests.

## Usage Workflow

### Core API Workflow (User CRUD)

1. **Start the service:**
   ```bash
   fastapi dev examples/core_api.py
   ```

2. **Check service health:**
   - Run: `1. Health & System Info` → `Check Service Health`
   - Verify: Status 200, `"status": "healthy"`

3. **Create a user:**
   - Run: `2. User Management` → `Create User`
   - Auto-captured: `user_id` variable
   - Body:
     ```json
     {
       "username": "alice",
       "email": "alice@example.com",
       "full_name": "Alice Smith",
       "is_active": true
     }
     ```

4. **List users:**
   - Run: `2. User Management` → `List All Users`
   - See all users including seeded data

5. **Get user by ID:**
   - Run: `2. User Management` → `Get User by ID`
   - Uses auto-captured `{{user_id}}`

6. **Update user:**
   - Run: `2. User Management` → `Update User`
   - Modify user details

7. **Delete user:**
   - Run: `2. User Management` → `Delete User`
   - Removes the user

8. **Get schema:**
   - Run: `2. User Management` → `Get User Schema`
   - View Pydantic JSON schema

### Authentication Workflow (auth_basic)

1. **Start the service:**
   ```bash
   # Create API keys file
   echo "sk_dev_abc123" > api_keys.txt
   echo "sk_dev_xyz789" >> api_keys.txt

   fastapi dev examples/auth_basic.py
   ```

2. **Test unauthenticated access:**
   - Run: `1. Health & System Info` → `Check Service Health`
   - Verify: Status 200 (health endpoints are public)

3. **Test authentication failures:**
   - Run: `3. Authentication Tests` → `Access Without Auth`
   - Verify: Status 401, missing auth header error
   - Run: `3. Authentication Tests` → `Access With Invalid Key`
   - Verify: Status 401, invalid key error

4. **Create user with valid key:**
   - Run: `2. User Management` → `Create User`
   - Uses: `X-API-Key: {{api_key}}` header
   - Verify: Status 200, user created

5. **Perform authenticated CRUD:**
   - Run other requests in `2. User Management`
   - All automatically use `{{api_key}}` header

6. **Test key rotation:**
   - Update `api_key` variable to `sk_dev_xyz789`
   - Run: `2. User Management` → `List All Users`
   - Verify: Both keys work (zero-downtime rotation)

### Monitoring Workflow

1. **Start the service:**
   ```bash
   fastapi dev examples/monitoring_api.py
   ```

2. **Check health:**
   - Run: `1. Health & System Info` → `Check Service Health`

3. **Get Prometheus metrics:**
   - Run: `2. Monitoring` → `Get Prometheus Metrics`
   - View metrics in Prometheus text format

4. **Get system info:**
   - Run: `1. Health & System Info` → `Get System Information`
   - See service metadata

### Running the Complete Workflow

Use Postman's **Collection Runner** to execute all requests in sequence:

1. Right-click collection → **Run collection**
2. Select requests to run (or run all)
3. Set iterations: 1
4. Set delay: 500ms (between requests)
5. Click **Run**

**Note:** Collection Runner executes requests sequentially. For async jobs, you may need to manually poll status.

## Example Requests

### core_api Collection

**Create User:**
```json
POST /api/v1/users
{
  "username": "bob",
  "email": "bob@example.com",
  "full_name": "Bob Johnson",
  "is_active": true
}
```

**List Users (Paginated):**
```
GET /api/v1/users?page=1&size=10
```

**Update User:**
```json
PUT /api/v1/users/{{user_id}}
{
  "username": "bob",
  "email": "bob.johnson@example.com",
  "full_name": "Robert Johnson",
  "is_active": true
}
```

### auth_basic Collection

**Access With Valid Key:**
```
GET /api/v1/users
Headers:
  X-API-Key: sk_dev_abc123
```

**Create User (Authenticated):**
```json
POST /api/v1/users
Headers:
  X-API-Key: sk_dev_abc123
Body:
{
  "username": "charlie",
  "email": "charlie@example.com",
  "full_name": "Charlie Brown",
  "is_active": true
}
```

### monitoring_api Collection

**Get Metrics:**
```
GET /metrics
```

Response (Prometheus format):
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/health"} 5.0

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
...
```

## Environment Variables

To use collections across different environments (dev, staging, production), create Postman environments:

### Development Environment
```json
{
  "name": "Servicekit Dev",
  "values": [
    {
      "key": "baseUrl",
      "value": "http://127.0.0.1:8000",
      "enabled": true
    },
    {
      "key": "api_key",
      "value": "sk_dev_abc123",
      "enabled": true
    }
  ]
}
```

### Production Environment
```json
{
  "name": "Servicekit Production",
  "values": [
    {
      "key": "baseUrl",
      "value": "https://api.example.com",
      "enabled": true
    },
    {
      "key": "api_key",
      "value": "sk_prod_secret_key",
      "enabled": true
    }
  ]
}
```

**To create environments:**
1. Click **Environments** (left sidebar)
2. Click **+** to create new environment
3. Add `baseUrl` and `api_key` variables
4. Select environment from dropdown (top-right)

## Test Scripts

Collections include test scripts that automatically:
- Extract IDs from responses
- Store in collection variables
- Enable request chaining
- Validate response structure

**Example test script:**
```javascript
// Save user ID for subsequent requests
if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.collectionVariables.set('user_id', response.id);
}

// Validate response
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has required fields", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('id');
    pm.expect(jsonData).to.have.property('username');
    pm.expect(jsonData).to.have.property('email');
});
```

## Troubleshooting

### Connection Refused
**Error:** `Error: connect ECONNREFUSED 127.0.0.1:8000`
**Solution:** Start the service with `fastapi dev examples/core_api.py`

### Variable Not Set
**Error:** `{{user_id}}` appears in URL instead of actual value
**Solution:** Run "Create User" request first to auto-set the variable

### Authentication Failed
**Error:** Status 401, "Missing authentication header"
**Solution:** Ensure `X-API-Key` header is set with valid API key

### Invalid ULID
**Error:** Status 400, "Invalid ULID format"
**Solution:** ULIDs are auto-generated - use the ID from create response

### User Not Found
**Error:** Status 404, "User not found"
**Solution:** Create a user first, or use an existing user ID from the list

## Advanced Usage

### Testing Different Scenarios

1. **Test pagination:**
   - Create 10+ users
   - Use "List Users (Paginated)" with different `page` and `size` params
   - Compare with "List All Users"

2. **Test validation:**
   - Create user with invalid email format
   - Create user with missing required fields
   - Verify RFC 9457 error responses

3. **Test concurrency:**
   - Use Collection Runner with multiple iterations
   - Test concurrent user creation
   - Verify no conflicts

### Batch Testing

Use Collection Runner with data files:

1. Create CSV with test data:
   ```csv
   username,email,full_name
   alice,alice@example.com,Alice Smith
   bob,bob@example.com,Bob Johnson
   charlie,charlie@example.com,Charlie Brown
   ```

2. Collection Runner → Select data file
3. Map CSV columns to request variables
4. Run collection with multiple iterations

### Monitoring and Logging

Enable Postman Console to see:
- Request/response details
- Variable updates
- Script execution logs
- Network timings

**To open:** View → Show Postman Console (or Cmd+Alt+C / Ctrl+Alt+C)

## Collection Maintenance

### Updating baseUrl

If service runs on different port:
1. Go to collection → Variables tab
2. Update `baseUrl` to `http://127.0.0.1:PORT`
3. Save collection

### Resetting Variables

To clear all auto-set IDs:
1. Click collection → Variables tab
2. Clear values for `user_id`, `job_id`, etc.
3. Save changes

### Adding Custom Headers

To add headers to all requests:
1. Collection → Edit
2. Go to Authorization or Pre-request Script tab
3. Add headers globally

## Exporting for Team Sharing

### Export Collection

1. Right-click collection → Export
2. Select Collection v2.1 format
3. Save JSON file
4. Share with team via Git or file sharing

### Export Environment

1. Click environment → ... (three dots)
2. Select Export
3. Save JSON file
4. Share alongside collection

## CI/CD Integration (Newman)

Run collections in CI/CD with Newman:

```bash
# Install Newman
npm install -g newman

# Run collection
newman run examples/docs/core_api.postman_collection.json \
  --environment prod-environment.json \
  --reporters cli,junit

# Run with delay between requests
newman run examples/docs/auth_basic.postman_collection.json \
  --delay-request 500
```

## Next Steps

- **Read documentation:** See [README.md](README.md) for detailed guides
- **Explore API:** Use Postman's documentation feature to generate API docs
- **Automate tests:** Convert collections to Newman scripts for CI/CD
- **Share collections:** Export and share with team members
- **Create environments:** Set up dev, staging, and production environments

## Related Files

- [README.md](README.md) - General API workflow overview and cURL examples
- [../core_api.py](../core_api.py) - User CRUD service source code
- [../auth_basic.py](../auth_basic.py) - Authentication example source code
- [../../CLAUDE.md](../../CLAUDE.md) - Architecture and API reference

## Support

For issues or questions:
- Check example source code in `examples/*.py`
- Review server logs for detailed error messages
- Consult [CLAUDE.md](../../CLAUDE.md) for API reference
- Visit interactive docs at `http://127.0.0.1:8000/docs`
