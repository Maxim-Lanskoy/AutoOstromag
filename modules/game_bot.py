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
        self.LOW_HP_THRESHOLD = 10
        self.CRITICAL_HP_THRESHOLD = 5
        
        # Debug logging flag
        self.DEBUG_LOGGING = getattr(config, 'VERBOSE_LOGGING', True)
    
    def set_debug_logging(self, enabled: bool):
        """Enable or disable verbose debug logging"""
        self.DEBUG_LOGGING = enabled
        logger.info(f"Debug logging {'enabled' if enabled else 'disabled'}")
        
    async def human_delay(self, min_seconds=0.5, max_seconds=2.0):
        """Simulate human-like reaction time with randomized delays"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def start(self):
        """Initialize bot connection and start main automation loop"""
        try:
            # Find and connect to game bot
            self.game_chat = await self.client.get_entity(self.config.GAME_BOT_USERNAME)
            logger.info(f"Found game bot: {self.game_chat.username}")
            
            # Send initial /start command
            await self.human_delay(1, 3)
            await self.client.send_message(self.game_chat, '/start')
            await asyncio.sleep(2)
            
            # Look for and click start button
            messages = await self.client.get_messages(self.game_chat, limit=3)
            for msg in messages:
                if msg.buttons:
                    await self.human_delay()
                    await msg.click(0)
                    logger.info("Clicked start button")
                    await asyncio.sleep(1)
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
            await self.human_delay(0.5, 1.5)
            await self.client.send_message(self.game_chat, "🧍 Персонаж")
            await asyncio.sleep(2)
            
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
            
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Error checking character status: {e}")
    
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
        
        await asyncio.sleep(5)
        self.current_energy = 1
        self.energy_regen_time = None
    
    async def handle_battle_simplified(self):
        """
        Handle battle with intelligent HP-based decision making
        
        Properly handles both initial battle messages and round messages
        """
        try:
            battle_ended = False
            rounds = 0
            final_hp = self.current_hp
            last_round_time = datetime.now()
            consecutive_escape_attempts = 0
            
            logger.info(f"Battle started with HP: {self.current_hp}/{self.max_hp}")
            
            # Main battle loop
            while not battle_ended and rounds < 30:
                rounds += 1
                
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
                    
                    # Check if battle ended - Victory
                    if "Ви отримали:" in msg.text:
                        battle_ended = True
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
                        logger.warning("Battle lost!")
                        final_hp = 1
                        break
                    
                    # Check for enemy flee
                    elif "занудьгував і втік" in msg.text:
                        battle_ended = True
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
                        logger.info("Successfully escaped from battle!")
                        break
                    
                    # Process battle messages with buttons
                    elif msg.buttons and not clicked_this_round:
                        # Check if this is a battle message (has attack/defend/escape buttons)
                        has_battle_buttons = False
                        attack_button_idx = 0
                        
                        for row_idx, row in enumerate(msg.buttons):
                            for btn_idx, btn in enumerate(row):
                                if btn.text and "Атака" in btn.text:
                                    has_battle_buttons = True
                                    attack_button_idx = (row_idx, btn_idx)
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
                            
                            # Make decision based on HP
                            action_index = 0  # Default: attack
                            action_name = "attack"
                            
                            # HP-based decision logic
                            if final_hp < self.CRITICAL_HP_THRESHOLD:
                                action_index = 2  # Escape
                                action_name = "escape"
                                consecutive_escape_attempts += 1
                            elif final_hp < self.LOW_HP_THRESHOLD:
                                if consecutive_escape_attempts < 3:
                                    action_index = 2  # Escape
                                    action_name = "escape"
                                    consecutive_escape_attempts += 1
                                else:
                                    logger.warning(f"Low HP ({final_hp}) but too many escape attempts, fighting instead")
                                    consecutive_escape_attempts = 0
                            else:
                                consecutive_escape_attempts = 0
                            
                            # Click the action button
                            try:
                                if action_name == "escape":
                                    await self.human_delay(1.5, 3.0)
                                    logger.info(f"Attempting to escape! HP: {final_hp}/{self.max_hp}")
                                else:
                                    await self.human_delay(1.0, 2.5)
                                
                                # For initial battle message, always use first row
                                if "З'явився" in msg.text:
                                    await msg.click(0, action_index)
                                else:
                                    await msg.click(action_index)
                                
                                logger.info(f"Clicked {action_name} in round {rounds}")
                                clicked_this_round = True
                                last_round_time = datetime.now()
                            except Exception as e:
                                logger.error(f"Failed to click battle button: {e}")
                            break
                
                # If no action taken this round, wait a bit
                if not clicked_this_round and not battle_ended:
                    await asyncio.sleep(1)
            
            logger.info(f"Battle ended after {rounds} rounds. Final HP: {final_hp}/{self.max_hp}")
            return final_hp
            
        except Exception as e:
            logger.error(f"Error in battle: {e}")
            return self.current_hp
    
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
                            await asyncio.sleep(min(wait_time + 5, 60))
                        continue
                
                # Check HP levels
                hp_percentage = (self.current_hp / self.max_hp) * 100
                if hp_percentage < self.config.MIN_HEALTH_PERCENT_TO_EXPLORE:
                    logger.info(f"Low HP: {self.current_hp}/{self.max_hp} ({hp_percentage:.1f}%). Waiting for regeneration...")
                    hp_needed = (self.max_hp * (self.config.MIN_HEALTH_PERCENT_TO_EXPLORE / 100)) - self.current_hp
                    wait_minutes = max(1, int(hp_needed / 0.6))
                    
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
                await self.human_delay(0.5, 1.5)
                await self.client.send_message(self.game_chat, "🗺️ Досліджувати (⚡1)")
                
                # Wait for response
                await asyncio.sleep(2)
                
                # Get latest messages
                messages = await self.client.get_messages(self.game_chat, limit=10)
                
                # First check if we're already in battle
                in_battle = False
                for msg in messages:
                    if msg.text and "Ви в бою!" in msg.text:
                        logger.warning("Already in battle! Cannot explore.")
                        in_battle = True
                        break
                
                if in_battle:
                    # Handle the existing battle
                    logger.info("Handling ongoing battle...")
                    final_hp = await self.handle_battle_simplified()
                    self.current_hp = final_hp
                    self.current_energy = max(0, self.current_energy - 1)
                    consecutive_failures = 0
                    await asyncio.sleep(3)
                    continue
                
                # Process exploration results
                battle_started = False
                energy_wait_time = 0
                exploration_successful = False
                
                for msg in messages:
                    if not msg.text:
                        continue
                    
                    # Check for camp (табір) FIRST
                    if "табір" in msg.text.lower() or "Табір" in msg.text:
                        logger.info("Camp (табір) option detected!")
                        if msg.buttons:
                            camp_clicked = False
                            for i, row in enumerate(msg.buttons):
                                for j, button in enumerate(row):
                                    if button.text and "табір" in button.text.lower():
                                        await self.human_delay()
                                        await msg.click(i, j)
                                        logger.info(f"Clicked camp (табір) button: {button.text}")
                                        camp_clicked = True
                                        self.pending_camp_visit = False
                                        await asyncio.sleep(2)
                                        break
                                if camp_clicked:
                                    break
                            if camp_clicked:
                                exploration_successful = True
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
                                await asyncio.sleep(1)
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
                    
                    # Other exploration results
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
                else:
                    consecutive_failures += 1
                    if self.DEBUG_LOGGING:
                        logger.debug(f"No clear result from exploration (failure #{consecutive_failures})")
                    if consecutive_failures > 3:
                        logger.warning("Multiple failures, checking character status...")
                        await self.check_character_status()
                        consecutive_failures = 0
                
                # Small delay before next iteration
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                if self.DEBUG_LOGGING:
                    import traceback
                    logger.debug(f"Full traceback: {traceback.format_exc()}")
                await asyncio.sleep(10)
                consecutive_failures += 1
                
                if consecutive_failures > 5:
                    logger.error("Too many consecutive errors, checking status...")
                    await self.check_character_status()
                    consecutive_failures = 0
    
    async def stop(self):
        """Gracefully stop the bot"""
        self.is_running = False
        logger.info("Bot stopped")
