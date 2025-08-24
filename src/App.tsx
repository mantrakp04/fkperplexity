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
  const [automationStatus, setAutomationStatus] = useState(null);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [sessionAlerts, setSessionAlerts] = useState([]);
  
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

  // Function to check automation status
  const checkAutomationStatus = async (sessionId) => {
    if (!sessionId) return;
    
    try {
      const response = await fetch(`http://localhost:8000/tracking/status/${sessionId}`);
      if (response.ok) {
        const statusData = await response.json();
        setAutomationStatus(statusData);
        return statusData;
      }
    } catch (error) {
      console.error('Error checking automation status:', error);
    }
    return null;
  };

  // Function to get session alerts
  const getSessionAlerts = async (sessionId) => {
    if (!sessionId) return;
    
    try {
      const response = await fetch(`http://localhost:8000/tracking/alerts/${sessionId}`);
      if (response.ok) {
        const alertsData = await response.json();
        setSessionAlerts(alertsData.alerts || []);
        return alertsData;
      }
    } catch (error) {
      console.error('Error fetching session alerts:', error);
    }
    return null;
  };

  // Function to get session summary
  const getSessionSummary = async (sessionId) => {
    if (!sessionId) return;
    
    try {
      const response = await fetch(`http://localhost:8000/tracking/summary/${sessionId}`);
      if (response.ok) {
        const summaryData = await response.json();
        return summaryData;
      }
    } catch (error) {
      console.error('Error fetching session summary:', error);
    }
    return null;
  };

  // Function to cleanup session data
  const cleanupSessionData = async (sessionId) => {
    if (!sessionId) return;
    
    try {
      const response = await fetch(`http://localhost:8000/tracking/cleanup/${sessionId}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        const cleanupData = await response.json();
        return cleanupData;
      }
    } catch (error) {
      console.error('Error cleaning up session data:', error);
    }
    return null;
  };

  // Polling function for automation status updates
  useEffect(() => {
    let statusInterval;
    
    if (currentSessionId && automationStatus && 
        ['running', 'initializing'].includes(automationStatus.status)) {
      statusInterval = setInterval(async () => {
        const updatedStatus = await checkAutomationStatus(currentSessionId);
        if (updatedStatus && ['completed', 'error'].includes(updatedStatus.status)) {
          // Stop polling when automation completes
          clearInterval(statusInterval);
          
          // Fetch alerts for the completed session
          await getSessionAlerts(currentSessionId);
        }
      }, 3000); // Poll every 3 seconds
    }
    
    return () => {
      if (statusInterval) {
        clearInterval(statusInterval);
      }
    };
  }, [currentSessionId, automationStatus]);
  
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
          const sessionId = `visa_interview_${Date.now()}`;
          setCurrentSessionId(sessionId);
          
          const mcpResponse = await fetch('http://localhost:8000/automated_form_filler', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              id: sessionId,
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
            setCallStatus(`✅ Interview completed! Form filling automation started...`);
            
            // Start checking status immediately
            setTimeout(() => checkAutomationStatus(sessionId), 1000);
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

      {/* Automation Status Display */}
      {automationStatus && (
        <div className="automation-status">
          <h3>🤖 Form Filling Progress</h3>
          <div className={`status-badge ${automationStatus.status}`}>
            {automationStatus.status?.toUpperCase()}
          </div>
          {automationStatus.message && (
            <p className="status-message">{automationStatus.message}</p>
          )}
          {automationStatus.current_step && (
            <p className="current-step">Step: {automationStatus.current_step}</p>
          )}
          {automationStatus.duration && (
            <p className="duration">Duration: {automationStatus.duration}</p>
          )}
          {automationStatus.status === 'error' && automationStatus.error && (
            <div className="error-details">
              <p className="error-message">❌ {automationStatus.error}</p>
            </div>
          )}
        </div>
      )}

      {/* Session Alerts Display */}
      {sessionAlerts.length > 0 && (
        <div className="alerts-section">
          <h3>⚠️ Form Filling Alerts ({sessionAlerts.length})</h3>
          <div className="alerts-list">
            {sessionAlerts.map((alert, index) => (
              <div key={index} className="alert-item">
                <div className="alert-header">
                  <strong>{alert.field_name}</strong>
                  <span className="alert-timestamp">{new Date(alert.timestamp).toLocaleTimeString()}</span>
                </div>
                <p className="alert-reason">{alert.reason}</p>
                <div className="alert-values">
                  <span className="expected">Expected: {alert.expected_value}</span>
                  <span className="actual">Used: {alert.actual_value}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Session Management */}
      {currentSessionId && (
        <div className="session-management">
          <h4>Session: {currentSessionId}</h4>
          <div className="session-buttons">
            <button 
              onClick={() => checkAutomationStatus(currentSessionId)}
              className="refresh-button"
              disabled={!currentSessionId}
            >
              🔄 Refresh Status
            </button>
            <button 
              onClick={() => getSessionAlerts(currentSessionId)}
              className="alerts-button"
              disabled={!currentSessionId}
            >
              ⚠️ Check Alerts
            </button>
            <button 
              onClick={async () => {
                const summary = await getSessionSummary(currentSessionId);
                if (summary) {
                  console.log('Session Summary:', summary);
                  alert(`Session Summary:\nStatus: ${summary.status?.status}\nAlerts: ${summary.alerts?.length || 0}\nDuration: ${summary.status?.duration || 'N/A'}`);
                }
              }}
              className="summary-button"
              disabled={!currentSessionId}
            >
              📋 View Summary
            </button>
            <button 
              onClick={async () => {
                if (confirm('This will permanently delete all session data. Continue?')) {
                  await cleanupSessionData(currentSessionId);
                  setCurrentSessionId(null);
                  setAutomationStatus(null);
                  setSessionAlerts([]);
                  setCallStatus('Session data cleaned up.');
                }
              }}
              className="cleanup-button danger"
              disabled={!currentSessionId}
            >
              🗑️ Cleanup Session
            </button>
          </div>
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
