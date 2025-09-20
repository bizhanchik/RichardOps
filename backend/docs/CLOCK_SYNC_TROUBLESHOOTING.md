# Clock Synchronization Troubleshooting Guide

## 🚨 CRITICAL ISSUE: Massive Time Difference Detected

Your monitoring system detected a **1.8-hour time difference** between client and server systems. This is a critical clock synchronization issue that needs immediate attention.

### Current Status
- **Time Difference**: ~6507 seconds (1.8 hours)
- **Client Time**: Behind server time
- **Emergency Fix**: Applied (HMAC_TIMESTAMP_WINDOW=7200s)
- **System Status**: Temporarily functional

## 🔍 Diagnosis Steps

### 1. Check Current System Times

**On Client System (Go Agent):**
```bash
# Check current time
date
timedatectl status  # Linux
Get-Date           # Windows PowerShell

# Check timezone
timedatectl list-timezones | grep -i utc  # Linux
[System.TimeZoneInfo]::Local              # Windows
```

**On Server System (Backend):**
```bash
# Check current time
date
timedatectl status  # Linux
Get-Date           # Windows PowerShell

# Check Docker container time
docker exec monitoring-backend-prod date
```

### 2. Verify Time Sources

**Check NTP Status:**
```bash
# Linux
timedatectl show-timesync --all
ntpq -p
chrony sources  # If using chrony

# Windows
w32tm /query /status
w32tm /query /peers
```

### 3. Check Network Time Synchronization

**Test NTP Connectivity:**
```bash
# Test NTP server connectivity
ntpdate -q pool.ntp.org
ntpdate -q time.google.com
ntpdate -q time.cloudflare.com

# Windows
w32tm /stripchart /computer:pool.ntp.org /samples:3
```

## 🔧 Fix Procedures

### Option 1: Linux Systems (Recommended)

**Install and Configure NTP:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ntp ntpdate

# CentOS/RHEL/Rocky
sudo yum install ntp ntpdate
# or
sudo dnf install ntp ntpdate

# Configure NTP
sudo nano /etc/ntp.conf

# Add these servers if not present:
server pool.ntp.org iburst
server time.google.com iburst
server time.cloudflare.com iburst

# Restart NTP service
sudo systemctl restart ntp
sudo systemctl enable ntp

# Force immediate sync
sudo ntpdate -s pool.ntp.org
```

**Alternative: Using systemd-timesyncd:**
```bash
# Enable time synchronization
sudo timedatectl set-ntp true

# Configure timesyncd
sudo nano /etc/systemd/timesyncd.conf

# Add:
[Time]
NTP=pool.ntp.org time.google.com
FallbackNTP=time.cloudflare.com

# Restart service
sudo systemctl restart systemd-timesyncd
sudo systemctl enable systemd-timesyncd

# Check status
timedatectl status
```

### Option 2: Windows Systems

**Configure Windows Time Service:**
```powershell
# Run as Administrator
# Stop Windows Time service
net stop w32time

# Configure time servers
w32tm /config /manualpeerlist:"pool.ntp.org,time.google.com,time.cloudflare.com" /syncfromflags:manual /reliable:yes /update

# Start Windows Time service
net start w32time

# Force immediate sync
w32tm /resync /force

# Check status
w32tm /query /status
```

### Option 3: Docker Container Time Sync

**If running in Docker:**
```bash
# Check if container inherits host time
docker exec monitoring-backend-prod date
docker exec go-client-container date

# Restart containers to inherit corrected host time
docker-compose restart

# For persistent fix, ensure host system time is correct first
```

## 🔍 Verification Steps

### 1. Verify Time Synchronization

**Check time difference:**
```bash
# On both systems, run simultaneously:
date +"%Y-%m-%d %H:%M:%S %Z"

# Should show minimal difference (< 1 second)
```

### 2. Test Monitoring System

**Check logs for timestamp errors:**
```bash
# Monitor backend logs
docker-compose logs -f monitoring-backend

# Look for these messages:
# ✅ Good: No "Request timestamp is stale" errors
# ⚠️  Warning: "Clock drift detected" (should be < 60s)
# ❌ Bad: "Request timestamp is stale" errors continue
```

### 3. Gradual Security Hardening

**Once clocks are synchronized, gradually reduce timestamp window:**

```bash
# Step 1: Reduce to 1 hour (after confirming sync works)
echo "HMAC_TIMESTAMP_WINDOW=3600" >> .env
docker-compose restart monitoring-backend

# Step 2: Reduce to 10 minutes (after 24h of stable operation)
echo "HMAC_TIMESTAMP_WINDOW=600" >> .env
docker-compose restart monitoring-backend

# Step 3: Return to secure default (after another 24h)
echo "HMAC_TIMESTAMP_WINDOW=300" >> .env
docker-compose restart monitoring-backend
```

## 🚨 Emergency Rollback

**If issues persist after clock sync:**
```bash
# Temporarily increase window again
echo "HMAC_TIMESTAMP_WINDOW=7200" >> .env
docker-compose restart monitoring-backend
```

## 📊 Monitoring and Alerts

### Set Up Clock Drift Monitoring

**Create monitoring script:**
```bash
#!/bin/bash
# clock_monitor.sh

CLIENT_TIME=$(ssh client-system 'date +%s')
SERVER_TIME=$(date +%s)
DIFF=$((SERVER_TIME - CLIENT_TIME))
ABS_DIFF=${DIFF#-}

if [ $ABS_DIFF -gt 60 ]; then
    echo "WARNING: Clock drift detected: ${DIFF}s difference"
    # Send alert to your monitoring system
fi
```

**Add to crontab:**
```bash
# Check every 5 minutes
*/5 * * * * /path/to/clock_monitor.sh
```

## 🔐 Security Considerations

### Why This Matters
- **Security Risk**: Large timestamp windows reduce HMAC security
- **Replay Attacks**: Old requests could be replayed within the window
- **Audit Trail**: Inaccurate timestamps affect log analysis

### Best Practices
1. **Keep timestamp window as small as possible** (300s ideal)
2. **Monitor clock drift regularly**
3. **Use reliable NTP sources**
4. **Set up alerts for clock sync failures**
5. **Document any temporary security relaxations**

## 📞 Support Information

### Log Analysis Commands
```bash
# Check for timestamp-related errors
docker-compose logs monitoring-backend | grep -i "timestamp\|clock"

# Monitor real-time timestamp issues
docker-compose logs -f monitoring-backend | grep -E "(stale|drift|clock)"

# Check Go client logs for clock warnings
docker-compose logs go-client | grep -i "clock\|drift"
```

### Common Error Patterns
- `Request timestamp is stale: time_diff=XXXXs` - Clock sync issue
- `Clock drift detected: XXs difference` - Minor sync issue (< 2min)
- `HMAC signature verification failed` - Could be related to timestamp

---

**Next Steps:**
1. ✅ Emergency fix applied (system functional)
2. 🔄 Fix clock synchronization on both systems
3. 📊 Monitor for 24-48 hours
4. 🔒 Gradually reduce timestamp window back to secure levels
5. 📈 Set up ongoing clock drift monitoring