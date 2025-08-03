"""
Game message parser
"""

import re
from utils.logger import setup_logger

logger = setup_logger(__name__)


class GameParser:
    """Parse game messages"""
    
    def parse_battle_rewards(self, text):
        """Parse battle rewards"""
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
            
            # Parse items
            if "Знайдені предмети:" in text:
                items = []
                # Look for item patterns after "Знайдені предмети:"
                items_section = text.split("Знайдені предмети:")[1]
                item_lines = items_section.strip().split('\n')
                for line in item_lines:
                    if line.strip() and any(emoji in line for emoji in ['🪨', '🧱', '⚔️', '🛡️', '🟤', '🟢', '🔵']):
                        items.append(line.strip())
                if items:
                    rewards['items'] = items
            
            return rewards
            
        except Exception as e:
            logger.error(f"Error parsing battle rewards: {e}")
            return None