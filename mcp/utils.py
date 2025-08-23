import time
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class AutomationStatus(BaseModel):
    session_id: str
    status: str
    form_name: str
    form_url: str
    start_time: float
    current_step: str
    progress: int = Field(ge=0, le=100)
    message: str
    end_time: Optional[float] = None
    result: Optional[str] = None
    error: Optional[str] = None


class FormAlert(BaseModel):
    session_id: str
    field_name: str
    expected_value: str
    actual_value: str
    reason: str
    timestamp: float = Field(default_factory=time.time)


class StatusManager:
    """Helper class for managing automation status and form alerts"""
    
    def __init__(self):
        self.automation_status: Dict[str, AutomationStatus] = {}
        self.form_alerts: List[FormAlert] = []
    
    def create_status(
        self,
        session_id: str,
        form_name: str,
        form_url: str,
        initial_message: str = "Automation starting..."
    ) -> AutomationStatus:
        """Create a new automation status entry"""
        status = AutomationStatus(
            session_id=session_id,
            status="starting",
            form_name=form_name,
            form_url=form_url,
            start_time=time.time(),
            current_step="initializing",
            progress=0,
            message=initial_message
        )
        self.automation_status[session_id] = status
        return status
    
    def update_status(
        self,
        session_id: str,
        status: Optional[str] = None,
        current_step: Optional[str] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        error: Optional[str] = None,
        result: Optional[str] = None
    ) -> Optional[AutomationStatus]:
        """Update an existing automation status"""
        if session_id not in self.automation_status:
            return None
        
        automation = self.automation_status[session_id]
        
        if status is not None:
            automation.status = status
        if current_step is not None:
            automation.current_step = current_step
        if progress is not None:
            automation.progress = max(0, min(100, progress))
        if message is not None:
            automation.message = message
        if error is not None:
            automation.error = error
        if result is not None:
            automation.result = result
        
        # Set end time for terminal states
        if status in ["completed", "error"]:
            automation.end_time = time.time()
        
        return automation
    
    def get_status(self, session_id: str) -> Optional[AutomationStatus]:
        """Get status for a specific session"""
        return self.automation_status.get(session_id)
    
    def get_all_statuses(self) -> Dict[str, AutomationStatus]:
        """Get all automation statuses"""
        return self.automation_status.copy()
    
    def add_alert(
        self,
        session_id: str,
        field_name: str,
        expected_value: str,
        actual_value: str,
        reason: str
    ) -> FormAlert:
        """Add a form alert"""
        alert = FormAlert(
            session_id=session_id,
            field_name=field_name,
            expected_value=expected_value,
            actual_value=actual_value,
            reason=reason
        )
        self.form_alerts.append(alert)
        return alert
    
    def get_session_alerts(self, session_id: str) -> List[FormAlert]:
        """Get alerts for a specific session"""
        return [alert for alert in self.form_alerts if alert.session_id == session_id]
    
    def get_all_alerts(self) -> List[FormAlert]:
        """Get all form alerts"""
        return self.form_alerts.copy()
    
    def clear_session_data(self, session_id: str) -> bool:
        """Clear all data for a specific session"""
        status_removed = self.automation_status.pop(session_id, None) is not None
        alerts_before = len(self.form_alerts)
        self.form_alerts = [alert for alert in self.form_alerts if alert.session_id != session_id]
        alerts_removed = len(self.form_alerts) < alerts_before
        
        return status_removed or alerts_removed
    
    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """Get a complete summary for a session including status and alerts"""
        status = self.get_status(session_id)
        if not status:
            return None
        
        alerts = self.get_session_alerts(session_id)
        
        return {
            "status": status.model_dump(),
            "alerts": [alert.model_dump() for alert in alerts],
            "alert_count": len(alerts)
        }




# Validation helpers
def validate_session_id(session_id: str) -> bool:
    """Validate session ID format"""
    if not session_id or len(session_id.strip()) == 0:
        return False
    
    # Allow alphanumeric, hyphens, and underscores
    import re
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', session_id))


def sanitize_field_name(field_name: str) -> str:
    """Sanitize field name for safe logging"""
    if not field_name:
        return "unknown_field"
    
    # Replace special characters with underscores
    import re
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', field_name)
    return sanitized.strip('_')[:50]  # Limit length


def format_duration(start_time: float, end_time: Optional[float] = None) -> str:
    """Format duration in human-readable format"""
    if end_time is None:
        end_time = time.time()
    
    duration = end_time - start_time
    
    if duration < 60:
        return f"{duration:.1f} seconds"
    elif duration < 3600:
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        return f"{minutes}m {seconds}s"
    else:
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        return f"{hours}h {minutes}m"