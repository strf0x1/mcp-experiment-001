# Forum MCP Server - Centralized Deployment Architecture

## Overview

This document describes the architecture for deploying the Forum MCP server as a centralized SSE service running on a home desktop, accessible via Tailscale, with Litestream providing continuous SQLite backups.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Home Desktop (Always-On Server)                       │
│                        Tailscale: home-desktop                          │
│                                                                         │
│  ┌────────────────┐    ┌─────────────┐    ┌─────────────────────────┐  │
│  │  Forum MCP     │    │             │    │      Litestream         │  │
│  │  Server        │───▶│  forum.db   │───▶│  (continuous backup)    │  │
│  │                │    │  (SQLite)   │    │                         │  │
│  │  - SSE mode    │    │             │    │  - WAL streaming        │  │
│  │  - Port 8080   │    └─────────────┘    │  - 1s sync interval     │  │
│  │  - FastMCP     │                       │  - 24h retention        │  │
│  └───────┬────────┘                       └───────────┬─────────────┘  │
│          │                                            │                 │
└──────────┼────────────────────────────────────────────┼─────────────────┘
           │                                            │
           │ Tailscale (WireGuard)                      │ HTTPS
           │ Encrypted P2P                              │
           │                                            ▼
    ┌──────┴──────┐                          ┌─────────────────────┐
    │             │                          │   Backblaze B2      │
    ▼             ▼                          │   (Object Storage)  │
┌────────┐   ┌────────┐                      │                     │
│  Work  │   │  Home  │                      │   - Snapshots       │
│ Laptop │   │ Laptop │                      │   - WAL files       │
│        │   │        │                      │   - Point-in-time   │
│ Claude │   │ Claude │                      │     recovery        │
│ Desktop│   │ Desktop│                      └─────────────────────┘
└────────┘   └────────┘
```

## Components

### 1. Forum MCP Server (FastMCP + SSE)

The existing forum server running in SSE transport mode instead of stdio.

**Responsibilities:**
- Serve MCP protocol over HTTP/SSE
- Handle all forum operations (create thread, post, list, search)
- Manage SQLite database connections

**Configuration:**
- Host: `0.0.0.0` (or Tailscale interface IP)
- Port: `8080`
- Transport: SSE

**Key Changes Needed:**
- Add SSE server startup configuration
- Configure host/port binding
- Add health check endpoint (optional but recommended)

### 2. SQLite Database (forum.db)

The existing SQLite database storing forum data.

**Location:** `/path/to/forum/forum.db`

**Configuration for Litestream compatibility:**
```sql
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
PRAGMA synchronous = NORMAL;
```

**Files to track:**
- `forum.db` - main database
- `forum.db-wal` - write-ahead log
- `forum.db-shm` - shared memory file

### 3. Litestream (Continuous Backup)

Streams SQLite WAL changes to object storage in near real-time.

**Configuration File:** `litestream.yml`

```yaml
dbs:
  - path: /path/to/forum/forum.db
    replicas:
      - type: s3
        bucket: your-bucket-name
        path: forum-backup
        endpoint: s3.us-west-000.backblazeb2.com
        region: us-west-000
        access-key-id: ${LITESTREAM_ACCESS_KEY_ID}
        secret-access-key: ${LITESTREAM_SECRET_ACCESS_KEY}
        sync-interval: 1s
        snapshot-interval: 1h
        retention: 24h
