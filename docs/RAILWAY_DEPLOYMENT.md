# Railway Deployment Guide

**← [Back to Main README](../README.md)**

This guide walks through deploying the Haystack Data Simulator as a continuous service on Railway with TimescaleDB.

**Related Documentation**:
- [Service Mode Guide](SERVICE_MODE_SUMMARY.md) - Understanding continuous operation
- [Docker Setup](DOCKER_LOCAL_SETUP.md) - Local testing before deployment

## Overview

The simulator will run continuously on Railway, generating building data every 15 minutes and automatically catching up on any gaps when restarted.

## Prerequisites

- Railway account (https://railway.app)
- GitHub repository (for deployment)
- Basic knowledge of environment variables

## Step 1: Create TimescaleDB Instance

### Option A: Railway Template (Recommended)
1. Go to Railway dashboard
2. Click "New Project" → "Database" → "Add PostgreSQL"
3. Once created, enable TimescaleDB extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
   ```

### Option B: External TimescaleDB
- Use Timescale Cloud or your own instance
- Note the connection URL for later

## Step 2: Initialize Database Schema

### Run Schema Creation
```bash
# Connect to your Railway PostgreSQL instance
psql $DATABASE_URL

# Run the core schema
\i schema/sql_schema_core_v2.sql

# Run the simulator state schema
\i schema/simulator_state.sql
```

## Step 3: Deploy Simulator Service

### Push to GitHub
```bash
git add .
git commit -m "Add continuous service support"
git push origin main
```

### Deploy on Railway
1. Go to Railway dashboard
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect the Dockerfile and deploy

## Step 4: Configure Environment Variables

In Railway dashboard, add these environment variables:

### Required Variables
```bash
# Database connection (Railway provides this automatically if using Railway PostgreSQL)
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Or use individual settings
DB_HOST=your-db-host.railway.app
DB_PORT=5432
DB_NAME=railway
DB_USER=postgres
DB_PASSWORD=your-password
```

### Optional Variables
```bash
# Service configuration
SERVICE_INTERVAL_MINUTES=15
HEALTH_CHECK_PORT=8080
LOG_LEVEL=INFO
```

## Step 5: Verify Deployment

### Check Service Status
1. Open your Railway service logs
2. Look for:
   ```
   Service started successfully!
   Health check: http://0.0.0.0:8080/health
   ```

### Test Health Endpoint
Railway provides a public URL. Access:
```
https://your-service.railway.app/health
```

Should return:
```json
{
  "status": "healthy",
  "service": "haystack_simulator",
  "last_run": "2025-10-03T12:15:00Z"
}
```

## Service Behavior

### On First Start
1. Checks if building entities exist
2. Creates entities if needed
3. Detects any data gaps
4. Fills gaps from last data point to present
5. Starts generating data every 15 minutes

### On Restart
1. Loads existing entities
2. Detects last data timestamp
3. Calculates gap duration
4. Backfills missing intervals
5. Resumes continuous generation

### Pause/Resume Capability
- **Pause**: Stop the Railway service
- **Resume**: Restart the service
  - Automatically detects downtime
  - Fills gap with historical data
  - Continues normal operation

## Monitoring

### Health Checks
Railway automatically monitors `/health` endpoint:
- **Healthy**: Returns 200 status
- **Unhealthy**: Returns 503 status

### Logs
View logs in Railway dashboard:
```
=== Service started successfully!
=== Generating data for interval: 2025-10-03 12:15:00
=== Successfully generated 245 data points
```

### Validation
SSH into Railway service and run:
```bash
# Check data continuity
python validation/validate_data_continuity.py

# Check all points have data
python validation/validate_all_points_data.py
```

## Scaling Considerations

### Single Instance
- Recommended for data consistency
- Prevents duplicate data generation
- Configure: `numReplicas: 1` in railway.json

### Resource Requirements
- **Memory**: 512MB minimum, 1GB recommended
- **CPU**: 0.5 vCPU sufficient
- **Storage**: Database grows ~50MB per week

## Cost Optimization

### Pause When Not Needed
1. Stop Railway service when not in use
2. Service automatically catches up on restart
3. Totalizers preserve continuity

### Data Retention
Configure in database:
```sql
-- Keep only last 30 days
SELECT drop_chunks('values_demo', INTERVAL '30 days');
```

## Troubleshooting

### Service Won't Start
**Check logs for:**
- Database connection errors
- Schema missing errors
- Permission issues

**Solutions:**
1. Verify DATABASE_URL is correct
2. Ensure schema is created
3. Check database user permissions

### No Data Being Generated
**Symptoms:**
- Health check passes
- No new data in database

**Solutions:**
1. Check scheduler logs
2. Verify entity_map loaded
3. Check for errors in generation loop

### Gap Filling Takes Too Long
**Symptoms:**
- Service startup >5 minutes
- Large backfill operations

**Solutions:**
1. Limit gap fill in config
2. Batch fill in smaller chunks
3. Consider manual backfill

## Manual Operations

### Reset and Regenerate
```bash
# Connect to service
python src/main.py --reset --days 30
```

### Check Service State
```bash
# Query simulator state
psql $DATABASE_URL -c "SELECT * FROM core.simulator_state;"
```

### Manual Gap Fill
```python
from service.state_manager import StateManager
from service.gap_filler import GapFiller

# Fill specific gap
gap_filler.fill_gap_incremental(start_time, end_time, totalizers)
```

## Production Best Practices

1. **Enable Monitoring**: Use Railway metrics
2. **Set Alerts**: Configure health check alerts
3. **Backup Database**: Regular Timescale backups
4. **Log Rotation**: Configure log retention
5. **Version Control**: Tag releases

## Support

- **Railway Docs**: https://docs.railway.app
- **TimescaleDB Docs**: https://docs.timescale.com
- **Project Issues**: [GitHub Issues](https://github.com/your-repo/issues)

## Next Steps

After successful deployment:
1. Set up monitoring dashboards
2. Configure data retention policies
3. Create front-end application
4. Build analytics queries
