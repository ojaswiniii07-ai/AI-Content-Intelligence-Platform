from app.services.integrations.adapters.google_forms import GoogleFormsAdapter
from app.services.integrations.adapters.typeform import TypeformAdapter
from app.services.integrations.adapters.canvas_lms import CanvasLMSAdapter
from app.services.integrations.adapters.moodle import MoodleAdapter
from app.services.integrations.adapters.blackboard import BlackboardAdapter
from app.services.integrations.adapters.custom import CustomClientAdapter
from app.services.integrations.adapters.mock import MockIntegrationAdapter

__all__ = [
    "GoogleFormsAdapter",
    "TypeformAdapter",
    "CanvasLMSAdapter",
    "MoodleAdapter",
    "BlackboardAdapter",
    "CustomClientAdapter",
    "MockIntegrationAdapter",
]