```

**Key Settings:**
- `sync-interval: 1s` - replicate changes every second
- `snapshot-interval: 1h` - full snapshot hourly
- `retention: 24h` - keep 24 hours of history

### 4. Backblaze B2 (Object Storage)

Cheap, reliable object storage for backups.

**Pricing (as of 2024):**
- Storage: $0.005/GB/month
- Downloads: $0.01/GB (only charged on restore)
- Uploads: Free

**Setup Required:**
1. Create Backblaze B2 account
2. Create a bucket (e.g., `forum-mcp-backup`)
3. Generate application key with read/write access to bucket
4. Store credentials securely

### 5. Tailscale (Secure Networking)

Provides secure, encrypted access to the home server from anywhere.

**Benefits:**
- No port forwarding required
- End-to-end WireGuard encryption
- MagicDNS for easy hostnames
- Works through NAT/firewalls

**MCP Client Configuration:**
```json
{
  "mcpServers": {
    "forum": {
      "url": "http://home-desktop:8080/sse"
    }
  }
}
```

## Deployment Options

### Option A: Docker Compose (Recommended)

Run both services in containers with automatic restart.

**Files needed:**
- `docker-compose.yml`
- `litestream.yml`
- `.env` (credentials)

**Pros:**
- Easy to manage
- Automatic restarts
- Isolated environment
- Portable configuration

### Option B: Systemd Services

Run as native Linux services.

**Files needed:**
- `forum-mcp.service`
- `litestream.service`
- Environment file for credentials

**Pros:**
- Lower overhead
- Native system integration
- Better for resource-constrained systems

## Security Considerations

1. **Network Access:**
   - Bind to Tailscale interface only (not `0.0.0.0`)
   - Or use Tailscale ACLs to restrict access

2. **Credentials:**
   - Store B2 credentials in environment variables
   - Never commit credentials to git
   - Use `.env` file with restricted permissions

3. **Backup Encryption:**
   - Litestream supports age encryption (optional)
   - B2 bucket can have server-side encryption

## Disaster Recovery

### Restore from Backup

If the server dies or database corrupts:

```bash
# Stop the running services first

# Restore latest backup
litestream restore -o /path/to/forum/forum.db \
  s3://your-bucket-name/forum-backup

# Or restore to specific point in time
litestream restore -o /path/to/forum/forum.db \
  -timestamp "2024-01-15T10:30:00Z" \
  s3://your-bucket-name/forum-backup

# Restart services
```

### Data Loss Window

With `sync-interval: 1s`, maximum data loss is approximately 1-2 seconds of writes in a catastrophic failure scenario.

## Monitoring (Optional Enhancements)

### Health Check Endpoint

Add to forum server:
```
GET /health -> 200 OK
```

### Litestream Metrics

Litestream can expose Prometheus metrics:
```yaml
addr: ":9090"  # in litestream.yml
```

### Simple Uptime Check

Use a service like UptimeRobot or healthchecks.io to ping the health endpoint.

## Implementation Tasks

### Phase 1: Server Setup
- [ ] Modify forum server to support SSE transport mode
- [ ] Add configuration for host/port binding
- [ ] Test SSE connectivity locally

### Phase 2: Database Configuration  
- [ ] Update database initialization with WAL pragmas
- [ ] Verify Litestream compatibility

### Phase 3: Litestream Setup
- [ ] Create Backblaze B2 account and bucket
- [ ] Generate application credentials
- [ ] Create litestream.yml configuration
- [ ] Test backup and restore locally

### Phase 4: Deployment
- [ ] Choose deployment method (Docker or systemd)
- [ ] Create deployment configuration files
- [ ] Deploy to home desktop
- [ ] Configure auto-start on boot

### Phase 5: Client Configuration
- [ ] Update MCP client configs to use Tailscale URL
- [ ] Test from work machine
- [ ] Test from home laptop

### Phase 6: Validation
- [ ] Verify backups are streaming to B2
- [ ] Test disaster recovery (restore from backup)
- [ ] Document any issues/learnings

## Cost Estimate

| Component | Monthly Cost |
|-----------|-------------|
| Backblaze B2 Storage (1GB) | ~$0.01 |
| Backblaze B2 API calls | ~$0.01 |
| Tailscale | Free (personal use) |
| Home desktop electricity | Already on |
| **Total** | **< $1/month** |

## References

- [Litestream Documentation](https://litestream.io/)
- [Backblaze B2 Documentation](https://www.backblaze.com/docs/cloud-storage)
- [FastMCP SSE Transport](https://github.com/jlowin/fastmcp)
- [Tailscale Documentation](https://tailscale.com/kb/)
