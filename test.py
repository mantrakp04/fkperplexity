import os
import sys
from typing import Dict, Any
from browser_use import Agent, BrowserProfile
from browser_use.llm.anthropic.chat import ChatAnthropic
# from browser_use.llm.openai.chat import ChatOpenAI
from fastmcp import FastMCP

mcp = FastMCP()


# Configuration constants
DS160_URL = "ceac.state.gov/genniv/"
MODEL_NAME = "gpt-4o"

browser_profile = BrowserProfile(
    # Set viewport to ensure proper zoom scaling
    viewport={"width": 1280, "height": 1024},
    minimum_wait_page_load_time=0.5,
    maximum_wait_page_load_time=2.0,

    # Add custom Chrome args for 125% zoom and disable popups
    args=[
        "--force-device-scale-factor=1.50",
        "--high-dpi-support=1",
        "--device-scale-factor=1.25",
        "--disable-beforeunload-throttling",
        "--disable-popup-blocking",
        "--disable-prompt-on-repost"
    ]
)

@mcp.tool(name="", description="")
def main(form_name: str = "DS-160", form_data: str = """
Example Input:

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
""", form_url: str = "ceac.state.gov/genniv/"):
    try:
        # Create language model instance
        # llm = ChatOpenAI(
        #     model=MODEL_NAME,
        #     temperature=1.0,
        #     # reasoning_effort="medium"
        # )
        llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            temperature=0.2,
        )
        
        # Create automation instructions
        instructions = """Fill out the {form_name} US visa form at {form_url} using the provided example data. Prefer using the click tool. Never stop until you are done. If you hit captcha retry.
        Use the following example data :\n
        """ + form_data + form_url
        print("🤖 Creating automation agent...")
        
        # Create and run the automation agent
        agent = Agent(
            instructions,
            llm=llm,
            browser_profile=browser_profile,
            verbose=True,
        )

        # Execute the automation
        result = agent.run_sync(max_steps=1000)
        
        print("✅ Automation completed successfully!")
        print(f"📋 Result: {result}")
        
    except Exception as e:
        print(f"❌ Automation failed: {e}")
        print("Please check your configuration and try again.")
        sys.exit(1)
