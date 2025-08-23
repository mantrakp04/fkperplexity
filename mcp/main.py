import sys
import time
from typing import Dict
from browser_use import Agent, BrowserSession
from browser_use.llm.anthropic.chat import ChatAnthropic
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class AutomationStatus(BaseModel):
    session_id: str
    status: str
    form_name: str
    form_url: str
    start_time: float
    current_step: str
    progress: int = Field(ge=0, le=100)
    message: str
    end_time: float = None
    result: str = None
    error: str = None

mcp = FastMCP(
    name="Browser Automation Service", 
    instructions="Automated web form filling service with real-time status tracking."
)

automation_status: Dict[str, AutomationStatus] = {}

@mcp.custom_route(path="/tracking/status/{session_id}", method="GET")
def get_automation_status(session_id: str):
    """Get the current status of an automation session"""
    if session_id not in automation_status:
        return {
            "session_id": session_id,
            "status": "not_found",
            "message": "No automation found for this session ID"
        }
    
    return automation_status[session_id]

@mcp.custom_route(path="/tracking/status", method="GET")
def get_all_automation_status():
    """Get the status of all automation sessions"""
    return {
        "sessions": automation_status,
        "total_sessions": len(automation_status)
    }

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

@mcp.custom_route(path="/automated_form_filler", method="POST")
@mcp.tool(name="automated_form_filler", description="Automatically fill out web forms using browser automation with provided form data and instructions")
async def main(id: str, form_name: str = "DS-160", form_url: str = "ceac.state.gov/genniv/", form_data: str = """
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
"""):
    # Initialize status tracking
    automation_status[id] = AutomationStatus(
        session_id=id,
        status="starting",
        form_name=form_name,
        form_url=form_url,
        start_time=time.time(),
        current_step="initializing", 
        progress=0,
        message="Automation starting...",
    )
    
    try:
        # Update status to model initialization
        automation_status[id].update({
            "status": "initializing",
            "current_step": "creating_llm_model",
            "progress": 10,
            "message": "Initializing language model..."
        })
        
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
        
        # Update status to browser session creation
        automation_status[id].update({
            "status": "initializing",
            "current_step": "creating_browser_session",
            "progress": 20,
            "message": "Creating browser session..."
        })
        
        # Get or create browser session
        browser_session = get_or_create_browser_session(id)
        
        async def run_automation():
            try:
                # Update status to starting browser
                automation_status[id].update({
                    "status": "running",
                    "current_step": "starting_browser",
                    "progress": 30,
                    "message": "Starting browser session..."
                })
                
                # Start the session
                await browser_session.start()
                
                # Update status to running automation
                automation_status[id].update({
                    "status": "running",
                    "current_step": "form_automation",
                    "progress": 50,
                    "message": f"Running form automation for {form_name}..."
                })
                
                # Create and run the automation agent
                agent = Agent(
                    task=instructions,
                    llm=llm,
                    browser_session=browser_session,
                    max_retires=5,
                    retry_delay=10
                )

                # Execute the automation
                result = await agent.run(max_steps=1000)
                
                # Update status to completed
                automation_status[id].update({
                    "status": "completed",
                    "current_step": "finished",
                    "progress": 100,
                    "message": "Automation completed successfully",
                    "end_time": time.time(),
                    "result": str(result) if result else "No result returned"
                })
                
                return result
                
            except Exception as e:
                # Update status to error
                automation_status[id].update({
                    "status": "error",
                    "current_step": "error_occurred",
                    "progress": automation_status[id].get("progress", 0),
                    "message": f"Error during automation: {str(e)}",
                    "end_time": time.time(),
                    "error": str(e)
                })
                raise
            finally:
                # Close session when done
                await browser_session.close()
        
        # Execute the automation
        result = await run_automation()
        if result.is_done() and not result.is_successful():
            automation_status[id].update({
                "status": "error",
                "current_step": "fatal_error",
                "message": f"Fatal error: {str(result.error)}",
                "end_time": time.time(),
                "error": str(result.error)
            })
        
    except Exception as e:
        # Update status to error if not already updated
        if id in automation_status and automation_status[id].get("status") != "error":
            automation_status[id].update({
                "status": "error",
                "current_step": "fatal_error",
                "message": f"Fatal error: {str(e)}",
                "end_time": time.time(),
                "error": str(e)
            })
        sys.exit(1)

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8000)