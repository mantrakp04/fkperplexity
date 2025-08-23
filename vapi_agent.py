"""
Simple Vapi Agent Implementation
A basic voice AI assistant using Vapi's REST API
"""

import requests
import json
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class VapiAgent:
    """A simple Vapi agent class for creating and managing voice assistants."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.vapi.ai"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def create_assistant(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new voice assistant."""
        url = f"{self.base_url}/assistant"
        response = requests.post(url, headers=self.headers, json=config)
        response.raise_for_status()
        return response.json()
    
    def get_assistant(self, assistant_id: str) -> Dict[str, Any]:
        """Get an existing assistant."""
        url = f"{self.base_url}/assistant/{assistant_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def list_assistants(self) -> Dict[str, Any]:
        """List all assistants."""
        url = f"{self.base_url}/assistant"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def create_basic_assistant(self, name: str, voice: str = "azure", 
                             model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
        """Create a basic assistant with default configuration."""
        config = {
            "name": name,
            "voice": {
                "provider": "azure",
                "voiceId": "andrew"
            },
            "model": {
                "provider": "openai", 
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": f"You are {name}, a helpful voice assistant. Keep responses concise and conversational."
                    }
                ]
            },
            "firstMessage": f"Hello! I'm {name}, your voice assistant. How can I help you today?"
        }
        return self.create_assistant(config)


def main():
    """Example usage of the VapiAgent class."""
    # Get API key from environment or user input
    api_key = os.getenv("VAPI_API_KEY")
    if not api_key:
        print("Please set your VAPI_API_KEY environment variable")
        print("You can find your API key at https://dashboard.vapi.ai/")
        return
    
    # Create Vapi agent
    agent = VapiAgent(api_key)
    
    try:
        # List existing assistants
        print("Listing existing assistants...")
        assistants = agent.list_assistants()
        if isinstance(assistants, list):
            print(f"Found {len(assistants)} assistants")
        else:
            print(f"Found {len(assistants.get('data', []))} assistants")
        
        # Create a new basic assistant
        print("\nCreating a new voice assistant...")
        assistant = agent.create_basic_assistant(
            name="MyVoiceBot",
            voice="azure"
        )
        
        print(f"✅ Created assistant: {assistant['name']}")
        print(f"Assistant ID: {assistant['id']}")
        print(f"Phone Number: {assistant.get('phoneNumber', 'Not assigned')}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json()
                print(f"Error details: {json.dumps(error_details, indent=2)}")
            except:
                print(f"Response text: {e.response.text}")
        print("Make sure your API key is valid and you have internet connectivity")


if __name__ == "__main__":
    main()