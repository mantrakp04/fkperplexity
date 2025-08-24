import time
from typing import Dict, List
from browser_use import Agent, BrowserSession
from browser_use.llm.anthropic.chat import ChatAnthropic
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from utils import (
    StatusManager, 
    validate_session_id,
    format_duration
)

load_dotenv()

# Import models from utils
from utils import AutomationStatus, FormAlert

mcp = FastMCP(
    name="Browser Automation Service", 
    instructions="Automated web form filling service with real-time status tracking."
)

# Helper function to add CORS headers
def add_cors_headers(response: JSONResponse) -> JSONResponse:
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# Initialize status manager
status_manager = StatusManager()

@mcp.custom_route("/tracking/status/{session_id}", methods=["GET"])
async def get_automation_status(request: Request) -> JSONResponse:
    """Get the current status of an automation session"""
    session_id = request.path_params["session_id"]
    
    if not validate_session_id(session_id):
        return JSONResponse(
            {"error": "Invalid session ID format"},
            status_code=400
        )
    
    status = status_manager.get_status(session_id)
    if not status:
        return JSONResponse({
            "session_id": session_id,
            "status": "not_found",
            "message": "No automation found for this session ID"
        })
    
    response_data = status.model_dump()
    
    # Add computed fields
    if status.start_time:
        response_data["duration"] = format_duration(status.start_time, status.end_time)
    
    return JSONResponse(response_data)

