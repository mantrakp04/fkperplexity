import { ConvexHttpClient } from "convex/browser";

// Webhook handler for Vapi events
export class VapiWebhookHandler {
  private convex: ConvexHttpClient;

  constructor(convexUrl: string) {
    this.convex = new ConvexHttpClient(convexUrl);
  }

  // Handle incoming webhook from Vapi
  async handleWebhook(request: Request): Promise<Response> {
    try {
      const payload = await request.json();
      
      console.log('Received webhook:', payload);

      switch (payload.type) {
        case 'function-call':
          return this.handleFunctionCall(payload);
        
        case 'call-ended':
          return this.handleCallEnded(payload);
        
        case 'call-started':
          return this.handleCallStarted(payload);
        
        case 'speech-update':
          return this.handleSpeechUpdate(payload);
        
        default:
          console.log('Unhandled webhook type:', payload.type);
          return new Response('OK', { status: 200 });
      }
    } catch (error) {
      console.error('Webhook error:', error);
      return new Response('Internal Server Error', { status: 500 });
    }
  }

  // Handle function calls from the assistant
  private async handleFunctionCall(payload: any): Promise<Response> {
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
          await this.saveDataToConvex(call.id, functionCall.name, functionCall.parameters);
          break;
          
        case 'complete_collection':
          await this.completeDS160Collection(call.id, functionCall.parameters);
          break;
          
        default:
          console.log('Unknown function call:', functionCall.name);
      }

      return new Response(JSON.stringify({
        result: "Function executed successfully"
      }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (error) {
      console.error('Function call error:', error);
      return new Response(JSON.stringify({
        error: "Function execution failed"
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }

  // Handle call started event
  private async handleCallStarted(payload: any): Promise<Response> {
    const { call } = payload;
    
    try {
      // Initialize a new DS-160 collection record
      await this.convex.mutation("ds160:createCollection", {
        callId: call.id,
        status: "in_progress",
        startedAt: new Date().toISOString(),
        data: {}
      });

      console.log('DS-160 collection started for call:', call.id);
      return new Response('OK', { status: 200 });
    } catch (error) {
      console.error('Call started error:', error);
      return new Response('Internal Server Error', { status: 500 });
    }
  }

  // Handle call ended event
  private async handleCallEnded(payload: any): Promise<Response> {
    const { call, transcript } = payload;
    
    try {
      // Update the collection record with final status
      await this.convex.mutation("ds160:updateCollection", {
        callId: call.id,
        updates: {
          status: "completed",
          endedAt: new Date().toISOString(),
          transcript: transcript,
          duration: call.duration || 0
        }
      });

      console.log('DS-160 collection completed for call:', call.id);
      return new Response('OK', { status: 200 });
    } catch (error) {
      console.error('Call ended error:', error);
      return new Response('Internal Server Error', { status: 500 });
    }
  }

  // Handle speech updates (optional - for real-time monitoring)
  private async handleSpeechUpdate(payload: any): Promise<Response> {
    // Log speech updates if needed for debugging
    console.log('Speech update:', payload.transcript);
    return new Response('OK', { status: 200 });
  }

  // Save data section to Convex
  private async saveDataToConvex(callId: string, section: string, data: any) {
    try {
      await this.convex.mutation("ds160:updateCollectionData", {
        callId,
        section,
        data
      });
      
      console.log(`Saved ${section} for call ${callId}:`, data);
    } catch (error) {
      console.error(`Error saving ${section}:`, error);
      throw error;
    }
  }

  // Complete DS-160 collection and mark as ready for form filling
  private async completeDS160Collection(callId: string, parameters: any) {
    try {
      await this.convex.mutation("ds160:completeCollection", {
        callId,
        confirmed: parameters.confirmed,
        summary: parameters.summary,
        completedAt: new Date().toISOString()
      });

      console.log(`DS-160 collection completed for call ${callId}`);
    } catch (error) {
      console.error('Error completing DS-160 collection:', error);
      throw error;
    }
  }
}

// Express.js/Node.js webhook endpoint
export async function setupWebhookEndpoint() {
  const express = require('express');
  const app = express();
  
  app.use(express.json());
  
  const webhookHandler = new VapiWebhookHandler(
    process.env.CONVEX_URL || "https://your-convex-deployment.convex.cloud"
  );

  app.post('/webhook/vapi', async (req: any, res: any) => {
    const response = await webhookHandler.handleWebhook(req);
    res.status(response.status).send(await response.text());
  });

  const PORT = process.env.PORT || 3000;
  app.listen(PORT, () => {
    console.log(`Webhook server running on port ${PORT}`);
    console.log(`Webhook URL: http://localhost:${PORT}/webhook/vapi`);
  });
}

// For serverless deployment (Vercel, Netlify, etc.)
export default async function handler(req: Request): Promise<Response> {
  if (req.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 });
  }

  const webhookHandler = new VapiWebhookHandler(
    process.env.CONVEX_URL || "https://your-convex-deployment.convex.cloud"
  );

  return await webhookHandler.handleWebhook(req);
}
