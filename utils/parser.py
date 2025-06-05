"""
Game message parser
"""

import re
from utils.logger import setup_logger

logger = setup_logger(__name__)


class GameParser:
    """Parse game messages"""
    
    def parse_character_info(self, text):
        """Parse character information from message"""
        try:
            info = {}
            
            # Parse level
            level_match = re.search(r'Рівень (\d+)', text)
            if level_match:
                info['level'] = int(level_match.group(1))
            
            # Parse health
            health_match = re.search(r'Здоров\'я: (\d+)/(\d+)', text)
            if health_match:
                info['health'] = int(health_match.group(1))
                info['max_health'] = int(health_match.group(2))
            
            # Parse energy
            energy_match = re.search(r'Енергія: (\d+)/(\d+)', text)
            if energy_match:
                info['energy'] = int(energy_match.group(1))
                info['max_energy'] = int(energy_match.group(2))
            
            # Parse stats
            attack_match = re.search(r'Атака: (\d+)', text)
            if attack_match:
                info['attack'] = int(attack_match.group(1))
            
            defense_match = re.search(r'Захист: (\d+)', text)
            if defense_match:
                info['defense'] = int(defense_match.group(1))
            
            # Parse gold
            gold_match = re.search(r'Золото: (\d+)', text)
            if gold_match:
                info['gold'] = int(gold_match.group(1))
            
            # Parse experience
            exp_match = re.search(r'Досвід: (\d+)/(\d+)', text)
            if exp_match:
                info['experience'] = int(exp_match.group(1))
                info['max_experience'] = int(exp_match.group(2))
            
            return info
            
        except Exception as e:
            logger.error(f"Error parsing character info: {e}")
            return None
    
    def parse_battle_start(self, text):
        """Parse battle start message"""
        try:
            info = {}
            
            # Parse enemy name
            enemy_match = re.search(r'З\'явився (.+?)!', text)
            if enemy_match:
                info['enemy_name'] = enemy_match.group(1)
            
            # Parse enemy stats
            health_match = re.search(r'Здоров\'я: (\d+)/(\d+)', text)
            if health_match:
                info['enemy_health'] = int(health_match.group(1))
                info['enemy_max_health'] = int(health_match.group(2))
            
            attack_match = re.search(r'Атака: (\d+)', text)
            if attack_match:
                info['enemy_attack'] = int(attack_match.group(1))
            
            defense_match = re.search(r'Захист: (\d+)', text)
            if defense_match:
                info['enemy_defense'] = int(defense_match.group(1))
            
            return info
            
        except Exception as e:
            logger.error(f"Error parsing battle start: {e}")
            return None
    
    def parse_battle_round(self, text):
        """Parse battle round information"""
        try:
            info = {}
            
            # Parse round number
            round_match = re.search(r'Раунд (\d+)', text)
            if round_match:
                info['round'] = int(round_match.group(1))
            
            # Parse player health
            player_match = re.search(r'👤 Ви \((\d+)/(\d+)\)', text)
            if player_match:
                info['player_health'] = int(player_match.group(1))
                info['player_max_health'] = int(player_match.group(2))
            
            # Parse enemy health
            enemy_match = re.search(r'[🦂🦇🐍🐺] .+? \((\d+)/(\d+)\)', text)
            if enemy_match:
                info['enemy_health'] = int(enemy_match.group(1))
                info['enemy_max_health'] = int(enemy_match.group(2))
            
            # Parse damage dealt/received
            damage_dealt_match = re.search(r'Ви завдали (\d+) шкоди', text)
            if damage_dealt_match:
                info['damage_dealt'] = int(damage_dealt_match.group(1))
            
            damage_received_match = re.search(r'Ворог завдав (\d+) шкоди', text)
            if damage_received_match:
                info['damage_received'] = int(damage_received_match.group(1))
            
            return info
            
        except Exception as e:
            logger.error(f"Error parsing battle round: {e}")
            return None
    
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
    
    def parse_heal_cost(self, text):
        """Parse healing cost"""
        try:
            info = {}
            
            # Parse current health
            health_match = re.search(r'Здоров\'я: (\d+)/(\d+)', text)
            if health_match:
                info['current_health'] = int(health_match.group(1))
                info['max_health'] = int(health_match.group(2))
            
            # Parse heal cost
            cost_match = re.search(r'Вартість лікування (\d+) ОЗ: 💰 (\d+)', text)
            if cost_match:
                info['health_to_heal'] = int(cost_match.group(1))
                info['cost'] = int(cost_match.group(2))
            
            return info
            
        except Exception as e:
            logger.error(f"Error parsing heal cost: {e}")
            return None
    
    def parse_shop_item(self, text):
        """Parse shop item information"""
        try:
            info = {}
            
            # Parse item name
            name_match = re.search(r'([⚔️🛡️🧥👢🎩📿🪶].+?)\n', text)
            if name_match:
                info['name'] = name_match.group(1).strip()
            
            # Parse price
            price_match = re.search(r'Ціна: (\d+) золота', text)
            if price_match:
                info['price'] = int(price_match.group(1))
            
            # Parse level requirement
            level_match = re.search(r'Мінімальний рівень: (\d+)', text)
            if level_match:
                info['min_level'] = int(level_match.group(1))
            
            # Parse stats
            stats = {}
            attack_match = re.search(r'Атака: \+(\d+)', text)
            if attack_match:
                stats['attack'] = int(attack_match.group(1))
            
            defense_match = re.search(r'Захист: \+(\d+)', text)
            if defense_match:
                stats['defense'] = int(defense_match.group(1))
            
            health_match = re.search(r'Здоров\'я: \+(\d+)', text)
            if health_match:
                stats['health'] = int(health_match.group(1))
            
            if stats:
                info['stats'] = stats
            
            return info
            
        except Exception as e:
            logger.error(f"Error parsing shop item: {e}")
            return None
    
    def parse_inventory_item(self, text):
        """Parse inventory item"""
        try:
            info = {}
            
            # Parse item name (first line)
            lines = text.strip().split('\n')
            if lines:
                info['name'] = lines[0].strip()
            
            # Parse quantity
            quantity_match = re.search(r'Кількість: (\d+)', text)
            if quantity_match:
                info['quantity'] = int(quantity_match.group(1))
            
            # Parse type
            type_match = re.search(r'Тип: (.+)', text)
            if type_match:
                info['type'] = type_match.group(1).strip()
            
            # Parse effect
            effect_match = re.search(r'Ефект: (.+?)╰', text, re.DOTALL)
            if effect_match:
                info['effect'] = effect_match.group(1).strip()
            
            return info
            
        except Exception as e:
            logger.error(f"Error parsing inventory item: {e}")
            return None
    
    def parse_equipment(self, text):
        """Parse equipped items"""
        try:
            equipment = {}
            
            # Parse each equipment slot
            slots = {
                'weapon': r'⚔️ (.+)',
                'hat': r'🎩 (.+)',
                'coat': r'🧥 (.+)',
                'armor': r'🥋 (.+)',
                'shield': r'🛡 (.+)',
                'pants': r'👖 (.+)',
                'boots': r'👢 (.+)',
                'amulet': r'📿 (.+)',
                'accessory': r'🪶 (.+)'
            }
            
            for slot, pattern in slots.items():
                match = re.search(pattern, text)
                if match:
                    item = match.group(1).strip()
                    if item != "Порожній слот":
                        equipment[slot] = item
            
            return equipment
            
        except Exception as e:
            logger.error(f"Error parsing equipment: {e}")
            return None
