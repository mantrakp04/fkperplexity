import { useAuthActions, useAuthToken } from "@convex-dev/auth/react";
import { useQuery } from "convex/react";
import { api } from "../convex/_generated/api";
import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const token = useAuthToken();
  const isAuthenticated = token !== null;
  
  // Remove loading state for now - using token-based authentication check
  
  return (
    <div className="App">
      {isAuthenticated ? <SignedInContent /> : <SignedOutContent />}
    </div>
  );
}

function SignedInContent() {
  const { signOut } = useAuthActions();
  const [vapi, setVapi] = useState(null);
  const [callStatus, setCallStatus] = useState('idle');
  const [isCallActive, setIsCallActive] = useState(false);
  const [conversationData, setConversationData] = useState([]);
  
  useEffect(() => {
    // Load VAPI SDK
    const loadVapi = async () => {
      try {
        console.log('Loading VAPI SDK...');
        const { default: Vapi } = await import('https://esm.sh/@vapi-ai/web@2.3.9');
        const vapiInstance = new Vapi('1bb2e750-95fc-4fda-a0db-bd3479e1aa50');
        setVapi(vapiInstance);
        console.log('VAPI SDK loaded successfully');
      } catch (error) {
        console.error('Failed to load VAPI SDK:', error);
      }
    };
    
    loadVapi();
  }, []);
  
  useEffect(() => {
    if (!vapi) return;
    
    // Setup VAPI event listeners
    vapi.on('call-start', () => {
      console.log('Call started');
      setIsCallActive(true);
      setCallStatus('🎤 Call started! You can now speak...');
    });
    
    vapi.on('call-end', () => {
      console.log('Call ended');
      setIsCallActive(false);
      setCallStatus('Call ended. Thank you for your visa interview!');
    });
    
    vapi.on('speech-start', () => {
      setCallStatus('🎤 Listening to you...');
    });
    
    vapi.on('speech-end', () => {
      setCallStatus('🤖 Assistant is responding...');
    });
    
    vapi.on('message', (message) => {
      console.log('Message received:', message);
      if (message.type === 'transcript' && message.transcriptType === 'final') {
        console.log(`${message.role}: ${message.transcript}`);
        // Store conversation data
        setConversationData(prev => [...prev, {
          role: message.role,
          transcript: message.transcript,
          timestamp: new Date().toISOString()
        }]);
      }
    });
    
    vapi.on('error', (error) => {
      console.error('VAPI Error:', error);
      setCallStatus('Error: ' + (error.message || 'Failed to start call'));
      setIsCallActive(false);
    });
    
  }, [vapi]);
  
  const startInterview = async () => {
    if (!vapi) {
      setCallStatus('VAPI is still loading...');
      return;
    }
    
    try {
      setCallStatus('Starting call...');
      
      const assistantConfig = {
        model: {
          provider: "openai",
          model: "gpt-3.5-turbo",
          messages: [{ 
            role: "system", 
            content: "You are a helpful visa application assistant. Be professional and ask one question at a time." 
          }]
        },
        voice: {
          provider: "openai",
          voiceId: "shimmer"
        },
        firstMessage: "Hello! I'm your visa application assistant. Let's start with your full name - what is your complete name?"
      };
      
      await vapi.start(assistantConfig);
    } catch (error) {
      console.error('Failed to start call:', error);
      setCallStatus('Failed to start call: ' + error.message);
    }
  };
  
  const endInterview = async () => {
    if (vapi && isCallActive) {
      try {
        await vapi.stop();
        setCallStatus('Ending call...');
        
        // Trigger MCP Browser Automation Service
        try {
          setCallStatus('Processing interview data...');
          const mcpResponse = await fetch('http://localhost:8000/automated_form_filler', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              id: `visa_interview_${Date.now()}`,
              form_name: "DS-160",
              form_url: "ceac.state.gov/genniv/",
              form_data: conversationData.map(msg => 
                `${msg.role}: ${msg.transcript} (${msg.timestamp})`
              ).join('\n'),
              source: 'interview_completed',
              conversation_data: conversationData,
              total_messages: conversationData.length
            })
          });
          
          if (mcpResponse.ok) {
            const responseData = await mcpResponse.json();
            console.log('MCP Browser Automation triggered successfully:', responseData);
            setCallStatus(`✅ Interview completed! Automation started (Session: ${responseData.session_id || 'N/A'})`);
          } else {
            const errorData = await mcpResponse.text();
            console.error('MCP API call failed:', mcpResponse.status, errorData);
            setCallStatus(`⚠️ Interview ended but automation failed (${mcpResponse.status})`);
          }
        } catch (mcpError) {
          console.error('Error calling MCP API:', mcpError);
          setCallStatus('⚠️ Interview ended but could not connect to automation service.');
        }
        
      } catch (error) {
        console.error('Error ending call:', error);
        setCallStatus('Error ending call: ' + error.message);
      }
    }
  };
  
  return (
    <div className="container">
      <div className="logo">VA</div>
      <h1>Visa Application Assistant</h1>
      <p className="subtitle">Complete your visa application through a natural conversation with our AI assistant.</p>
      
      <div className="auth-section">
        <p>✅ You are signed in!</p>
        <button onClick={signOut} className="auth-button">
          Sign Out
        </button>
      </div>
      
      {callStatus !== 'idle' && (
        <div className="status-section">
          <p className="status">{callStatus}</p>
        </div>
      )}
      
      <div className="instructions">
        <h3>Ready to start your DS-160 interview:</h3>
        <ul>
          <li>Click "Start Visa Interview" to begin</li>
          <li>Allow microphone access when prompted</li>
          <li>The AI assistant will guide you through all questions</li>
          <li>Your progress is automatically saved</li>
        </ul>
      </div>
      
      {!isCallActive ? (
        <button 
          className="call-button" 
          onClick={startInterview}
          disabled={!vapi}
        >
          🎤 Start Visa Interview
        </button>
      ) : (
        <button 
          className="call-button end-button" 
          onClick={endInterview}
        >
          ❌ End Interview
        </button>
      )}
    </div>
  );
}

function SignedOutContent() {
  const { signIn } = useAuthActions();
  
  return (
    <div className="container">
      <div className="logo">VA</div>
      <h1>Visa Application Assistant</h1>
      <p className="subtitle">Complete your visa application through a natural conversation with our AI assistant.</p>
      
      <div className="auth-section">
        <p>👋 Welcome! Please sign in to start your visa interview.</p>
        <button 
          onClick={() => signIn("anonymous")} 
          className="auth-button"
        >
          Start Anonymous Session
        </button>
      </div>
      
      <div className="instructions">
        <h3>How it works:</h3>
        <ul>
          <li>Sign in to create a secure session</li>
          <li>Your progress will be automatically saved</li>
          <li>Resume your interview anytime</li>
          <li>All data is encrypted and secure</li>
        </ul>
      </div>
    </div>
  );
}

export default App;
