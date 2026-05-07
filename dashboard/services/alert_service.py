import aiosmtplib
import httpx

from config import settings

# Sends alerts via email (SMTP) and Slack (webhook)
# Triggered at 80% and 100% of monthly budget
