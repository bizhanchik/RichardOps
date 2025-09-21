# 📧 Email Alert Setup Guide

This guide will help you set up email alerts for your monitoring system using Brevo (formerly Sendinblue).

## 🚀 Quick Setup

### Step 1: Create a Brevo Account

1. Go to [Brevo.com](https://www.brevo.com/) and sign up for a free account
2. Verify your email address
3. Complete the account setup process

### Step 2: Get Your API Key

1. Log into your Brevo dashboard
2. Go to **Settings** → **API Keys** (or visit: https://app.brevo.com/settings/keys/api)
3. Click **Generate a new API key**
4. Give it a name like "Monitoring System"
5. Copy the generated API key (keep it secure!)

### Step 3: Configure Environment Variables

1. Copy the `.env.example` file to `.env` in your backend directory:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and add your email configuration:
   ```bash
   # Email Alert Configuration
   BREVO_API_KEY=your-actual-brevo-api-key-here
   ALERT_EMAIL=your-email@example.com
   ALERT_SENDER_NAME=Monitoring Bot
   ALERT_SENDER_EMAIL=noreply@yourdomain.com
   ```

### Step 4: Test Your Setup

Run the email test script to verify everything works:

```bash
cd backend
python email_test.py
```

If successful, you should receive a test email!

## 📨 What Alerts Will You Receive?

Your monitoring system will automatically send email alerts for:

### 🔴 High Severity Alerts
- **CPU Spikes** - When CPU usage exceeds normal thresholds
- **Brute Force Attacks** - When multiple failed login attempts are detected
- **Shell Access in Containers** - When unauthorized shell access is detected
- **High Error Rates** - When container error rates exceed 20%

### 🟡 Medium Severity Alerts
- **Memory Usage Spikes** - When memory usage is abnormally high
- **High Docker Event Volume** - When unusual container activity is detected
- **Database Connection Issues** - When database connectivity problems occur

### 📊 Anomaly Detection Alerts
- **Metric Anomalies** - Statistical anomalies in system metrics
- **Performance Degradation** - When system performance drops significantly
- **Resource Exhaustion** - When system resources are running low

## 🛠️ Advanced Configuration

### Custom Sender Information

You can customize the sender name and email in your `.env` file:

```bash
ALERT_SENDER_NAME=Your Company Monitoring
ALERT_SENDER_EMAIL=alerts@yourcompany.com
```

**Note**: The sender email should be a domain you own or use Brevo's default.

### Multiple Recipients

Currently, the system supports one primary alert email. To send to multiple recipients, you can:

1. Use a distribution list/group email
2. Set up email forwarding rules
3. Modify the code to support multiple recipients (advanced)

## 🧪 Testing Your Setup

### Basic Email Test

```bash
cd backend
python email_test.py
```

### Comprehensive Alert Test

```bash
cd backend
python test_alert_system.py
```

This will test:
- Basic email functionality
- Security alert formatting
- Anomaly detection alerts
- High severity alert handling

## 🔧 Troubleshooting

### Common Issues

**"BREVO_API_KEY is not set"**
- Make sure your `.env` file exists in the backend directory
- Verify the API key is correctly set without quotes
- Restart your backend server after making changes

**"Failed to send email via Brevo API"**
- Check your API key is valid and active
- Verify your Brevo account is in good standing
- Check your internet connection

**"Email not received"**
- Check your spam/junk folder
- Verify the recipient email address is correct
- Check Brevo's sending limits (free accounts have daily limits)

### Checking Logs

Monitor the backend logs for email-related messages:

```bash
# In your backend directory
tail -f logs/app.log | grep -i email
```

### Brevo Account Limits

Free Brevo accounts include:
- 300 emails per day
- Brevo branding in emails
- Basic support

For production use, consider upgrading to a paid plan for:
- Higher sending limits
- No branding
- Priority support
- Advanced features

## 🔒 Security Best Practices

1. **Keep your API key secure** - Never commit it to version control
2. **Use environment variables** - Store sensitive data in `.env` files
3. **Rotate API keys regularly** - Generate new keys periodically
4. **Monitor usage** - Check Brevo dashboard for unusual activity
5. **Use HTTPS** - Ensure your monitoring endpoints use secure connections

## 📞 Support

If you need help:

1. Check the [Brevo Documentation](https://developers.brevo.com/)
2. Review the backend logs for error messages
3. Test with the provided test scripts
4. Verify your environment configuration

## 🎯 Next Steps

Once email alerts are working:

1. **Customize alert thresholds** - Adjust sensitivity in the monitoring rules
2. **Set up monitoring dashboards** - Use the web interface for real-time monitoring
3. **Configure additional integrations** - Add Slack, Discord, or other notification channels
4. **Set up log aggregation** - Centralize logs for better analysis
5. **Implement custom rules** - Add business-specific monitoring rules

---

**Happy Monitoring!** 🚀