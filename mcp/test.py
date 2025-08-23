import sys
import asyncio
from browser_use import Agent, BrowserSession
from browser_use.llm.anthropic.chat import ChatAnthropic
# from browser_use.llm.openai.chat import ChatOpenAI
from fastmcp import FastMCP

mcp = FastMCP()

def get_or_create_browser_session(session_id: str) -> BrowserSession:
    """Get or create a persistent browser session based on ID"""
    return BrowserSession(
        keep_alive=True,
        user_data_dir=f'~/.config/browseruse/profiles/{session_id}',
        viewport={"width": 1280, "height": 1024},
        minimum_wait_page_load_time=0.5,
        maximum_wait_page_load_time=2.0,
        device_scale_factor=1.5
    )

@mcp.tool(name="automated_form_filler", description="Automatically fill out web forms using browser automation with provided form data and instructions")
def main(id: str, form_name: str = "DS-160", form_data: str = """
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
        instructions = f"""Fill out the {form_name} form at {form_url} using the provided data.
        
        INSTRUCTIONS:
        - Navigate to the specified URL: {form_url}
        - Fill out all form fields accurately using the provided data
        - Handle any pop-ups, confirmations, or navigation steps
        - Use click tool for buttons and form interactions
        - If you encounter captcha, retry the operation
        - Continue until the form is completely filled and submitted
        - Never stop until the task is fully completed
        
        FORM DATA TO USE:
        {form_data}"""
        
        print(f"🤖 Creating automation agent for session: {id}")
        
        # Get or create browser session
        browser_session = get_or_create_browser_session(id)
        
        async def run_automation():
            try:
                # Start the session
                await browser_session.start()
                
                # Create and run the automation agent
                agent = Agent(
                    task=instructions,
                    llm=llm,
                    browser_session=browser_session,
                    verbose=True,
                )

                # Execute the automation
                result = await agent.run(max_steps=1000)
                return result
                
            finally:
                # Close session when done
                await browser_session.close()
        
        # Execute the automation
        result = asyncio.run(run_automation())
        
    except Exception as e:
        sys.exit(1)
