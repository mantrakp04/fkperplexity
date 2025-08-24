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
        minimum_wait_page_load_time=2.0,  # Increased for better stability
        maximum_wait_page_load_time=15.0,  # Much more generous timeout
        wait_for_network_idle_page_load_time=2.0,  # Wait longer for network idle
        default_timeout=45000,  # 90 seconds timeout (was 45s)
        default_navigation_timeout=60000,  # 2 minutes navigation timeout (was 60s)
        wait_between_actions=.3,  # Longer wait between actions for stability
        device_scale_factor=1.5,
        args=[
            "--force-device-scale-factor=1.5",
            "--disable-extensions-except",
            "--disable-plugins-discovery",
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
        
        # Create automation instructions with enhanced error handling and stability guidance
        instructions = f"""Fill out the {form_name} form at {form_url} using the provided data.
        
        CRITICAL INSTRUCTIONS:
        - Navigate to the specified URL: {form_url}
        - Wait for pages to fully load before interacting with elements
        - Fill out all form fields accurately using the provided data
        - Handle any pop-ups, confirmations, or navigation steps carefully
        - Use click tool for buttons and form interactions
        - Continue until the form is completely filled and submitted
        - Never stop until the task is fully completed
        
        DATA HANDLING RULES:
        - When data is missing, unclear, or you need to use placeholder values, ALWAYS use the alert_uncertain_data tool to flag the field for later review
        - Only use placeholder data when absolutely necessary to pass form validation
        - For dates, use the exact format required by the form (check placeholder text)
        - For dropdowns, select the closest matching option available
        - For required fields with no data, use "N/A" or similar and flag with alert tool
        - If form submission fails, check for validation errors and correct them

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
                
                await browser_session.start()
                # Update status to running automation
                status_manager.update_status(
                    session_id=id,
                    status="running",
                    current_step="form_automation",
                    message=f"Running form automation for {form_name}..."
                )
                # Create a controller with our custom action
                from browser_use.controller.service import Controller
                controller = Controller()

                # Register the alert_uncertain_data function as a custom action
                @controller.action("Alert when form data is uncertain or placeholder values are used")
                def alert_uncertain_data_action(field_name: str, expected_value: str, actual_value: str, reason: str, session_id: str = id) -> str:
                    return alert_uncertain_data(field_name, expected_value, actual_value, reason, session_id)

                # Create and run the automation agent with improved configuration
                agent = Agent(
                    task=instructions,
                    controller=controller,
                    llm=llm,
                    browser_session=browser_session,
                    max_failures=10,  # Significantly increased failure tolerance
                    retry_delay=30,  # Much longer retry delay for CDP recovery
                    max_actions_per_step=10,  # Reduced for better stability and control
                    use_vision=True,  # Enable vision for better element detection
                    generate_gif=False,  # Disable GIF generation to reduce overhead
                    extend_system_message="""CRITICAL FORM FILLING AND STABILITY CONTEXT:
                    - You are filling out government forms that require extreme accuracy
                    - Every field matters and errors can cause application rejection
                    - When uncertain about any data, use the alert_uncertain_data tool immediately
                    - Handle date fields with special care - check the required format first"""
                )

                result = await agent.run(max_steps=1000)

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
                # Stop session when done with error handling
                try:
                    if browser_session:
                        await browser_session.stop()
                except Exception as cleanup_error:
                    print(f"Warning: Error during browser session cleanup: {cleanup_error}")
                    # Don't raise cleanup errors, just log them
        
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