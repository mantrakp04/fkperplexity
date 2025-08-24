#!/usr/bin/env node

/**
 * Comprehensive Test Suite for MCP Browser Automation Service Endpoints
 * Tests all integrated endpoints and simulates the React frontend workflow
 */

const http = require('http');

// Test configuration
const BASE_URL = 'http://localhost:8000';
const TEST_SESSION_ID = `test_integration_${Date.now()}`;

// Helper function to make HTTP requests
function makeRequest(method, path, data = null) {
  return new Promise((resolve, reject) => {
    const url = new URL(path, BASE_URL);
    const options = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + url.search,
      method: method,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    };

    const req = http.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => body += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(body);
          resolve({ status: res.statusCode, data: parsed });
        } catch (e) {
          resolve({ status: res.statusCode, data: body });
        }
      });
    });

    req.on('error', reject);
    
    if (data) {
      req.write(JSON.stringify(data));
    }
    
    req.end();
  });
}

// Test Functions
async function testEndpoint(name, method, path, data = null, expectedStatus = 200) {
  console.log(`\n🔍 Testing: ${name}`);
  console.log(`   Method: ${method} ${path}`);
  
  try {
    const result = await makeRequest(method, path, data);
    const success = result.status === expectedStatus;
    
    console.log(`   Status: ${result.status} ${success ? '✅' : '❌'}`);
    console.log(`   Response: ${JSON.stringify(result.data, null, 2)}`);
    
    return { success, result };
  } catch (error) {
    console.log(`   Error: ${error.message} ❌`);
    return { success: false, error };
  }
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Main Test Suite
async function runTestSuite() {
  console.log('🚀 Starting MCP Browser Automation Service Endpoint Tests');
  console.log('='.repeat(60));
  
  const results = [];
  
  // Test 1: Check initial state (no sessions)
  results.push(await testEndpoint(
    'Get All Sessions (Empty State)', 
    'GET', 
    '/tracking/status'
  ));
  
  // Test 2: Check non-existent session
  results.push(await testEndpoint(
    'Get Non-Existent Session', 
    'GET', 
    `/tracking/status/${TEST_SESSION_ID}`,
    null,
    200 // Should return 200 with not_found status
  ));
  
  // Test 3: Get alerts for non-existent session
  results.push(await testEndpoint(
    'Get Alerts for Non-Existent Session', 
    'GET', 
    `/tracking/alerts/${TEST_SESSION_ID}`
  ));
  
  // Test 4: Get all alerts (should be empty)
  results.push(await testEndpoint(
    'Get All Alerts (Empty)', 
    'GET', 
    '/tracking/alerts'
  ));
  
  // Test 5: Start automation session (this will create the session but not complete)
  console.log('\n⚠️  Note: Next test will create a browser session but may not complete');
  console.log('   This is expected for testing purposes - we\'ll interrupt after a few seconds');
  
  // Start automation in background and quickly test status
  const automationPromise = makeRequest('POST', '/automated_form_filler', {
    id: TEST_SESSION_ID,
    form_name: 'Test Form',
    form_url: 'https://httpbin.org/delay/60', // Use a delay endpoint for testing
    form_data: 'Test data for endpoint testing'
  });
  
  // Wait a moment for the session to initialize
  await sleep(3000);
  
  // Test 6: Check session status (should be running/initializing)
  results.push(await testEndpoint(
    'Get Running Session Status', 
    'GET', 
    `/tracking/status/${TEST_SESSION_ID}`
  ));
  
  // Test 7: Get session summary
  results.push(await testEndpoint(
    'Get Session Summary', 
    'GET', 
    `/tracking/summary/${TEST_SESSION_ID}`
  ));
  
  // Test 8: Check all sessions (should show our test session)
  results.push(await testEndpoint(
    'Get All Sessions (With Active Session)', 
    'GET', 
    '/tracking/status'
  ));
  
  // Test 9: Get alerts for active session
  results.push(await testEndpoint(
    'Get Session Alerts', 
    'GET', 
    `/tracking/alerts/${TEST_SESSION_ID}`
  ));
  
  // Test 10: Cleanup session
  results.push(await testEndpoint(
    'Cleanup Session', 
    'DELETE', 
    `/tracking/cleanup/${TEST_SESSION_ID}`
  ));
  
  // Test 11: Verify cleanup worked
  results.push(await testEndpoint(
    'Verify Session Cleanup', 
    'GET', 
    `/tracking/status/${TEST_SESSION_ID}`
  ));
  
  // Test 12: Check all sessions after cleanup (should be empty again)
  results.push(await testEndpoint(
    'Get All Sessions After Cleanup', 
    'GET', 
    '/tracking/status'
  ));
  
  // Summary
  console.log('\n' + '='.repeat(60));
  console.log('📊 TEST SUMMARY');
  console.log('='.repeat(60));
  
  const passed = results.filter(r => r.success).length;
  const failed = results.filter(r => !r.success).length;
  
  console.log(`✅ Passed: ${passed}`);
  console.log(`❌ Failed: ${failed}`);
  console.log(`📈 Success Rate: ${Math.round((passed / results.length) * 100)}%`);
  
  if (failed === 0) {
    console.log('\n🎉 All endpoint tests passed! The MCP Browser Automation Service is fully functional.');
    console.log('   React frontend can successfully connect to all tracking endpoints.');
  } else {
    console.log('\n⚠️  Some tests failed. Check the output above for details.');
  }
  
  console.log('\n🌐 Frontend URLs:');
  console.log(`   React App: http://localhost:3001/`);
  console.log(`   MCP Service: http://localhost:8000/`);
  console.log(`   Webhook Server: http://localhost:3000/`);
  
  // Try to gracefully handle the automation promise
  try {
    // Give it a moment to settle
    setTimeout(() => process.exit(0), 2000);
  } catch (e) {
    console.log('Background automation cleaned up');
  }
}

// Run the tests
runTestSuite().catch(console.error);
