# utils.py
from datetime import datetime

def get_financial_year():
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month

    if current_month >= 6:
        start_year = current_year
        end_year = current_year + 1
    else:
        start_year = current_year - 1
        end_year = current_year

    return f"{start_year}/{end_year}"