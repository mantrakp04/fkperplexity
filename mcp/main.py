import time
from typing import Dict, List
from browser_use import Agent, BrowserSession
from browser_use.llm.anthropic.chat import ChatAnthropic
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from starlette.requests import Request
from starlette.responses import JSONResponse

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

class FormAlert(BaseModel):
    session_id: str
    field_name: str
    expected_value: str
    actual_value: str
    reason: str
    timestamp: float = Field(default_factory=time.time)

mcp = FastMCP(
    name="Browser Automation Service", 
    instructions="Automated web form filling service with real-time status tracking."
)

automation_status: Dict[str, AutomationStatus] = {}
form_alerts: List[FormAlert] = []

@mcp.custom_route("/tracking/status/{session_id}", methods=["GET"])
async def get_automation_status(request: Request) -> JSONResponse:
    """Get the current status of an automation session"""
    session_id = request.path_params["session_id"]
    if session_id not in automation_status:
        return JSONResponse({
            "session_id": session_id,
            "status": "not_found",
            "message": "No automation found for this session ID"
        })
    
    return JSONResponse(automation_status[session_id].dict())

@mcp.custom_route("/tracking/status", methods=["GET"])
async def get_all_automation_status(request: Request) -> JSONResponse:
    """Get the status of all automation sessions"""
    return JSONResponse({
        "sessions": {k: v.dict() for k, v in automation_status.items()},
        "total_sessions": len(automation_status)
    })

def alert_uncertain_data(field_name: str, expected_value: str, actual_value: str, reason: str, session_id: str = "default_session") -> str:
    """
    Alert when form data is uncertain or placeholder values are used.
    Use this tool when you encounter missing, unclear, or questionable data while filling forms.
    This helps flag fields that may need manual review or correction.
    
    Args:
        field_name: The name or identifier of the form field
        expected_value: What value should ideally be entered
        actual_value: What value was actually entered (e.g., "N/A", "Unknown", placeholder data)
        reason: Explanation of why this data is uncertain (e.g., "missing from provided data", "using placeholder")
        session_id: The automation session ID (defaults to "default_session")
    
    Returns:
        Confirmation message about the alert being logged
    """
    alert = FormAlert(
        session_id=session_id,
        field_name=field_name,
        expected_value=expected_value,
        actual_value=actual_value,
        reason=reason
    )
    
    form_alerts.append(alert)
    
    return f"Alert logged: Field '{field_name}' flagged for review. Used '{actual_value}' but expected '{expected_value}'. Reason: {reason}"

@mcp.custom_route("/tracking/alerts", methods=["GET"])
async def get_form_alerts(request: Request) -> JSONResponse:
    """Get all form alerts across all sessions"""
    return JSONResponse({
        "alerts": [alert.dict() for alert in form_alerts],
        "total_alerts": len(form_alerts)
    })

@mcp.custom_route("/tracking/alerts/{session_id}", methods=["GET"])
async def get_session_alerts(request: Request) -> JSONResponse:
    """Get form alerts for a specific session"""
    session_id = request.path_params["session_id"]
    session_alerts = [alert for alert in form_alerts if alert.session_id == session_id]
    
    return JSONResponse({
        "session_id": session_id,
        "alerts": [alert.dict() for alert in session_alerts],
        "total_alerts": len(session_alerts)
    })

def get_or_create_browser_session(session_id: str) -> BrowserSession:
    """Get or create a persistent browser session based on ID"""
    from browser_use.browser.profile import BrowserProfile
    
    profile = BrowserProfile(
        keep_alive=True,
        user_data_dir=f'~/.config/browseruse/profiles/{session_id}',
        viewport={"width": 1280, "height": 1024},
        minimum_wait_page_load_time=0.5,
        maximum_wait_page_load_time=2.0,
        device_scale_factor=1.5,
        args=[
            "--force-device-scale-factor=1.5",
        ]
    )
    
    return BrowserSession(
        id=session_id,
        browser_profile=profile
    )

@mcp.custom_route("/automated_form_filler", methods=["POST"])
async def main(request: Request) -> JSONResponse:
    # Extract parameters from request body
    try:
        body = await request.json()
    except Exception:
        body = {}
    
    id = body.get("id", "default_session")
    form_name = body.get("form_name", "DS-160")
    form_url = body.get("form_url", "ceac.state.gov/genniv/")
    form_data = body.get("form_data", """Example Input:

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
- Have you ever used other names (i.e., maiden, religious, professional, alias, etc.)? No
- Do you have a telecode that represents your name? No
""")
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
        automation_status[id].status = "initializing"
        automation_status[id].current_step = "creating_llm_model"
        automation_status[id].progress = 10
        automation_status[id].message = "Initializing language model..."
        
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
        - When data is missing, unclear, or you need to use placeholder values, use the alert_uncertain_data tool to flag the field for manual review
        - Only use placeholder data when absolutely necessary to pass form validation

        FORM DATA TO USE:
        {form_data} {form_url}"""
        
        # Update status to browser session creation
        automation_status[id].status = "initializing"
        automation_status[id].current_step = "creating_browser_session"
        automation_status[id].progress = 20
        automation_status[id].message = "Creating browser session..."
        
        # Get or create browser session
        browser_session = get_or_create_browser_session(id)
        
        async def run_automation():
            try:
                # Update status to starting browser
                automation_status[id].status = "running"
                automation_status[id].current_step = "starting_browser"
                automation_status[id].progress = 30
                automation_status[id].message = "Starting browser session..."
                
                # Start the session
                await browser_session.start()
                
                # Update status to running automation
                automation_status[id].status = "running"
                automation_status[id].current_step = "form_automation"
                automation_status[id].progress = 50
                automation_status[id].message = f"Running form automation for {form_name}..."
                
                # Create and run the automation agent
                agent = Agent(
                    task=instructions,
                    llm=llm,
                    browser_session=browser_session,
                    max_retires=5,
                    retry_delay=10,
                    additional_tools=[alert_uncertain_data]
                )

                # Execute the automation
                result = await agent.run(max_steps=1000)
                
                # Update status to completed
                automation_status[id].status = "completed"
                automation_status[id].current_step = "finished"
                automation_status[id].progress = 100
                automation_status[id].message = "Automation completed successfully"
                automation_status[id].end_time = time.time()
                automation_status[id].result = str(result) if result else "No result returned"
                
                return result
                
            except Exception as e:
                # Update status to error
                automation_status[id].status = "error"
                automation_status[id].current_step = "error_occurred"
                automation_status[id].message = f"Error during automation: {str(e)}"
                automation_status[id].end_time = time.time()
                automation_status[id].error = str(e)
                raise
            finally:
                # Stop session when done
                await browser_session.stop()
        
        # Execute the automation
        result = await run_automation()
        if result.is_done() and not result.is_successful():
            automation_status[id].status = "error"
            automation_status[id].current_step = "fatal_error"
            automation_status[id].message = f"Fatal error: {str(result.error)}"
            automation_status[id].end_time = time.time()
            automation_status[id].error = str(result.error)
        
    except Exception as e:
        # Update status to error if not already updated
        if id in automation_status and automation_status[id].status != "error":
            automation_status[id].status = "error"
            automation_status[id].current_step = "fatal_error"
            automation_status[id].message = f"Fatal error: {str(e)}"
            automation_status[id].end_time = time.time()
            automation_status[id].error = str(e)
        return JSONResponse({"error": str(e)}, status_code=500)
    
    return JSONResponse(automation_status[id].model_dump())

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8000)