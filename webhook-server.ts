import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import { config } from 'dotenv';
import { ConvexHttpClient } from 'convex/browser';

// Load environment variables
config();

const app = express();
const PORT = process.env.PORT || 3000;

// Use minimal helmet configuration to avoid HTTPS upgrade issues
app.use(helmet({
  contentSecurityPolicy: false, // Disable CSP entirely for localhost development
  hsts: false,
}));
app.use(cors({
  origin: [
    'http://localhost:3000', 'http://127.0.0.1:3000', 
    'http://localhost:3001', 'http://127.0.0.1:3001',
    'http://localhost:8080', 'http://127.0.0.1:8080',  // Add port 8080 for HTML server
    'http://localhost:8000', 'http://127.0.0.1:8000'   // Add port 8000 as backup
  ],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'Accept', 'Cache-Control'],
}));
app.use(express.json({ limit: '10mb' }));
app.use(express.static('.', { index: 'index.html' }));

// Initialize Convex client
const convex = new ConvexHttpClient(process.env.CONVEX_URL || "");

// Webhook handler for Vapi events
app.post('/webhook/vapi', async (req, res) => {
  try {
    console.log('Received webhook:', req.body);
    const payload = req.body;

    switch (payload.type) {
      case 'function-call':
        await handleFunctionCall(payload);
        res.json({ result: "Function executed successfully" });
        break;
      
      case 'call-ended':
        await handleCallEnded(payload);
        res.json({ result: "Call ended processed" });
        break;
      
      case 'call-started':
        await handleCallStarted(payload);
        res.json({ result: "Call started processed" });
        break;
      
      case 'speech-update':
        // Optional: handle real-time speech updates
        console.log('Speech update:', payload.transcript);
        res.json({ result: "Speech update processed" });
        break;
      
      default:
        console.log('Unhandled webhook type:', payload.type);
        res.json({ result: "OK" });
    }
  } catch (error) {
    console.error('Webhook error:', error);
    res.status(500).json({ error: "Internal Server Error" });
  }
});

// Handle function calls from the assistant
async function handleFunctionCall(payload: any) {
  const { functionCall, call } = payload;
  
  try {
    switch (functionCall.name) {
      case 'save_personal_info':
      case 'save_passport_info':
      case 'save_travel_info':
      case 'save_contact_info':
      case 'save_family_info':
      case 'save_work_info':
      case 'save_security_info':
        await convex.mutation("ds160:updateCollectionData", {
          callId: call.id,
          section: functionCall.name,
          data: functionCall.parameters
        });
        break;
        
      case 'complete_collection':
        await convex.mutation("ds160:completeCollection", {
          callId: call.id,
          confirmed: functionCall.parameters.confirmed,
          summary: functionCall.parameters.summary,
          completedAt: new Date().toISOString()
        });
        break;
        
      default:
        console.log('Unknown function call:', functionCall.name);
    }
  } catch (error) {
    console.error('Function call error:', error);
    throw error;
  }
}

// Handle call started event
async function handleCallStarted(payload: any) {
  const { call } = payload;
  
  try {
    await convex.mutation("ds160:createCollection", {
      callId: call.id,
      status: "in_progress",
      startedAt: new Date().toISOString(),
    });

    console.log('DS-160 collection started for call:', call.id);
  } catch (error) {
    console.error('Call started error:', error);
    throw error;
  }
}

// Handle call ended event
async function handleCallEnded(payload: any) {
  const { call, transcript } = payload;
  
  try {
    await convex.mutation("ds160:updateCollection", {
      callId: call.id,
      updates: {
        status: "completed",
        endedAt: new Date().toISOString(),
        transcript: transcript,
        duration: call.duration || 0
      }
    });

    console.log('DS-160 collection completed for call:', call.id);
  } catch (error) {
    console.error('Call ended error:', error);
    throw error;
  }
}

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: 'OK', 
    timestamp: new Date().toISOString(),
    service: 'DS-160 Vapi Webhook Server'
  });
});

// Get Vapi public key endpoint
app.get('/api/config', (req, res) => {
  res.json({
    vapiPublicKey: process.env.VAPI_PUBLIC_KEY || '',
    webhookUrl: `http://localhost:${PORT}/webhook/vapi`
  });
});

