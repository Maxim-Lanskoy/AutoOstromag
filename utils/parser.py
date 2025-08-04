"""
Simplified Game message parser
"""

import re
from utils.logger import setup_logger

logger = setup_logger(__name__)


class GameParser:
    """Parse basic game messages"""
    
    def parse_battle_rewards(self, text):
        """Parse battle rewards (kept for compatibility)"""
        try:
            rewards = {}
            
            # Parse gold
            gold_match = re.search(r'💰 (\d+) золота', text)
            if gold_match:
                rewards['gold'] = int(gold_match.group(1))
            
            # Parse experience
            exp_match = re.search(r'⭐ (\d+) досвіду', text)
            if exp_match:
                rewards['experience'] = int(exp_match.group(1))
            
            return rewards
            
        except Exception as e:
            logger.error(f"Error parsing battle rewards: {e}")
            return None