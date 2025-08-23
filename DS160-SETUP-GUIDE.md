# DS-160 Voice Agent Setup Guide

This guide will help you set up a voice agent using Vapi that collects DS-160 visa application information conversationally and stores it in a Convex database.

## 🎯 What This System Does

- **Voice Collection**: Uses Vapi to conduct a natural conversation collecting all DS-160 required information
- **Smart Conversation Flow**: AI assistant guides users through 7 key sections of DS-160 data
- **Database Storage**: Automatically stores collected data in Convex with proper validation
- **Form Automation**: Data can be used with your existing browser automation to fill DS-160 forms

## 🛠️ Setup Instructions

### 1. Install Dependencies

```bash
# Install Node.js dependencies
bun install

# Or if using npm
npm install
```

### 2. Set Up Convex Database

```bash
# Install Convex CLI if not already installed
npm install -g convex

# Initialize and deploy Convex
convex login
convex init
convex dev

# This will give you a Convex URL like: https://your-project.convex.cloud
```

### 3. Set Up Vapi Account

1. Go to [Vapi.ai](https://vapi.ai) and create an account
2. Get your **Public Key** and **Private Key** from the dashboard
3. Note these down - you'll need them for configuration

### 4. Create Environment Configuration

Create a `.env` file in the project root:

```env
# Vapi Configuration
VAPI_PUBLIC_KEY=your_vapi_public_key_here
VAPI_PRIVATE_KEY=your_vapi_private_key_here

# Convex Configuration
CONVEX_URL=https://your-convex-deployment.convex.cloud

# Server Configuration
PORT=3000
NODE_ENV=development

# Webhook Security
WEBHOOK_SECRET=ds160_webhook_secret_2024

# Optional: External URL for webhook (when deployed)
# EXTERNAL_URL=https://your-domain.com
```

### 5. Deploy Convex Functions

```bash
# Deploy the schema and functions
convex deploy

# Or run in development mode
convex dev
```

### 6. Start the Webhook Server

```bash
# Start the webhook server
bun run webhook

# Or
npm run webhook
```

The server will start on `http://localhost:3000`

### 7. Configure Vapi Webhook

1. In your Vapi dashboard, go to your assistant settings
2. Set the webhook URL to: `http://localhost:3000/webhook/vapi`
3. For production, use your deployed URL: `https://your-domain.com/webhook/vapi`

### 8. Test the Voice Agent

1. Open `http://localhost:3000` in your browser
2. Enter your Vapi public key in the configuration section
3. Click "Start DS-160 Interview" to test the voice agent

## 📋 DS-160 Information Collected

The voice agent collects the following information:

### 1. Personal Information
- Full name (first, middle, last)
- Gender
- Marital status
- Date of birth
- City and country of birth
- Nationality

### 2. Passport Information
- Passport number
- Passport book number (if available)
- Issuing country
- Place of issue
- Issue and expiration dates

### 3. Travel Information
- Purpose of trip to the US
- Intended arrival date
- Length of stay
- US address where you'll stay
- Who is paying for your trip

### 4. US Contact Information
- Contact person in the US (name, address, phone, email)

### 5. Family Information
- Father's full name
- Mother's full name
- Spouse's name (if married)

### 6. Work Information
- Current occupation
- Employer name and address
- Monthly income

### 7. Security Questions
- Have you ever been arrested or convicted?
- Do you belong to a clan or tribe?
- Do you have specialized skills in weapons/explosives?
- Have you ever been involved in terrorist activities?

## 🔄 How It Works

1. **User starts call** → Convex creates collection record
2. **Assistant asks questions** → Data saved to specific sections via function calls  
3. **Validation happens** → System ensures all required fields are collected
4. **Call ends** → Final validation and completion status updated
5. **Form filling ready** → Collected data available for DS-160 automation

## 📊 API Endpoints

The system provides several API endpoints for monitoring and management:

- `GET /health` - Health check
- `GET /api/collections` - Get all collections
- `GET /api/collections/:callId` - Get specific collection
- `GET /api/collections/ready-for-fill` - Get collections ready for form filling
- `POST /api/collections/:callId/mark-for-fill` - Mark collection for form filling

## 🔗 Integration with Existing Automation

Your existing Python browser automation can now pull data from Convex instead of using hardcoded data:

```python
import requests

# Get collections ready for form filling
response = requests.get('http://localhost:3000/api/collections/ready-for-fill')
collections = response.json()

for collection in collections:
    # Extract data for DS-160 form filling
    personal_info = collection.get('personalInfo', {})
    passport_info = collection.get('passportInfo', {})
    # ... use this data in your browser automation
    
    # Mark as being processed
    requests.post(f'http://localhost:3000/api/collections/{collection["callId"]}/mark-for-fill')
```

## 🚀 Deployment

### For Production Deployment:

1. **Deploy Convex**:
   ```bash
   convex deploy --prod
   ```

2. **Deploy Webhook Server** (choose one):
   
   **Option A: Vercel**
   ```bash
   npm i -g vercel
   vercel --prod
   ```
   
   **Option B: Railway**
   ```bash
   npm i -g @railway/cli
   railway deploy
   ```
   
   **Option C: DigitalOcean, AWS, etc.**
   - Deploy the webhook server to your preferred platform
   - Ensure environment variables are set

3. **Update Vapi Webhook URL** to your production URL

## 🔒 Security Considerations

- Store API keys in environment variables, never in code
- Use HTTPS for production webhook URLs
- Consider implementing webhook signature verification
- Regularly rotate API keys
- Monitor for unusual usage patterns

## 🛠️ Troubleshooting

### Common Issues:

1. **"Convex URL not found"**
   - Make sure `CONVEX_URL` is set in your `.env` file
   - Run `convex dev` to get your deployment URL

2. **"Vapi call fails to start"**
   - Check that your Vapi public key is correct
   - Ensure webhook URL is accessible from the internet

3. **"Function calls not working"**
   - Verify webhook server is running
   - Check webhook URL in Vapi dashboard
   - Look at server logs for errors

4. **"Data not saving to Convex"**
   - Confirm Convex functions are deployed
   - Check webhook logs for function call errors
   - Verify database schema matches

### Debug Mode:

Enable detailed logging by setting:
```env
NODE_ENV=development
```

Check logs in:
- Webhook server console
- Convex dashboard logs
- Browser developer tools

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review server and Convex logs
3. Test with the provided HTML interface first
4. Ensure all environment variables are set correctly

The system is designed to be robust and will gracefully handle most error conditions while providing detailed logging for debugging.
