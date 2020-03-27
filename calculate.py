"""
Does the moving average calculation
"""
from database import db, Avg_calc
from datetime import datetime, timedelta
from time import sleep

if __name__ == "__main__":
    Avg_calc().run()