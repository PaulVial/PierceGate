import asyncpg

# Reads team budgets and computes consumption percentage
# Triggers alert_service when 80% / 100% thresholds are reached
