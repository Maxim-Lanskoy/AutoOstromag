"""
Energy tracking system for daily automation limits
"""

import json
import os
from datetime import datetime, time
from pathlib import Path

from utils.logger import setup_logger

logger = setup_logger(__name__)


class EnergyTracker:
    """Tracks daily energy usage with persistence and 12:00 reset"""
    
    def __init__(self, daily_limit: int = 0, exploration_start_hour: int = -1):
        """Initialize energy tracker with daily limit and time window"""
        self.daily_limit = daily_limit
        self.exploration_start_hour = exploration_start_hour
        self.data_file = Path("energy_data.json")
        self.energy_used = 0
        self.last_reset_date = None
        
        # Load existing data
        self.load_data()
        
        # Check if we need to reset
        self.check_daily_reset()
    
    def load_data(self):
        """Load energy data from file"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.energy_used = data.get('energy_used', 0)
                    self.last_reset_date = data.get('last_reset_date')
                    logger.info(f"Loaded energy data: {self.energy_used} energy used today")
            except Exception as e:
                logger.error(f"Error loading energy data: {e}")
                self.reset_daily_usage()
        else:
            self.reset_daily_usage()
    
    def save_data(self):
        """Save energy data to file"""
        try:
            data = {
                'energy_used': self.energy_used,
                'last_reset_date': self.last_reset_date
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Error saving energy data: {e}")
    
    def check_daily_reset(self):
        """Check if we need to reset daily usage (resets at 12:00)"""
        now = datetime.now()
        today_noon = now.replace(hour=12, minute=0, second=0, microsecond=0)
        
        # If we haven't reset yet
        if not self.last_reset_date:
            self.reset_daily_usage()
            return
        
        # Parse last reset date
        last_reset = datetime.fromisoformat(self.last_reset_date)
        
        # Check if we need to reset
        # Reset if: last reset was before today's noon AND current time is after noon
        # OR if last reset was more than 24 hours ago
        if (last_reset < today_noon and now >= today_noon) or \
           (now - last_reset).total_seconds() >= 86400:
            logger.info("Daily reset time reached (12:00) - resetting energy usage")
            self.reset_daily_usage()
    
    def reset_daily_usage(self):
        """Reset daily energy usage"""
        self.energy_used = 0
        self.last_reset_date = datetime.now().isoformat()
        self.save_data()
        logger.info("Daily energy usage reset to 0")
    
    def use_energy(self, amount: int = 1):
        """Record energy usage"""
        self.check_daily_reset()  # Always check for reset before using energy
        
        self.energy_used += amount
        self.save_data()
        logger.info(f"Used {amount} energy. Total today: {self.energy_used}/{self.daily_limit if self.daily_limit > 0 else '∞'}")
    
    def can_use_energy(self) -> bool:
        """Check if we can use more energy today"""
        self.check_daily_reset()  # Always check for reset
        
        # If no limit set, always allow
        if self.daily_limit <= 0:
            return True
        
        # Check if we've reached the limit
        return self.energy_used < self.daily_limit
    
    def get_remaining_energy(self) -> int:
        """Get remaining energy for today"""
        if self.daily_limit <= 0:
            return -1  # Unlimited
        return max(0, self.daily_limit - self.energy_used)
    
    def get_time_until_reset(self) -> str:
        """Get time remaining until next reset (12:00)"""
        now = datetime.now()
        today_noon = now.replace(hour=12, minute=0, second=0, microsecond=0)
        
        # If it's before noon, reset is today at noon
        if now < today_noon:
            reset_time = today_noon
        else:
            # If it's after noon, reset is tomorrow at noon
            tomorrow = now.replace(hour=12, minute=0, second=0, microsecond=0)
            reset_time = tomorrow.replace(day=tomorrow.day + 1)
        
        time_diff = reset_time - now
        hours = int(time_diff.total_seconds() // 3600)
        minutes = int((time_diff.total_seconds() % 3600) // 60)
        
        return f"{hours}h {minutes}m"
    
    def is_in_exploration_window(self) -> bool:
        """Check if current time is within exploration window"""
        # If no time restriction, always allow
        if self.exploration_start_hour < 0:
            return True
        
        now = datetime.now()
        current_hour = now.hour
        
        # Exploration window: start_hour to 12:00 (reset time)
        # Handle case where window crosses midnight (e.g., 23:00 to 12:00)
        if self.exploration_start_hour <= 12:
            # Normal case: e.g., 6:00 to 12:00
            return self.exploration_start_hour <= current_hour < 12
        else:
            # Crosses midnight: e.g., 23:00 to 12:00 (next day)
            return current_hour >= self.exploration_start_hour or current_hour < 12
    
    def get_time_until_exploration_window(self) -> str:
        """Get time remaining until exploration window opens"""
        if self.exploration_start_hour < 0 or self.is_in_exploration_window():
            return "0h 0m"
        
        now = datetime.now()
        
        # Calculate next exploration start time
        if now.hour < self.exploration_start_hour:
            # Same day
            start_time = now.replace(hour=self.exploration_start_hour, minute=0, second=0, microsecond=0)
        else:
            # Next day
            tomorrow = now.replace(hour=self.exploration_start_hour, minute=0, second=0, microsecond=0)
            start_time = tomorrow.replace(day=tomorrow.day + 1)
        
        time_diff = start_time - now
        hours = int(time_diff.total_seconds() // 3600)
        minutes = int((time_diff.total_seconds() % 3600) // 60)
        
        return f"{hours}h {minutes}m"
    
    def can_explore_now(self) -> bool:
        """Check if bot can explore now (considering both energy limit and time window)"""
        # Check daily reset first
        self.check_daily_reset()
        
        # Check time window
        if not self.is_in_exploration_window():
            return False
        
        # Check energy limit
        return self.can_use_energy()