@mcp.custom_route("/tracking/status", methods=["GET"])
async def get_all_automation_status(_: Request) -> JSONResponse:
    """Get the status of all automation sessions"""
    all_statuses = status_manager.get_all_statuses()
    
    sessions_data = {}
    for session_id, status in all_statuses.items():
        status_data = status.model_dump()
        # Add duration info
        if status.start_time:
            status_data["duration"] = format_duration(status.start_time, status.end_time)
        sessions_data[session_id] = status_data
    
    return JSONResponse({
        "sessions": sessions_data,
        "total_sessions": len(all_statuses)
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
    # Validate inputs
    if not validate_session_id(session_id):
        session_id = "default_session"
    
    alert = status_manager.add_alert(
        session_id=session_id,
        field_name=field_name,
        expected_value=expected_value,
        actual_value=actual_value,
        reason=reason
    )
    
    return f"Alert logged: Field '{field_name}' flagged for review. Used '{actual_value}' but expected '{expected_value}'. Reason: {reason}"

@mcp.custom_route("/tracking/alerts", methods=["GET"])
async def get_form_alerts(_: Request) -> JSONResponse:
    """Get all form alerts across all sessions"""
    all_alerts = status_manager.get_all_alerts()
    
    return JSONResponse({
        "alerts": [alert.model_dump() for alert in all_alerts],
        "total_alerts": len(all_alerts)
    })

@mcp.custom_route("/tracking/alerts/{session_id}", methods=["GET"])
async def get_session_alerts(request: Request) -> JSONResponse:
    """Get form alerts for a specific session"""
    session_id = request.path_params["session_id"]
    
    if not validate_session_id(session_id):
        return JSONResponse(
            {"error": "Invalid session ID format"},
            status_code=400
        )
    
    session_alerts = status_manager.get_session_alerts(session_id)
    
    return JSONResponse({
        "session_id": session_id,
        "alerts": [alert.model_dump() for alert in session_alerts],
        "total_alerts": len(session_alerts)
    })

@mcp.custom_route("/tracking/summary/{session_id}", methods=["GET"])
async def get_session_summary(request: Request) -> JSONResponse:
    """Get complete summary for a session including status and alerts"""
    session_id = request.path_params["session_id"]
    
    if not validate_session_id(session_id):
        return JSONResponse(
            {"error": "Invalid session ID format"},
            status_code=400
        )
    
    summary = status_manager.get_session_summary(session_id)
    if not summary:
        return JSONResponse({
            "session_id": session_id,
            "status": "not_found",
            "message": "No session found with this ID"
        })
    
    # Add duration info if available
    if summary["status"].get("start_time"):
        summary["status"]["duration"] = format_duration(
            summary["status"]["start_time"], 
            summary["status"].get("end_time")
        )
    
    return JSONResponse(summary)

@mcp.custom_route("/tracking/cleanup/{session_id}", methods=["DELETE"])
async def cleanup_session_data(request: Request) -> JSONResponse:
    """Clean up all data for a specific session"""
    session_id = request.path_params["session_id"]
    
    if not validate_session_id(session_id):
        return JSONResponse(
            {"error": "Invalid session ID format"},
            status_code=400
        )
    
    success = status_manager.clear_session_data(session_id)
    
    return JSONResponse({
        "session_id": session_id,
        "cleaned": success,
        "message": "Session data cleaned successfully" if success else "No data found for session"
    })

def get_or_create_browser_session(session_id: str) -> BrowserSession:
    """Get or create a persistent browser session based on ID with improved timeout and stability settings"""
    from browser_use.browser.profile import BrowserProfile
    
    profile = BrowserProfile(
        keep_alive=True,
        user_data_dir=f'~/.config/browseruse/profiles/{session_id}',
        viewport={"width": 1280, "height": 1024},
        minimum_wait_page_load_time=1.0,  # Increased for stability
        maximum_wait_page_load_time=5.0,  # Increased for stability
        wait_for_network_idle_page_load_time=2.0,  # Wait for network idle
        device_scale_factor=1.5,
        default_timeout=45000,  # 45 seconds timeout
        default_navigation_timeout=60000,  # 60 seconds navigation timeout
        wait_between_actions=1.0,  # Wait between actions
        args=[
            "--force-device-scale-factor=1.5",
            "--disable-blink-features=AutomationControlled",  # Reduce detection
            "--disable-extensions-except",
            "--disable-plugins-discovery",
            "--no-first-run"
        ]
    )
    
    return BrowserSession(
        id=session_id,
        browser_profile=profile
    )

@mcp.custom_route("/automated_form_filler", methods=["POST", "OPTIONS"])
async def main(request: Request) -> JSONResponse:
    # Handle preflight requests
    if request.method == "OPTIONS":
        response = JSONResponse({"status": "ok"})
        return add_cors_headers(response)
    # Extract parameters from request body
    try:
        body = await request.json()
    except Exception:
        body = {}
    
    id = body.get("id", "default_session")
    form_name = body.get("form_name", "J-1 Visa Waiver (DS-3035)")
    form_url = body.get("form_url", "ceac.state.gov/genniv/")
    form_data = body.get("form_data", """Example Input:

Personal Information:
- Title: Dr.
- Surname: [As in Passport]
- Given Names: [As in Passport, First and Middle]
- Maiden Name: [If Any]
- Other Names: [Aliases, previous married names, religious names, professional names, etc.]
- Date of Birth: [mm-dd-yyyy]
- Gender: Male/Female
- City of Birth: [City]
- Country of Birth: [Country]
- Citizenship Country: [Country]
- Legal Permanent Residence Country: [Country]

Contact Information:
- Current Address: [Street, City, State/Province, ZIP/Postal Code, Country]
- Home Phone: [Phone Number]
- Business Phone: [Phone Number]
- Facsimile: [Fax Number]
- Email Address: [Email]
- Last U.S. City and State: [If not currently living in U.S.]

Attorney/Representation:
- Are you represented by an attorney or organization? Yes/No
- Attorney/Representative/Organization Name: [Name]
- Attorney Address: [Street, City, State, ZIP Code, Country]
- Business Phone/Extension: [Phone]
- Facsimile: [Fax]
- Email Address: [Email]

Exchange Visitor Program Information:
- SEVIS Number: [Number]
- Program Number: [Number]
- Purpose of the Form: [Purpose]
- Begin Date: [mm-dd-yyyy]
- End Date: [mm-dd-yyyy]
- Subject/Field Code: [Code]
- Funding Amount: [Amount]
- Did program include U.S. Government funds, own government funds, or international organization funds? Yes/No

Waiver Request Basis:
- I am requesting a waiver recommendation based on: [Check one]
  * Exceptional Hardship
  * Interested Government Agency (non-physician)
  * State Health Agency Request
  * Interested Government Agency (Physician)
  * No Objection Statement
  * Persecution

Dependent Information:
- Does this application include J-2 dependents? Yes/No
- If yes, provide: Surname, Given Name, Date of Birth, Country of Birth, Relationship

Spouse Information:
- Is your spouse in J-1 status? Yes/No
- If spouse has applied for waiver: Surname, Given Name, Date of Birth, Country of Birth, J Waiver Case Number

Entry Information:
- Date and place of first entry into U.S. on J-1 visa: [Date, Port of Entry, State of Entry, Visa Control Number, Issuing Post]
- Alien Registration Number: [If any]
- I-94 Number: [Number]

Previous Applications:
- Have you ever applied for J visa waiver recommendation or advisory opinion? Yes/No
- If yes, provide: Case Number, Date Received, Fee Paid, G-28

Mailing Preferences:
- I request all correspondence be sent to: [Check one]
  * Current Address
  * Attorney Address
  * Mailing Address

Supporting Documents:
- Application fee: $215 (cashier's check or money order)
- Statement demonstrating eligibility for waiver
- Copies of all DS-2019 forms
- G-28 form (if represented by attorney)
- Two self-addressed stamped envelopes
- Copy of passport data page
- Additional pages for complete responses

Certification:
- I certify that I have read and understood all questions and answers are true and correct
- Signature of Exchange Visitor: [Signature]
- Date: [Date]

Mailing Address:
U.S. Department of State
Waiver Review Division
P.O. Box 952137
St. Louis, MO 63195-2137
""")
    # Validate session ID
    if not validate_session_id(id):
        return JSONResponse(
            {"error": "Invalid session ID format"},
            status_code=400
        )
    
    # Initialize status tracking with helper
    status_manager.create_status(
        session_id=id,
        form_name=form_name,
        form_url=form_url,
        initial_message="Automation starting..."
    )
    
    try:
        # Update status to model initialization
        status_manager.update_status(
            session_id=id,
            status="initializing",
            current_step="creating_llm_model",
            message="Initializing language model..."
        )
        
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
        
        # Create automation instructions with improved error handling and form filling guidance
        instructions = f"""Fill out the {form_name} form at {form_url} using the provided data.
        
        CRITICAL INSTRUCTIONS:
        - Navigate to the specified URL: {form_url}
        - Wait for pages to fully load before interacting with elements
        - Fill out all form fields accurately using the provided data
        - Handle any pop-ups, confirmations, or navigation steps carefully
        - Use click tool for buttons and form interactions
        - If you encounter captcha, wait and retry the operation
        - Continue until the form is completely filled and submitted
        - Never stop until the task is fully completed
        
        DATA HANDLING RULES:
        - When data is missing, unclear, or you need to use placeholder values, ALWAYS use the alert_uncertain_data tool to flag the field for later review
        - Only use placeholder data when absolutely necessary to pass form validation
        - For dates, use the exact format required by the form (check placeholder text)
        - For dropdowns, select the closest matching option available
        - For required fields with no data, use "N/A" or similar and flag with alert tool
        
        ERROR HANDLING:
        - If a page doesn't load properly, wait 3 seconds and try again
        - If elements are not found, scroll to find them or refresh the page
        - If form submission fails, check for validation errors and correct them
        - Use the wait action liberally when pages are loading
        - If stuck, try alternative navigation paths
        
        FORM DATA TO USE:
        {form_data}
        
        Target URL: {form_url}
        Session ID for alerts: {id}"""
        
        # Update status to browser session creation
        status_manager.update_status(
            session_id=id,
            status="initializing",
            current_step="creating_browser_session",
            message="Creating browser session..."
        )
        
        # Get or create browser session
        browser_session = get_or_create_browser_session(id)
        
        async def run_automation():
            try:
                # Update status to starting browser
                status_manager.update_status(
                    session_id=id,
                    status="running",
                    current_step="starting_browser",
                    message="Starting browser session..."
                )
                
                # Start the session
                await browser_session.start()
                
                # Update status to running automation
                status_manager.update_status(
                    session_id=id,
                    status="running",
                    current_step="form_automation",
                    message=f"Running form automation for {form_name}..."
                )
                
                # Create and run the automation agent with improved configuration
                agent = Agent(
                    task=instructions,
                    llm=llm,
                    browser_session=browser_session,
                    max_failures=5,  # Increased failure tolerance
                    retry_delay=15,  # Increased retry delay
                    max_actions_per_step=8,  # Reduced actions per step for stability
                    additional_tools=[alert_uncertain_data],
                    use_vision=True,  # Enable vision for better element detection
                    extend_system_message="""IMPORTANT FORM FILLING CONTEXT:
                    - You are filling out government forms that require extreme accuracy
                    - Every field matters and errors can cause application rejection
                    - When uncertain about any data, use the alert_uncertain_data tool immediately
                    - Handle date fields with special care - check the required format first"""
                )

                # Execute the automation with progress tracking
                async def progress_hook(agent_obj):
                    """Track progress and update status"""
                    try:
                        current_step = len(agent_obj.history) if hasattr(agent_obj, 'history') else 0
                        # Simple progress tracking
                        status_manager.update_status(
                            session_id=id,
                            message=f"Processing step {current_step}..."
                        )
                    except Exception as e:
                        print(f"Progress hook error: {e}")
                
                result = await agent.run(max_steps=500, on_step_start=progress_hook)  # Reduced max steps
                
                # Update status to completed
                status_manager.update_status(
                    session_id=id,
                    status="completed",
                    current_step="finished",
                    message="Automation completed successfully",
                    result=str(result) if result else "No result returned"
                )
                
                return result
                
            except Exception as e:
                # Update status to error
                status_manager.update_status(
                    session_id=id,
                    status="error",
                    current_step="error_occurred",
                    message=f"Error during automation: {str(e)}",
                    error=str(e)
                )
                raise
            finally:
                # Stop session when done
                await browser_session.stop()
        
        # Execute the automation
        result = await run_automation()
        if result.is_done() and not result.is_successful():
            status_manager.update_status(
                session_id=id,
                status="error",
                current_step="fatal_error",
                message=f"Fatal error: {str(result.error)}",
                error=str(result.error)
            )
        
    except Exception as e:
        # Update status to error if not already updated
        current_status = status_manager.get_status(id)
        if current_status and current_status.status != "error":
            status_manager.update_status(
                session_id=id,
                status="error",
                current_step="fatal_error",
                message=f"Fatal error: {str(e)}",
                error=str(e)
            )
        response = JSONResponse({"error": str(e)}, status_code=500)
        return add_cors_headers(response)
    
    final_status = status_manager.get_status(id)
    if final_status:
        response_data = final_status.model_dump()
        response = JSONResponse(response_data)
        return add_cors_headers(response)
    else:
        response = JSONResponse({"error": "Failed to retrieve final status"}, status_code=500)
        return add_cors_headers(response)

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8000)