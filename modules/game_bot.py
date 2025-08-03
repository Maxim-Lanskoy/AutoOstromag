"""
Game Bot Controller - Final Fixed Version
Properly handles all battle scenarios including initial battle messages
"""

import asyncio
import re
import random
from datetime import datetime, timedelta
from telethon import events, Button
from telethon.tl.custom import Message

from utils.logger import setup_logger
from utils.parser import GameParser

logger = setup_logger(__name__)


class GameBot:
    """
    Main game bot controller with comprehensive state management
    
    Features:
    - Automatic exploration with energy efficiency
    - Smart battle handling with escape mechanics
    - Camp (табір) detection and interaction
    - Player greeting for resource collection
    - Automatic HP/energy regeneration tracking
    """
    
    def __init__(self, client, config):
        """Initialize bot with client and configuration"""
        self.client = client
        self.config = config
        self.parser = GameParser()
        
        # Bot state management
        self.game_chat = None
        self.is_running = False
        self.pending_camp_visit = False
        
        # Character statistics tracking
        self.current_hp = self.config.MAXIMUM_HEALTH_PLACEHOLDER
        self.max_hp = self.config.MAXIMUM_HEALTH_PLACEHOLDER
        self.current_energy = 10
        self.max_energy = 10
        self.level = 1
        self.gold = 0
        
        # Timing and regeneration tracking
        self.last_energy_use = datetime.now()
        self.energy_regen_time = None
        
        # Battle escape thresholds
        self.LOW_HP_THRESHOLD = config.LOW_HP_THRESHOLD
        self.CRITICAL_HP_THRESHOLD = config.CRITICAL_HP_THRESHOLD
        
        # Debug logging flag
        self.DEBUG_LOGGING = getattr(config, 'VERBOSE_LOGGING', True)
        
        # Battle outcome tracking
        self.battle_stats = {
            'wins': 0,
            'losses': 0,
            'escapes': 0,
            'enemy_types': {},
            'total_battles': 0
        }
        
        # Error recovery tracking
        self.consecutive_errors = 0
        self.last_error_time = None
    
    def set_debug_logging(self, enabled: bool):
        """Enable or disable verbose debug logging"""
        self.DEBUG_LOGGING = enabled
        logger.info(f"Debug logging {'enabled' if enabled else 'disabled'}")
        
    async def human_delay(self, min_seconds=None, max_seconds=None):
        """Simulate human-like reaction time with randomized delays"""
        if min_seconds is None:
            min_seconds = self.config.HUMAN_DELAY_MIN
        if max_seconds is None:
            max_seconds = self.config.HUMAN_DELAY_MAX
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def handle_error_recovery(self, error, operation_name):
        """Handle errors with exponential backoff and recovery"""
        self.consecutive_errors += 1
        self.last_error_time = datetime.now()
        
        if self.consecutive_errors >= self.config.MAX_CONSECUTIVE_ERRORS:
            logger.error(f"Too many consecutive errors ({self.consecutive_errors}), taking longer break")
            await asyncio.sleep(self.config.ERROR_RETRY_DELAY * 2)
            self.consecutive_errors = 0
        else:
            delay = self.config.BASE_DELAY * (self.config.RETRY_DELAY_MULTIPLIER ** self.consecutive_errors)
            logger.warning(f"Error in {operation_name}: {error}. Retrying in {delay:.1f}s (attempt {self.consecutive_errors})")
            await asyncio.sleep(delay)
    
    def reset_error_counter(self):
        """Reset error counter after successful operation"""
        if self.consecutive_errors > 0:
            logger.info(f"Recovered after {self.consecutive_errors} errors")
            self.consecutive_errors = 0
    
    def track_battle_outcome(self, outcome, enemy_name=None):
        """Track battle outcomes for learning"""
        if not self.config.TRACK_BATTLE_OUTCOMES:
            return
            
        self.battle_stats['total_battles'] += 1
        
        if outcome == 'win':
            self.battle_stats['wins'] += 1
        elif outcome == 'loss':
            self.battle_stats['losses'] += 1
        elif outcome == 'escape':
            self.battle_stats['escapes'] += 1
        
        if enemy_name:
            if enemy_name not in self.battle_stats['enemy_types']:
                self.battle_stats['enemy_types'][enemy_name] = {'wins': 0, 'losses': 0, 'escapes': 0}
            self.battle_stats['enemy_types'][enemy_name][outcome] += 1
        
        # Log stats occasionally
        if self.battle_stats['total_battles'] % 10 == 0:
            win_rate = (self.battle_stats['wins'] / self.battle_stats['total_battles']) * 100
            logger.info(f"Battle stats: {self.battle_stats['wins']}W/{self.battle_stats['losses']}L/{self.battle_stats['escapes']}E ({win_rate:.1f}% win rate)")
    
    async def check_for_potions(self, msg, current_hp=None):
        """Check for and use potions if available (Зілля button) - only when HP is low"""
        if not self.config.USE_POTIONS_IN_BATTLE:
            return False, False
        
        # Only use potions if HP is below threshold
        if current_hp and current_hp > self.config.HEALING_POTION_HP_THRESHOLD:
            return False, False
            
        has_potions_button = False
        potions_button_pos = None
        
        for row_idx, row in enumerate(msg.buttons):
            for btn_idx, btn in enumerate(row):
                if btn.text and "Зілля" in btn.text:
                    has_potions_button = True
                    potions_button_pos = (row_idx, btn_idx)
                    logger.info(f"Potions (Зілля) button detected! Current HP: {current_hp}")
                    break
            if has_potions_button:
                break
        
        if has_potions_button and potions_button_pos:
            # Double-check HP before actually using potion
            if current_hp and current_hp > self.config.HEALING_POTION_HP_THRESHOLD:
                logger.info(f"HP ({current_hp}) is above threshold ({self.config.HEALING_POTION_HP_THRESHOLD}), skipping potion")
                return True, False  # Button available but not used
                
            try:
                await self.human_delay()
                await msg.click(potions_button_pos[0], potions_button_pos[1])
                logger.info(f"Clicked potions (Зілля) button! HP: {current_hp}")
                
                # Wait for potion selection message
                await asyncio.sleep(self.config.BASE_DELAY)
                potion_messages = await self.client.get_messages(self.game_chat, limit=3)
                
                for potion_msg in potion_messages:
                    if potion_msg.text and "Оберіть зілля для використання:" in potion_msg.text:
                        if potion_msg.buttons and len(potion_msg.buttons) > 0:
                            # Click the first potion option (healing potion preference)
                            await self.human_delay()
                            await potion_msg.click(0, 0)
                            logger.info("Selected first potion from the list!")
                            await asyncio.sleep(self.config.BASE_DELAY)
                            return True, True
                return True, False
            except Exception as e:
                logger.error(f"Failed to use potions: {e}")
                return False, False
        
        return False, False
    
    async def check_for_skills(self, msg):
        """Check for and use skills if available (Прийоми button)"""
        if not self.config.USE_SKILLS_IN_BATTLE:
            return False, False
            
        has_skills_button = False
        skills_button_pos = None
        
        for row_idx, row in enumerate(msg.buttons):
            for btn_idx, btn in enumerate(row):
                if btn.text and "Прийоми" in btn.text:
                    has_skills_button = True
                    skills_button_pos = (row_idx, btn_idx)
                    logger.info("Skills (Прийоми) button detected!")
                    break
            if has_skills_button:
                break
        
        if has_skills_button and skills_button_pos:
            try:
                await self.human_delay()
                await msg.click(skills_button_pos[0], skills_button_pos[1])
                logger.info("Clicked skills (Прийоми) button!")
                
                # Wait for skill selection message
                await asyncio.sleep(self.config.BASE_DELAY)
                skill_messages = await self.client.get_messages(self.game_chat, limit=3)
                
                for skill_msg in skill_messages:
                    if skill_msg.text and "Оберіть прийом для використання:" in skill_msg.text:
                        if skill_msg.buttons and len(skill_msg.buttons) > 0:
                            # Click the first skill option
                            await self.human_delay()
                            await skill_msg.click(0, 0)
                            logger.info("Selected first skill from the list!")
                            await asyncio.sleep(self.config.BASE_DELAY)
                            return True, True
                return True, False
            except Exception as e:
                logger.error(f"Failed to use skills: {e}")
                return False, False
        
        return False, False
    
    def extract_enemy_name(self, text):
        """Extract enemy name from battle text"""
        try:
            if "З'явився" in text:
                match = re.search(r"З'явився (.+?)!", text)
                if match:
                    return match.group(1).strip()
            elif "Раунд" in text:
                # Try to extract from round text
                match = re.search(r'[🦂🦇🐍🐺🕷️🐻🦅] (.+?) \(\d+/\d+\)', text)
                if match:
                    return match.group(1).strip()
        except Exception as e:
            logger.debug(f"Could not extract enemy name: {e}")
        return None
    
    def make_battle_decision(self, current_hp, max_hp, consecutive_escape_attempts):
        """Make intelligent battle decision based on HP and situation"""
        hp_percentage = (current_hp / max_hp) * 100
        
        # Critical HP - always try to escape
        if current_hp <= self.CRITICAL_HP_THRESHOLD:
            return 2, "escape"  # Escape action
        
        # Low HP - escape unless too many failed attempts
        if current_hp <= self.LOW_HP_THRESHOLD:
            if consecutive_escape_attempts < 3:
                return 2, "escape"
            else:
                logger.warning(f"Low HP ({current_hp}) but too many escape attempts, fighting instead")
                return 0, "attack"  # Attack action
        
        # Good HP - attack
        return 0, "attack"
    
    async def start(self):
        """Initialize bot connection and start main automation loop"""
        try:
            # Find and connect to game bot
            self.game_chat = await self.client.get_entity(self.config.GAME_BOT_USERNAME)
            logger.info(f"Found game bot: {self.game_chat.username}")
            
            # Send initial /start command
            await self.human_delay(self.config.INITIAL_START_DELAY_MIN, self.config.INITIAL_START_DELAY_MAX)
            await self.client.send_message(self.game_chat, '/start')
            await asyncio.sleep(self.config.MESSAGE_WAIT_DELAY)
            
            # Look for and click start button
            messages = await self.client.get_messages(self.game_chat, limit=3)
            for msg in messages:
                if msg.buttons:
                    await self.human_delay()
                    await msg.click(0)
                    logger.info("Clicked start button")
                    await asyncio.sleep(self.config.AFTER_BUTTON_CLICK_DELAY)
                    break
                        
            # Begin main automation loop
            self.is_running = True
            await self.main_loop()
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
    
    async def check_character_status(self):
        """Query and update character statistics from game"""
        try:
            logger.info("Checking character status...")
            await self.human_delay(self.config.CHARACTER_STATUS_DELAY_MIN, self.config.CHARACTER_STATUS_DELAY_MAX)
            await self.client.send_message(self.game_chat, "🧍 Персонаж")
            await asyncio.sleep(self.config.MESSAGE_WAIT_DELAY)
            
            messages = await self.client.get_messages(self.game_chat, limit=5)
            
            for msg in messages:
                if msg.text and "Рівень" in msg.text and "Здоров'я:" in msg.text:
                    # Parse all character information
                    level_match = re.search(r'Рівень (\d+)', msg.text)
                    if level_match:
                        self.level = int(level_match.group(1))
                    
                    hp_match = re.search(r'Здоров\'я: (\d+)/(\d+)', msg.text)
                    if hp_match:
                        self.current_hp = int(hp_match.group(1))
                        self.max_hp = int(hp_match.group(2))
                    
                    energy_match = re.search(r'Енергія: (\d+)/(\d+)', msg.text)
                    if energy_match:
                        self.current_energy = int(energy_match.group(1))
                        self.max_energy = int(energy_match.group(2))
                    
                    gold_match = re.search(r'Золото: (\d+)', msg.text)
                    if gold_match:
                        self.gold = int(gold_match.group(1))
                    
                    # Parse energy regeneration time
                    regen_match = re.search(r'(\d+)хв до відновлення енергії', msg.text)
                    if regen_match:
                        minutes = int(regen_match.group(1))
                        self.energy_regen_time = datetime.now() + timedelta(minutes=minutes)
                    
                    logger.info(f"Character status - Level: {self.level}, "
                              f"HP: {self.current_hp}/{self.max_hp}, "
                              f"Energy: {self.current_energy}/{self.max_energy}, "
                              f"Gold: {self.gold}")
                    break
            
            await asyncio.sleep(self.config.AFTER_BUTTON_CLICK_DELAY)
            
        except Exception as e:
            logger.error(f"Error checking character status: {e}")
    
    async def try_use_healing_potion(self):
        """Try to use healing potions when HP is low outside of battle"""
        if not self.config.AUTO_USE_HEALING_POTIONS:
            return False
            
        if self.current_hp > self.config.HEALING_POTION_HP_THRESHOLD:
            return False
            
        try:
            logger.info("Attempting to use healing potion...")
            
            # Go to inventory
            await self.human_delay()
            await self.client.send_message(self.game_chat, "🎒 Інвентар")
            await asyncio.sleep(self.config.MESSAGE_WAIT_DELAY)
            
            # Get inventory messages
            messages = await self.client.get_messages(self.game_chat, limit=10)
            
            # Look for healing potions
            for msg in messages:
                if msg.text and ("Зілля Здоров'я" in msg.text or "здоров'я" in msg.text.lower()) and msg.buttons:
                    # Found a healing potion, try to use it
                    await self.human_delay()
                    await msg.click(0)  # Click the potion
                    logger.info("Clicked on healing potion")
                    await asyncio.sleep(self.config.BASE_DELAY)
                    
                    # Look for "Use" button
                    use_messages = await self.client.get_messages(self.game_chat, limit=3)
                    for use_msg in use_messages:
                        if use_msg.buttons:
                            for row in use_msg.buttons:
                                for btn in row:
                                    if btn.text and ("Використати" in btn.text or "Use" in btn.text):
                                        await self.human_delay()
                                        await use_msg.click(btn.text)
                                        logger.info("Used healing potion!")
                                        await asyncio.sleep(self.config.BASE_DELAY)
                                        
                                        # Check character status after using potion
                                        await self.check_character_status()
                                        return True
            
            logger.info("No healing potions found in inventory")
            return False
            
        except Exception as e:
            logger.error(f"Error using healing potion: {e}")
            return False
    
    async def parse_energy_wait_time(self, text):
        """Extract energy regeneration wait time from game message"""
        match = re.search(r'відновиться через (\d+) хв', text)
        if match:
            minutes = int(match.group(1))
            return minutes * 60
        return 300  # Default 5 minutes
    
    async def wait_for_energy(self, wait_seconds):
        """Wait for energy regeneration with periodic status checks"""
        self.energy_regen_time = datetime.now() + timedelta(seconds=wait_seconds)
        logger.info(f"Waiting {wait_seconds} seconds for energy regeneration...")
        
        check_interval = self.config.ENERGY_STATUS_CHECK_INTERVAL
        elapsed = 0
        
        while elapsed < wait_seconds:
            wait_time = min(check_interval, wait_seconds - elapsed)
            await asyncio.sleep(wait_time)
            elapsed += wait_time
            
            if elapsed % check_interval == 0 and elapsed < wait_seconds:
                logger.info("Checking if energy was restored manually...")
                await self.check_character_status()
                
                if self.current_energy > 0:
                    logger.info(f"Energy restored! Current: {self.current_energy}/{self.max_energy}")
                    self.energy_regen_time = None
                    return
            
            remaining = wait_seconds - elapsed
            if remaining > 0 and elapsed % 60 == 0:
                logger.info(f"Still waiting {int(remaining)} seconds for energy...")
        
        await asyncio.sleep(self.config.ENERGY_REGEN_EXTRA_DELAY)
        self.current_energy = 1
        self.energy_regen_time = None
    
    async def handle_battle_simplified(self):
        """
        Handle battle with intelligent decision making and resource usage
        
        Now includes potion usage, skills, better error recovery, and outcome tracking
        """
        try:
            battle_ended = False
            rounds = 0
            final_hp = self.current_hp
            last_round_time = datetime.now()
            consecutive_escape_attempts = 0
            enemy_name = None
            battle_outcome = None
            
            logger.info(f"Battle started with HP: {self.current_hp}/{self.max_hp}")
            
            # Main battle loop
            while not battle_ended and rounds < 30:
                rounds += 1
                
                try:
                    # Maintain proper delay between actions
                    time_since_last = (datetime.now() - last_round_time).total_seconds()
                    if time_since_last < self.config.BATTLE_DELAY:
                        await asyncio.sleep(self.config.BATTLE_DELAY - time_since_last)
                    
                    # Get latest messages
                    messages = await self.client.get_messages(self.game_chat, limit=5)
                    
                    # Debug logging
                    if self.DEBUG_LOGGING and rounds == 1:
                        logger.debug("=== Battle messages ===")
                        for i, msg in enumerate(messages[:3]):
                            if msg.text:
                                logger.debug(f"Battle msg {i}: {msg.text[:80]}...")
                    
                    clicked_this_round = False
                    
                    for msg in messages:
                        if not msg.text:
                            continue
                        
                        # Extract enemy name for tracking
                        if not enemy_name:
                            enemy_name = self.extract_enemy_name(msg.text)
                        
                        # Check if battle ended - Victory
                        if "Ви отримали:" in msg.text:
                            battle_ended = True
                            battle_outcome = "win"
                            rewards = self.parser.parse_battle_rewards(msg.text)
                            if rewards:
                                if 'gold' in rewards:
                                    self.gold += rewards['gold']
                                logger.info(f"Battle won! Rewards: {rewards}")
                            
                            # Get final HP
                            hp_match = re.search(r'👤 Ви \((\d+)/(\d+)\)', msg.text)
                            if hp_match:
                                final_hp = int(hp_match.group(1))
                            break
                        
                        # Check for battle end - Defeat
                        elif "Ви зазнали поразки!" in msg.text:
                            battle_ended = True
                            battle_outcome = "loss"
                            logger.warning("Battle lost!")
                            final_hp = 1
                            break
                        
                        # Check for enemy flee
                        elif "занудьгував і втік" in msg.text:
                            battle_ended = True
                            battle_outcome = "win"  # Enemy fled counts as win
                            logger.info("Enemy fled!")
                            break
                        
                        # Check for escape results
                        elif "❌ Втеча не вдалася!" in msg.text:
                            logger.warning("Escape failed! Enemy attacked!")
                            damage_match = re.search(r'завдав (\d+) шкоди', msg.text)
                            if damage_match:
                                damage = int(damage_match.group(1))
                                final_hp = max(1, final_hp - damage)
                                logger.info(f"Took {damage} damage from failed escape. HP: {final_hp}")
                        
                        elif "🏃 Вам вдалося втекти!" in msg.text:
                            battle_ended = True
                            battle_outcome = "escape"
                            logger.info("Successfully escaped from battle!")
                            break
                        
                        # Process battle messages with buttons
                        elif msg.buttons and not clicked_this_round:
                            # Check if this is a battle message (has attack/defend/escape buttons)
                            has_battle_buttons = False
                            
                            for row_idx, row in enumerate(msg.buttons):
                                for btn_idx, btn in enumerate(row):
                                    if btn.text and "Атака" in btn.text:
                                        has_battle_buttons = True
                                        break
                                if has_battle_buttons:
                                    break
                            
                            if has_battle_buttons:
                                # Extract current HP if available
                                if "Раунд" in msg.text:
                                    hp_match = re.search(r'👤 Ви \((\d+)/(\d+)\)', msg.text)
                                    if hp_match:
                                        final_hp = int(hp_match.group(1))
                                        self.max_hp = int(hp_match.group(2))
                                        logger.debug(f"Round {rounds}: HP {final_hp}/{self.max_hp}")
                                
                                # Priority 1: Check for and use potions (healing priority) - only if HP is low
                                potion_available, potion_used = await self.check_for_potions(msg, final_hp)
                                if potion_used:
                                    clicked_this_round = True
                                    last_round_time = datetime.now()
                                    logger.info(f"Used potion this round (HP was {final_hp})")
                                    break
                                
                                # Priority 2: Check for and use skills (if no potions used)
                                if not clicked_this_round:
                                    skill_available, skill_used = await self.check_for_skills(msg)
                                    if skill_used:
                                        clicked_this_round = True
                                        last_round_time = datetime.now()
                                        logger.info("Used skill this round")
                                        break
                                
                                # Priority 3: Normal combat if no special actions
                                if not clicked_this_round:
                                    action_index, action_name = self.make_battle_decision(
                                        final_hp, self.max_hp, consecutive_escape_attempts
                                    )
                                    
                                    if action_name == "escape":
                                        consecutive_escape_attempts += 1
                                    else:
                                        consecutive_escape_attempts = 0
                                    
                                    # Click the action button
                                    try:
                                        await self.human_delay()
                                        
                                        # For initial battle message, always use first row
                                        if "З'явився" in msg.text:
                                            await msg.click(0, action_index)
                                        else:
                                            await msg.click(action_index)
                                        
                                        logger.info(f"Clicked {action_name} in round {rounds} (HP: {final_hp}/{self.max_hp})")
                                        clicked_this_round = True
                                        last_round_time = datetime.now()
                                    except Exception as e:
                                        await self.handle_error_recovery(e, f"battle action {action_name}")
                                        continue
                                break
                    
                    # If no action taken this round, wait a bit
                    if not clicked_this_round and not battle_ended:
                        await asyncio.sleep(self.config.NO_ACTION_DELAY)
                        
                except Exception as e:
                    await self.handle_error_recovery(e, f"battle round {rounds}")
                    continue
            
            # Track battle outcome
            if battle_outcome:
                self.track_battle_outcome(battle_outcome, enemy_name)
            
            # Reset error counter after successful battle
            self.reset_error_counter()
            
            logger.info(f"Battle ended after {rounds} rounds. Final HP: {final_hp}/{self.max_hp}")
            return final_hp
            
        except Exception as e:
            logger.error(f"Critical error in battle: {e}")
            await self.handle_error_recovery(e, "battle handling")
            return max(1, self.current_hp - 10)  # Assume some damage if battle failed
    
    async def main_loop(self):
        """
        Main game automation loop
        
        Handles all game states and interactions
        """
        consecutive_failures = 0
        
        while self.is_running:
            try:
                # Check if waiting for energy
                if self.energy_regen_time and datetime.now() < self.energy_regen_time:
                    wait_time = (self.energy_regen_time - datetime.now()).total_seconds()
                    if wait_time > 0:
                        await self.check_character_status()
                        if self.current_energy > 0:
                            logger.info(f"Energy already restored! Current: {self.current_energy}/{self.max_energy}")
                            self.energy_regen_time = None
                            if self.pending_camp_visit:
                                logger.info("Energy restored, checking for camp (табір) option...")
                        else:
                            logger.info(f"Still waiting {int(wait_time)} seconds for energy...")
                            await asyncio.sleep(min(wait_time + 5, self.config.ENERGY_WAIT_MAX_CHECK_INTERVAL))
                        continue
                
                # Check HP levels
                hp_percentage = (self.current_hp / self.max_hp) * 100
                if hp_percentage < self.config.MIN_HEALTH_PERCENT_TO_EXPLORE:
                    logger.info(f"Low HP: {self.current_hp}/{self.max_hp} ({hp_percentage:.1f}%)")
                    
                    # Try to use healing potion first
                    if self.current_hp <= self.config.HEALING_POTION_HP_THRESHOLD:
                        potion_used = await self.try_use_healing_potion()
                        if potion_used:
                            hp_percentage = (self.current_hp / self.max_hp) * 100
                            logger.info(f"HP after potion: {self.current_hp}/{self.max_hp} ({hp_percentage:.1f}%)")
                            
                            # If HP is now good enough, continue exploring
                            if hp_percentage >= self.config.MIN_HEALTH_PERCENT_TO_EXPLORE:
                                continue
                    
                    # If no potion used or still low HP, wait for natural regeneration
                    logger.info("Waiting for HP regeneration...")
                    hp_needed = (self.max_hp * (self.config.MIN_HEALTH_PERCENT_TO_EXPLORE / 100)) - self.current_hp
                    wait_minutes = max(1, int(hp_needed / self.config.HP_REGEN_RATE_PER_MINUTE))
                    
                    check_interval_minutes = self.config.HP_STATUS_CHECK_INTERVAL / 60
                    elapsed_minutes = 0
                    
                    while elapsed_minutes < wait_minutes:
                        wait_time_minutes = min(check_interval_minutes, wait_minutes - elapsed_minutes)
                        await asyncio.sleep(wait_time_minutes * 60)
                        elapsed_minutes += wait_time_minutes
                        
                        await self.check_character_status()
                        hp_percentage = (self.current_hp / self.max_hp) * 100
                        
                        if hp_percentage >= self.config.MIN_HEALTH_PERCENT_TO_EXPLORE:
                            logger.info(f"HP restored to {self.current_hp}/{self.max_hp} ({hp_percentage:.1f}%)!")
                            break
                    
                    continue
                
                # Ensure we have energy
                if self.current_energy < 1:
                    logger.info("Energy might have regenerated, checking...")
                    self.current_energy = 1
                
                # Try to explore
                logger.info(f"Exploring... (HP: {self.current_hp}/{self.max_hp}, Energy: {self.current_energy}/{self.max_energy})")
                if self.DEBUG_LOGGING:
                    logger.debug(f"Pending camp visit: {self.pending_camp_visit}")
                await self.human_delay(self.config.EXPLORE_DELAY_MIN, self.config.EXPLORE_DELAY_MAX)
                await self.client.send_message(self.game_chat, "🗺️ Досліджувати (⚡1)")
                
                # Wait for response
                await asyncio.sleep(self.config.MESSAGE_WAIT_DELAY)
                
                # Get latest messages
                messages = await self.client.get_messages(self.game_chat, limit=10)
                
                # First check for critical messages that should stop exploration
                in_battle = False
                battle_started = False
                low_health_detected = False
                no_energy_detected = False
                battle_event_detected = False
                greeting_detected = False
                
                for msg in messages:
                    if msg.text:
                        # Check for explicit battle states
                        if "Ви в бою!" in msg.text:
                            logger.warning("Already in battle! Cannot explore.")
                            in_battle = True
                            break
                        elif "З'явився" in msg.text:
                            logger.info("Battle starting detected!")
                            battle_started = True
                            break
                        elif msg.buttons and any("Атака" in btn.text for row in msg.buttons for btn in row):
                            logger.info("Battle buttons detected!")
                            battle_started = True
                            break
                        # Check for battle events (like abandoned camps during exploration)
                        elif ("натрапили" in msg.text or "знайшли" in msg.text or "покинутий табір" in msg.text) and msg.buttons:
                            # This is a battle/exploration event that needs immediate handling
                            logger.info("Battle/exploration event detected - handling immediately")
                            battle_event_detected = True
                            break
                        # Check for greeting opportunities
                        elif "бачите" in msg.text and "подорожує" in msg.text and msg.buttons:
                            logger.info("Greeting opportunity detected - handling immediately")
                            greeting_detected = True
                            break
                        elif "замало здоров'я" in msg.text:
                            logger.info("Not enough health to explore - detected early")
                            self.current_hp = int(self.max_hp * 0.15)
                            low_health_detected = True
                            break
                        elif "Недостатньо енергії" in msg.text:
                            logger.info("Out of energy - detected early")
                            self.current_energy = 0
                            self.pending_camp_visit = True
                            no_energy_detected = True
                            break
                
                # Handle battle start immediately if detected
                if in_battle or battle_started:
                    logger.info("Starting battle handling...")
                    await self.handle_battle_simplified()
                    consecutive_failures = 0
                    continue
                
                # Handle battle events immediately (like abandoned camps)
                if battle_event_detected:
                    for msg in messages:
                        if msg.text and msg.buttons and ("натрапили" in msg.text or "знайшли" in msg.text or "покинутий табір" in msg.text):
                            logger.info(f"Handling battle event: {msg.text[:100]}...")
                            # Click the first button (usually "Дослідити" or similar)
                            if msg.buttons and len(msg.buttons) > 0 and len(msg.buttons[0]) > 0:
                                await self.human_delay()
                                await msg.click(0, 0)
                                logger.info("Clicked first button on battle event")
                                await asyncio.sleep(self.config.BASE_DELAY)
                                
                                # After clicking, check if a battle starts
                                new_messages = await self.client.get_messages(self.game_chat, limit=5)
                                for new_msg in new_messages:
                                    if new_msg.text and ("З'явився" in new_msg.text or (new_msg.buttons and any("Атака" in btn.text for row in new_msg.buttons for btn in row))):
                                        logger.info("Battle started from event! Entering battle mode...")
                                        await self.handle_battle_simplified()
                                        break
                                
                                consecutive_failures = 0
                                self.reset_error_counter()
                                break
                    continue
                
                # Handle greeting opportunities immediately
                if greeting_detected:
                    for msg in messages:
                        if msg.text and msg.buttons and "бачите" in msg.text and "подорожує" in msg.text:
                            logger.info(f"Handling greeting: {msg.text[:50]}...")
                            # Find and click the greeting button
                            for row_idx, row in enumerate(msg.buttons):
                                for btn_idx, btn in enumerate(row):
                                    if btn.text and "привітати" in btn.text.lower():
                                        await self.human_delay()
                                        await msg.click(row_idx, btn_idx)
                                        logger.info("Clicked greeting button!")
                                        await asyncio.sleep(self.config.GREETING_CLICK_DELAY)
                                        consecutive_failures = 0
                                        self.reset_error_counter()
                                        break
                                break
                            break
                    continue
                
                # Only look for regular exploration opportunities if NOT in battle and no critical issues
                exploration_opportunity_found = False
                if not in_battle and not battle_started and not low_health_detected and not no_energy_detected and not battle_event_detected:
                    for msg in messages:
                        if msg.text and msg.buttons:
                            # Look for exploration buttons in messages with buttons
                            for row_idx, row in enumerate(msg.buttons):
                                for btn_idx, btn in enumerate(row):
                                    if btn.text and ("дослідити" in btn.text.lower() or "досліджувати" in btn.text.lower()):
                                        # Make sure this isn't a battle message
                                        if not any("атака" in b.text.lower() for r in msg.buttons for b in r):
                                            logger.info(f"Found clickable exploration opportunity: {btn.text}")
                                            await self.human_delay()
                                            await msg.click(row_idx, btn_idx)
                                            logger.info(f"Clicked exploration button: {btn.text}")
                                            self.current_energy = max(0, self.current_energy - 1)
                                            consecutive_failures = 0
                                            self.reset_error_counter()
                                            await asyncio.sleep(self.config.CAMP_CLICK_DELAY)
                                            exploration_opportunity_found = True
                                            break
                                if exploration_opportunity_found:
                                    break
                            if exploration_opportunity_found:
                                break
                        
                        # Also check if there's a "Дослідити (1⚡)" message that's clickable (not in battle)
                        elif msg.text and "дослідити" in msg.text.lower() and "⚡" in msg.text and "з'явився" not in msg.text.lower():
                            logger.info(f"Found exploration message that might be clickable: {msg.text}")
                            try:
                                await self.human_delay()
                                await msg.click()
                                logger.info("Clicked on exploration message!")
                                self.current_energy = max(0, self.current_energy - 1)
                                consecutive_failures = 0
                                self.reset_error_counter()
                                await asyncio.sleep(self.config.CAMP_CLICK_DELAY)
                                exploration_opportunity_found = True
                                break
                            except Exception as e:
                                logger.debug(f"Could not click exploration message: {e}")
                
                # If we found and clicked an exploration opportunity, skip to next iteration
                if exploration_opportunity_found:
                    continue
                
                # Handle low health detection
                if low_health_detected:
                    logger.warning(f"Game reported low health! Current HP estimate: {self.current_hp}/{self.max_hp}")
                    # Try to use healing potion first
                    if self.current_hp <= self.config.HEALING_POTION_HP_THRESHOLD:
                        potion_used = await self.try_use_healing_potion()
                        if potion_used:
                            logger.info("Used healing potion due to low health warning")
                            # Check character status after using potion
                            await self.check_character_status()
                        else:
                            logger.info("No healing potions available, will wait for HP regeneration")
                    consecutive_failures = 0
                    continue
                
                # Handle no energy detection
                if no_energy_detected:
                    logger.info("Game reported no energy!")
                    # Parse wait time and start energy waiting
                    for msg in messages:
                        if msg.text and "Недостатньо енергії" in msg.text:
                            energy_wait_time = await self.parse_energy_wait_time(msg.text)
                            logger.info(f"Starting energy wait for {energy_wait_time} seconds")
                            await self.wait_for_energy(energy_wait_time)
                            break
                    consecutive_failures = 0
                    continue
                
                # Handle battle if detected
                if in_battle or battle_started:
                    # Handle the existing battle
                    logger.info("Handling ongoing battle...")
                    final_hp = await self.handle_battle_simplified()
                    self.current_hp = final_hp
                    self.current_energy = max(0, self.current_energy - 1)
                    consecutive_failures = 0
                    await asyncio.sleep(self.config.AFTER_BATTLE_DELAY)
                    continue
                
                # Process exploration results
                battle_started = False
                energy_wait_time = 0
                exploration_successful = False
                
                for msg in messages:
                    if not msg.text:
                        continue
                    
                    # Check for camp (табір) FIRST - including abandoned camps
                    if "табір" in msg.text.lower() or "Табір" in msg.text or "покинутий табір" in msg.text:
                        logger.info("Camp (табір) or abandoned camp option detected!")
                        if msg.buttons:
                            camp_clicked = False
                            for i, row in enumerate(msg.buttons):
                                for j, button in enumerate(row):
                                    if button.text and ("табір" in button.text.lower() or "дослідити" in button.text.lower()):
                                        await self.human_delay()
                                        await msg.click(i, j)
                                        logger.info(f"Clicked camp/explore button: {button.text}")
                                        camp_clicked = True
                                        self.pending_camp_visit = False
                                        await asyncio.sleep(self.config.CAMP_CLICK_DELAY)
                                        break
                                if camp_clicked:
                                    break
                            if camp_clicked:
                                exploration_successful = True
                                break
                        # If there are no buttons but it's an abandoned camp message, treat as successful exploration
                        elif "покинутий табір" in msg.text:
                            logger.info("Found abandoned camp text without buttons - treating as exploration result")
                            exploration_successful = True
                            self.current_energy = max(0, self.current_energy - 1)
                            break
                    
                    # Check for player greeting opportunities
                    elif "Ви бачите" in msg.text and "подорожує" in msg.text:
                        player_name = "someone"
                        try:
                            if ", який подорожує" in msg.text:
                                player_name = msg.text.split("Ви бачите ")[1].split(", який подорожує")[0]
                        except:
                            pass
                        
                        logger.info(f"Found player to greet: {player_name}")
                        
                        if msg.buttons and len(msg.buttons) > 0:
                            try:
                                await self.human_delay()
                                await msg.click(0)
                                logger.info(f"Clicked greeting button for player: {player_name}")
                                exploration_successful = True
                                self.current_energy = max(0, self.current_energy - 1)
                                await asyncio.sleep(self.config.GREETING_CLICK_DELAY)
                                break
                            except Exception as e:
                                if self.DEBUG_LOGGING:
                                    logger.debug(f"Failed to click greeting button: {e}")
                    
                    # Check if battle started
                    elif "З'явився" in msg.text:
                        battle_started = True
                        exploration_successful = True
                        
                        # Parse initial HP
                        if "Ваші характеристики:" in msg.text:
                            hp_match = re.search(r'Здоров\'я: (\d+)/(\d+)', msg.text.split('Ваші характеристики:')[1])
                            if hp_match:
                                self.current_hp = int(hp_match.group(1))
                                self.max_hp = int(hp_match.group(2))
                                logger.info(f"Battle started! Current HP: {self.current_hp}/{self.max_hp}")
                        
                        # If battle start has buttons, click attack immediately
                        if msg.buttons and len(msg.buttons) > 0:
                            has_battle_buttons = False
                            for row in msg.buttons:
                                for btn in row:
                                    if btn.text and "Атака" in btn.text:
                                        has_battle_buttons = True
                                        break
                            
                            if has_battle_buttons:
                                logger.info("Battle start has buttons - starting battle immediately")
                                # Don't click here, let handle_battle_simplified do it
                        break
                    
                    # Check for no energy
                    elif "Недостатньо енергії" in msg.text:
                        logger.info("Out of energy")
                        self.current_energy = 0
                        self.pending_camp_visit = True
                        energy_wait_time = await self.parse_energy_wait_time(msg.text)
                        break
                    
                    # Check for low health
                    elif "замало здоров'я" in msg.text:
                        logger.info("Not enough health to explore")
                        self.current_hp = int(self.max_hp * 0.15)
                        break
                    
                    # Greeting result
                    elif "Ви привітали" in msg.text:
                        logger.info(f"Successfully greeted player: {msg.text[:80]}...")
                        exploration_successful = True
                        break
                    
                    # Check for exploration opportunities with buttons (like abandoned camps)
                    elif msg.buttons and ("натрапили" in msg.text or "покинутий" in msg.text or "знайшли" in msg.text):
                        logger.info(f"Exploration opportunity with buttons detected: {msg.text[:80]}...")
                        opportunity_clicked = False
                        for i, row in enumerate(msg.buttons):
                            for j, button in enumerate(row):
                                if button.text and ("дослідити" in button.text.lower() or "досліджувати" in button.text.lower()):
                                    await self.human_delay()
                                    await msg.click(i, j)
                                    logger.info(f"Clicked exploration opportunity: {button.text}")
                                    opportunity_clicked = True
                                    await asyncio.sleep(self.config.CAMP_CLICK_DELAY)
                                    break
                            if opportunity_clicked:
                                break
                        if opportunity_clicked:
                            exploration_successful = True
                            self.current_energy = max(0, self.current_energy - 1)
                            break
                    
                    # Other exploration results (text only)
                    elif any(phrase in msg.text for phrase in ["Ви помітили", "Ви натрапили", 
                                                               "Ви відкрили", "Ви виявили", "Ви чуєте",
                                                               "Ви знайшли", "знайшли"]):
                        logger.info(f"Exploration result: {msg.text[:80]}...")
                        exploration_successful = True
                        self.current_energy = max(0, self.current_energy - 1)
                        
                        if "+2 ⚡ енергія" in msg.text:
                            self.current_energy = min(self.max_energy, self.current_energy + 2)
                            logger.info(f"Gained 2 energy! Current: {self.current_energy}/{self.max_energy}")
                        break
                    
                    # Bee sting
                    elif "вас боляче вжалив джміль" in msg.text:
                        damage_match = re.search(r'\(-(\d+) ❤️', msg.text)
                        if damage_match:
                            damage = int(damage_match.group(1))
                            self.current_hp = max(1, self.current_hp - damage)
                            logger.info(f"Bee sting! Lost {damage} HP. Current: {self.current_hp}/{self.max_hp}")
                        exploration_successful = True
                        self.current_energy = max(0, self.current_energy - 1)
                        break
                
                # Handle results
                if battle_started:
                    final_hp = await self.handle_battle_simplified()
                    self.current_hp = final_hp
                    self.current_energy = max(0, self.current_energy - 1)
                    consecutive_failures = 0
                elif energy_wait_time > 0:
                    if self.DEBUG_LOGGING:
                        logger.debug(f"Starting energy wait for {energy_wait_time} seconds")
                    await self.wait_for_energy(energy_wait_time)
                    consecutive_failures = 0
                elif exploration_successful:
                    consecutive_failures = 0
                    self.reset_error_counter()  # Reset error counter on successful exploration
                else:
                    consecutive_failures += 1
                    if self.DEBUG_LOGGING:
                        logger.debug(f"No clear result from exploration (failure #{consecutive_failures})")
                    if consecutive_failures > 3:
                        logger.warning("Multiple failures, checking character status...")
                        await self.check_character_status()
                        consecutive_failures = 0
                
                # Small delay before next iteration
                await asyncio.sleep(self.config.MAIN_LOOP_DELAY)
                
            except Exception as e:
                consecutive_failures += 1
                await self.handle_error_recovery(e, "main loop")
                
                if consecutive_failures > 5:
                    logger.error("Too many consecutive main loop errors, checking status...")
                    try:
                        await self.check_character_status()
                        consecutive_failures = 0
                    except Exception as status_error:
                        logger.error(f"Failed to check character status: {status_error}")
                        # Take a longer break if we can't even check status
                        await asyncio.sleep(self.config.ERROR_RETRY_DELAY * 3)
    
    async def stop(self):
        """Gracefully stop the bot"""
        self.is_running = False
        logger.info("Bot stopped")
