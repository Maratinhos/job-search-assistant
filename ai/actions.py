# ai/actions.py
"""
Реестр действий AI, который сопоставляет имена действий с методами клиента AI и другой метаинформацией.
"""
from bot import messages

ACTION_REGISTRY = {
    "analyze_match": {
        "ai_method_name": "analyze_match",
        "response_header": messages.ANALYSIS_COMPLETE,
    },
    "generate_letter": {
        "ai_method_name": "generate_cover_letter",
        "response_header": messages.COVER_LETTER_COMPLETE,
    },
    "generate_hr_plan": {
        "ai_method_name": "generate_hr_call_plan",
        "response_header": messages.HR_CALL_PLAN_COMPLETE,
    },
    "generate_tech_plan": {
        "ai_method_name": "generate_tech_interview_plan",
        "response_header": messages.TECH_INTERVIEW_PLAN_COMPLETE,
    },
}
