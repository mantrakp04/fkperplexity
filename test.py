import os
import sys
from typing import Dict, Any
from browser_use import Agent, BrowserProfile
from browser_use.llm.anthropic.chat import ChatAnthropic
from browser_use.llm.openai.chat import ChatOpenAI

# Configuration constants
DS160_URL = "https://ceac.state.gov/genniv/"
MODEL_NAME = "gpt-4.1"

# Comprehensive example DS-160 data (fictional for demonstration purposes)
EXAMPLE_DS160_DATA = """
Example DS-160 Data (Fictional)

Personal Information:
- Full Name: Johnathan Michael Doe
- Gender: Male
- Marital Status: Single
- Date of Birth: 15-March-1990
- City of Birth: Springfield
- Country of Birth: Exampleland
- Nationality: Examplelandian

Passport Information:
- Passport Number: X1234567
- Passport Book Number: N/A
- Issuing Country: Exampleland
- Place of Issue: Springfield
- Date of Issue: 01-January-2020
- Expiration Date: 01-January-2030

Travel Information:
- Purpose of Trip: Tourism
- Intended Date of Arrival: 10-October-2025
- Intended Length of Stay: 2 weeks
- U.S. Address: 123 Example Street, New York, NY 10001
- Person/Entity Paying for Trip: Self

U.S. Contact Information:
- Contact Person: Jane Smith (Friend)
- Address: 456 Demo Avenue, Los Angeles, CA 90001
- Phone: +1-555-123-4567
- Email: jane.smith@example.com

Family Information:
- Father's Name: Robert Doe
- Mother's Name: Emily Doe
- Spouse's Name: N/A

Work/Education/Training:
- Primary Occupation: Software Engineer
- Employer: ExampleTech Solutions
- Employer Address: 789 Innovation Blvd, Springfield, Exampleland
- Monthly Income: 5,000 Exampleland Dollars

Security & Background (Example Answers):
- Do you belong to a clan or tribe? No
- Have you ever been arrested? No
- Do you have specialized skills in weapons/explosives? No
- Have you ever been involved in terrorist activities? No
"""

def main():
    """
    Main execution function for the DS-160 automation script.
    """
    print("🚀 Starting DS-160 US Visa Form Automation")
    print("=" * 50)
    
    try:
        # Create browser profile with 125% zoom configuration
        browser_profile = BrowserProfile(
            # Set viewport to ensure proper zoom scaling
            viewport={"width": 1280, "height": 1024},
            # Add custom Chrome args for 125% zoom and disable popups
            args=[
                "--force-device-scale-factor=1.50",  # 150% zoom
                "--high-dpi-support=1",
                "--device-scale-factor=1.25",
                "--disable-beforeunload-throttling",  # Disable beforeunload popups
                "--disable-popup-blocking",  # Disable popup blocking
                "--disable-prompt-on-repost"  # Disable repost prompts
            ]
        )
        
        # Create language model instance
        llm = ChatOpenAI(
            model=MODEL_NAME,
            temperature=1.0,
            # reasoning_effort="medium"
        )
        # llm = ChatAnthropic(
        #     model="claude-3-5-sonnet-20241022",
        #     temperature=0.2,
        # )
        
        # Create automation instructions
        instructions = """Fill out the DS-160 US visa form at {DS160_URL} using the provided example data. Prefer using the click tool. Use multi tool calling to quickly fill out the form. If the screen is too small, use the console tool to zoom in.
        Use the following example data:\n
        """ + EXAMPLE_DS160_DATA
        print("🤖 Creating automation agent...")
        
        # Create and run the automation agent
        agent = Agent(
            instructions,
            llm=llm,
            browser_profile=browser_profile,
            verbose=True,
        )

        # Execute the automation
        result = agent.run_sync()
        
        print("✅ Automation completed successfully!")
        print(f"📋 Result: {result}")
        
    except Exception as e:
        print(f"❌ Automation failed: {e}")
        print("Please check your configuration and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()