import random
import string
from datetime import date, timedelta

def generate_otp_code(length: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=length))

def get_current_week_start() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())

def get_available_weeks() -> list:
    """Returns exactly the past 4 weeks before the current week."""
    current_start = get_current_week_start()
    weeks = []
    # Get weeks starting from current week down to 4 weeks ago
    for i in range(0, 5):
        weeks.append(current_start - timedelta(days=7 * i))
    return weeks