// Create Vapi assistant endpoint (server-side proxy)
app.post('/api/vapi/assistant', async (req, res) => {
  try {
    const response = await fetch('https://api.vapi.ai/assistant', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.VAPI_PRIVATE_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(req.body)
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Vapi assistant creation failed:', response.status, errorText);
      return res.status(response.status).json({ error: 'Failed to create assistant', details: errorText });
    }

    const assistant = await response.json();
    console.log('Assistant created successfully:', assistant.id);
    res.json(assistant);
  } catch (error) {
    console.error('Error creating assistant:', error);
    res.status(500).json({ error: 'Internal server error', message: error.message });
  }
});

// Start Vapi call endpoint (server-side proxy)
app.post('/api/vapi/call', async (req, res) => {
  try {
    const response = await fetch('https://api.vapi.ai/call', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.VAPI_PRIVATE_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(req.body)
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Vapi call creation failed:', response.status, errorText);
      return res.status(response.status).json({ error: 'Failed to start call', details: errorText });
    }

    const call = await response.json();
    console.log('Call started successfully:', call.id);
    res.json(call);
  } catch (error) {
    console.error('Error starting call:', error);
    res.status(500).json({ error: 'Internal server error', message: error.message });
  }
});

// End Vapi call endpoint (server-side proxy)
app.patch('/api/vapi/call/:callId', async (req, res) => {
  try {
    const { callId } = req.params;
    const response = await fetch(`https://api.vapi.ai/call/${callId}`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${process.env.VAPI_PRIVATE_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(req.body)
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.warn('Vapi call end failed:', response.status, errorText);
      return res.status(response.status).json({ error: 'Failed to end call', details: errorText });
    }

    const result = await response.json();
    console.log('Call ended successfully:', callId);
    res.json(result);
  } catch (error) {
    console.error('Error ending call:', error);
    res.status(500).json({ error: 'Internal server error', message: error.message });
  }
});

// Get Vapi call status endpoint (server-side proxy)
app.get('/api/vapi/call/:callId', async (req, res) => {
  try {
    const { callId } = req.params;
    const response = await fetch(`https://api.vapi.ai/call/${callId}`, {
      headers: {
        'Authorization': `Bearer ${process.env.VAPI_PRIVATE_KEY}`,
      }
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.warn('Vapi call status failed:', response.status, errorText);
      return res.status(response.status).json({ error: 'Failed to get call status', details: errorText });
    }

    const call = await response.json();
    res.json(call);
  } catch (error) {
    console.error('Error getting call status:', error);
    res.status(500).json({ error: 'Internal server error', message: error.message });
  }
});

// Get collections endpoint (for monitoring)
app.get('/api/collections', async (req, res) => {
  try {
    const collections = await convex.query("ds160:getAllCollections", {
      limit: 50
    });
    res.json(collections);
  } catch (error) {
    console.error('Error fetching collections:', error);
    res.status(500).json({ error: "Failed to fetch collections" });
  }
});

// Get collection by call ID
app.get('/api/collections/:callId', async (req, res) => {
  try {
    const collection = await convex.query("ds160:getCollectionByCallId", {
      callId: req.params.callId
    });
    
    if (!collection) {
      res.status(404).json({ error: "Collection not found" });
      return;
    }
    
    res.json(collection);
  } catch (error) {
    console.error('Error fetching collection:', error);
    res.status(500).json({ error: "Failed to fetch collection" });
  }
});

// Get collections ready for form filling
app.get('/api/collections/ready-for-fill', async (req, res) => {
  try {
    const collections = await convex.query("ds160:getReadyForFormFill");
    res.json(collections);
  } catch (error) {
    console.error('Error fetching ready collections:', error);
    res.status(500).json({ error: "Failed to fetch ready collections" });
  }
});

// Mark collection for form filling
app.post('/api/collections/:callId/mark-for-fill', async (req, res) => {
  try {
    await convex.mutation("ds160:markForFormFill", {
      callId: req.params.callId
    });
    res.json({ result: "Collection marked for form filling" });
  } catch (error) {
    console.error('Error marking collection for fill:', error);
    res.status(500).json({ error: "Failed to mark collection for fill" });
  }
});

// Error handling middleware
app.use((error: any, req: any, res: any, next: any) => {
  console.error('Server error:', error);
  res.status(500).json({ error: 'Internal Server Error' });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 DS-160 Vapi Webhook Server running on port ${PORT}`);
  console.log(`📡 Webhook URL: http://localhost:${PORT}/webhook/vapi`);
  console.log(`🏥 Health check: http://localhost:${PORT}/health`);
  console.log(`📊 Collections API: http://localhost:${PORT}/api/collections`);
  console.log(`🌐 Web interface: http://localhost:${PORT}/`);
});

export default app;
