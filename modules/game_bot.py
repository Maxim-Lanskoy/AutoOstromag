"""
Simplified Game Bot for Ostromag - Auto-leveling bot
Main flow:
1. Send /start command
2. Check player profile once  
3. Start exploring if HP is full and energy > 0
4. In battle: use skills and potions (if HP < 100)
5. After battle: check profile and wait for regeneration
"""

import asyncio
import re
from datetime import datetime, timedelta
from telethon import events, Button
from telethon.tl.custom import Message

from utils.logger import setup_logger
from utils.parser import GameParser
from utils.energy_tracker import EnergyTracker

logger = setup_logger(__name__)


class GameBot:
    """
    Simplified game bot controller for auto-leveling
    """
    
    def __init__(self, client, config):
        """Initialize bot with client and configuration"""
        self.client = client
        self.config = config
        self.parser = GameParser()
        
        # Bot state
        self.game_chat = None
        self.is_running = False
        
        # Character stats (updated from profile checks)
        self.current_hp = 0
        self.max_hp = 1
        self.current_energy = 0
        self.max_energy = 1
        self.level = 1
        self.gold = 0
        
        # Regeneration times from game
        self.hp_regen_minutes = None
        self.energy_regen_minutes = None
        
        # Energy tracker for daily limits and time windows
        self.energy_tracker = EnergyTracker(config.DAILY_ENERGY_LIMIT, config.EXPLORATION_START_HOUR)
    
    async def human_delay(self, min_seconds=None, max_seconds=None):
        """Simulate human-like reaction time"""
        import random
        if min_seconds is None:
            min_seconds = self.config.HUMAN_DELAY_MIN
        if max_seconds is None:
            max_seconds = self.config.HUMAN_DELAY_MAX
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def start(self):
        """Initialize bot and start main loop"""
        try:
            logger.info("=== BOT STARTING ===")
            
            # Connect to game bot
            self.game_chat = await self.client.get_entity(self.config.GAME_BOT_USERNAME)
            logger.info(f"Connected to game bot: {self.game_chat.username}")
            
            # Send /start to refresh menu
            await self.human_delay(2, 4)
            await self.client.send_message(self.game_chat, '/start')
            await asyncio.sleep(3)
            
            # Start main loop (it will handle profile check and HP wait)
            self.is_running = True
            await self.main_loop()
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
    
    async def check_character_status(self, retry_count=0):
        """Check character profile and update stats with retry mechanism"""
        max_retries = 3
        
        try:
            logger.info(f"Checking character status... (attempt {retry_count + 1})")
            await self.human_delay()
            await self.client.send_message(self.game_chat, "🧍 Персонаж")
            await asyncio.sleep(3)
            
            messages = await self.client.get_messages(self.game_chat, limit=2)
            
            # Check for "don't rush" message indicating we need to wait
            for msg in messages:
                if msg.text and ("Будь ласка, не поспішайте" in msg.text or "не поспішайте" in msg.text):
                    logger.warning("Game says 'don't rush' - profile check failed")
                    if retry_count < max_retries:
                        logger.info(f"Retrying character status check in 60 seconds... (attempt {retry_count + 2}/{max_retries + 1})")
                        await asyncio.sleep(60)  # Wait 1 minute before retry
                        return await self.check_character_status(retry_count + 1)
                    else:
                        logger.error("Max retries reached for character status check")
                        raise Exception("Failed to get character status after multiple attempts")
            
            # Look for actual character profile
            profile_found = False
            for msg in messages:
                if msg.text and "Рівень" in msg.text and "Здоров'я:" in msg.text:
                    profile_found = True
                    # ✨ Parse level
                    level_match = re.search(r'Рівень (\d+)', msg.text)
                    if level_match:
                        self.level = int(level_match.group(1))
                    
                    # ❤️ Parse HP
                    hp_match = re.search(r'Здоров\'я: (\d+)/(\d+)', msg.text)
                    if hp_match:
                        self.current_hp = int(hp_match.group(1))
                        self.max_hp = int(hp_match.group(2))
                    
                    # ⚡ Parse energy
                    energy_match = re.search(r'Енергія: (\d+)/(\d+)', msg.text)
                    if energy_match:
                        self.current_energy = int(energy_match.group(1))
                        self.max_energy = int(energy_match.group(2))
                    
                    # 💰 Parse gold
                    gold_match = re.search(r'Золото: (\d+)', msg.text)
                    if gold_match:
                        self.gold = int(gold_match.group(1))
                    
                    # ❤️ Parse HP regeneration time
                    hp_regen_match = re.search(r'(\d+)хв до повного відновлення здоров\'я', msg.text)
                    if hp_regen_match:
                        self.hp_regen_minutes = int(hp_regen_match.group(1))
                        logger.info(f"HP will be full in {self.hp_regen_minutes} minutes")
                    else:
                        self.hp_regen_minutes = None
                    
                    # ⚡ Parse energy regeneration time
                    energy_regen_match = re.search(r'(\d+)хв до відновлення енергії', msg.text)
                    if energy_regen_match:
                        self.energy_regen_minutes = int(energy_regen_match.group(1))
                        logger.info(f"New energy will be restored in {self.energy_regen_minutes} minutes")
                    else:
                        self.energy_regen_minutes = None
                    
                    logger.info(f"Status - Level: {self.level}, HP: {self.current_hp}/{self.max_hp}, "
                              f"Energy: {self.current_energy}/{self.max_energy}, Gold: {self.gold}")
                    break
            
            # If no profile found, retry
            if not profile_found:
                logger.warning("Character profile not found in messages")
                if retry_count < max_retries:
                    logger.info(f"Retrying character status check in 30 seconds... (attempt {retry_count + 2}/{max_retries + 1})")
                    await asyncio.sleep(30)
                    return await self.check_character_status(retry_count + 1)
                else:
                    logger.error("Max retries reached - could not get character profile")
                    raise Exception("Failed to get character profile after multiple attempts")
            
        except Exception as e:
            if retry_count < max_retries:
                logger.warning(f"Error checking character status: {e}. Retrying in 30 seconds...")
                await asyncio.sleep(30)
                return await self.check_character_status(retry_count + 1)
            else:
                logger.error(f"Error checking character status after {max_retries + 1} attempts: {e}")
                raise
    
    async def wait_for_full_hp(self):
        """Wait for HP to fully regenerate with manual healing detection"""
        if self.hp_regen_minutes:
            wait_seconds = ((self.hp_regen_minutes - 1) * 60) + 30  # Add 30s buffer
            logger.info(f"Waiting {self.hp_regen_minutes} minutes for full HP...")
            
            # Check for manual healing every 30 seconds
            check_interval = 30
            elapsed = 0
            
            while elapsed < wait_seconds:
                # Calculate time to wait this iteration
                time_to_wait = min(check_interval, wait_seconds - elapsed)
                if time_to_wait <= 0:
                    break
                    
                await asyncio.sleep(time_to_wait)
                elapsed += time_to_wait
                
                # Check recent messages for profile updates
                messages = await self.client.get_messages(self.game_chat, limit=3)
                for msg in messages:
                    if msg.text and "Здоров'я:" in msg.text and "Енергія:" in msg.text:
                        # Parse HP from profile message
                        hp_match = re.search(r'Здоров\'я: (\d+)/(\d+)', msg.text)
                        if hp_match:
                            current_hp = int(hp_match.group(1))
                            max_hp = int(hp_match.group(2))
                            if current_hp >= max_hp:
                                logger.info("Manual healing detected! HP is now full!")
                                self.current_hp = current_hp
                                self.max_hp = max_hp
                                return
                
                # Show progress
                remaining = max(0, wait_seconds - elapsed)
                if remaining > 0 and elapsed % 60 == 0:  # Log every minute
                    logger.info(f"Still waiting for HP... {remaining // 60} minutes remaining")
        else:
            # Check every minute until full
            logger.info("Waiting for full HP (checking every minute)...")
            while self.current_hp < self.max_hp:
                await asyncio.sleep(60)
                await self.check_character_status()
                if self.current_hp >= self.max_hp:
                    logger.info("HP is now full!")
                    break
    
    async def wait_for_energy(self):
        """Wait for energy to regenerate"""
        if self.energy_regen_minutes:
            wait_seconds = (self.energy_regen_minutes * 60) + 30  # Add 30s buffer
            logger.info(f"Waiting {self.energy_regen_minutes} minutes for next energy...")
            await asyncio.sleep(wait_seconds)
        else:
            # Wait 5 minutes as default
            logger.info("Waiting 5 minutes for energy...")
            await asyncio.sleep(300)
    
    async def explore(self):
        """Send explore command"""
        logger.info(f"Exploring... (HP: {self.current_hp}/{self.max_hp}, Energy: {self.current_energy}/{self.max_energy})")
        await self.human_delay()
        await self.client.send_message(self.game_chat, "🗺️ Досліджувати (⚡1)")
        await asyncio.sleep(3)
    
    async def handle_battle(self):
        """Handle battle with simple logic"""
        battle_ended = False
        rounds = 0
        should_escape = False
        escape_attempts = 0
        max_escape_attempts = 5
        mob_name = "Unknown"
        
        logger.info("Battle started!")
        
        # Check if we should escape from this mob and extract mob name
        messages = await self.client.get_messages(self.game_chat, limit=2)
        for msg in messages:
            if msg.text and "З'явився" in msg.text:
                # Extract mob name from message
                mob_match = re.search(r'З\'явився (.+?)!', msg.text)
                if mob_match:
                    mob_name = mob_match.group(1)
                
                for escape_mob in self.config.ESCAPE_MOBS:
                    if escape_mob in msg.text:
                        should_escape = True
                        logger.warning(f"Encountered escape mob: {escape_mob} - will attempt to run away!")
                        break
                break
        
        if should_escape:
            logger.info(f"Trying to escape from: {mob_name}")
        else:
            logger.info(f"Fighting against: {mob_name}")
        
        while not battle_ended and rounds < 30:
            rounds += 1
            await asyncio.sleep(3)
            
            # If we've exceeded max escape attempts for an escape mob, fight normally
            if should_escape and escape_attempts >= max_escape_attempts:
                logger.warning(f"Max escape attempts ({max_escape_attempts}) exceeded, will fight normally")
                should_escape = False
            
            # Get latest messages
            messages = await self.client.get_messages(self.game_chat, limit=2)
            
            for msg in messages:
                if not msg.text:
                    continue
                
                # Check if battle ended
                if "Ви отримали:" in msg.text:
                    logger.info("Battle won!")
                    battle_ended = True
                    break
                elif "Ви зазнали поразки!" in msg.text:
                    logger.warning(f"Battle lost against {mob_name}!")
                    battle_ended = True
                    break
                elif "Ви не перебуваєте в бою" in msg.text:
                    logger.info("Not in battle - enemy fled or battle ended")
                    battle_ended = True
                    break
                elif "занудьгував і втік" in msg.text or "втік" in msg.text:
                    logger.info("Enemy fled!")
                    battle_ended = True
                    break
                elif "Вам вдалося втекти!" in msg.text:
                    logger.info("Successfully escaped!")
                    battle_ended = True
                    break
                elif "Втеча не вдалася!" in msg.text:
                    if should_escape:  # Only process if we're still trying to escape
                        if escape_attempts < max_escape_attempts:
                            logger.warning(f"Escape failed! Will try again... (attempt {escape_attempts}/{max_escape_attempts})")
                        else:
                            logger.warning(f"Escape failed! Max attempts reached ({escape_attempts}/{max_escape_attempts})")
                            should_escape = False
                    continue
                
                # Handle battle actions
                if msg.buttons and not battle_ended:
                    # Extract current HP from message
                    current_hp = None
                    hp_match = re.search(r'👤 Ви \((\d+)/(\d+)\)', msg.text)
                    if hp_match:
                        current_hp = int(hp_match.group(1))
                    
                    # Check for action buttons
                    has_attack = False
                    has_skills = False
                    has_potions = False
                    has_escape = False
                    
                    for row_idx, row in enumerate(msg.buttons):
                        for btn_idx, btn in enumerate(row):
                            if btn.text:
                                if "Атака" in btn.text:
                                    has_attack = True
                                elif "Прийоми" in btn.text:
                                    has_skills = True
                                elif "Зілля" in btn.text:
                                    has_potions = True
                                elif "Втеча" in btn.text:
                                    has_escape = True
                    
                    # If this is a battle message with actions
                    if has_attack or has_escape:
                        clicked = False
                        
                        # Priority 1: Try to escape if this is an escape mob and we haven't exceeded max attempts
                        if should_escape and has_escape and escape_attempts < max_escape_attempts:
                            for row_idx, row in enumerate(msg.buttons):
                                for btn_idx, btn in enumerate(row):
                                    if btn.text and "Втеча" in btn.text:
                                        escape_attempts += 1  # Increment before clicking
                                        await self.human_delay()
                                        await msg.click(row_idx, btn_idx)
                                        logger.info(f"Clicking escape button (attempt {escape_attempts}/{max_escape_attempts})")
                                        clicked = True
                                        break
                                if clicked:
                                    break
                        
                        # Priority 2: Use potion if HP < 100 (and we're not escaping)
                        if has_potions and current_hp and current_hp < 100 and not clicked:
                            for row_idx, row in enumerate(msg.buttons):
                                for btn_idx, btn in enumerate(row):
                                    if btn.text and "Зілля" in btn.text:
                                        await self.human_delay()
                                        await msg.click(row_idx, btn_idx)
                                        logger.info(f"Clicked potions button (HP: {current_hp})")
                                        clicked = True
                                        
                                        # Wait and select first potion
                                        await asyncio.sleep(3)
                                        potion_msgs = await self.client.get_messages(self.game_chat, limit=2)
                                        for pmsg in potion_msgs:
                                            if pmsg.text and "Оберіть зілля" in pmsg.text and pmsg.buttons:
                                                await self.human_delay()
                                                await pmsg.click(0, 0)
                                                logger.info("Selected first potion")
                                                break
                                        break
                                if clicked:
                                    break
                        
                        # Priority 3: Use skills if available
                        elif has_skills and not clicked:
                            for row_idx, row in enumerate(msg.buttons):
                                for btn_idx, btn in enumerate(row):
                                    if btn.text and "Прийоми" in btn.text:
                                        await self.human_delay()
                                        await msg.click(row_idx, btn_idx)
                                        logger.info("Clicked skills button")
                                        clicked = True
                                        
                                        # Wait and select last skill (button before the "back" button)
                                        await asyncio.sleep(3)
                                        skill_msgs = await self.client.get_messages(self.game_chat, limit=2)
                                        for smsg in skill_msgs:
                                            if smsg.text and "Оберіть прийом" in smsg.text and smsg.buttons:
                                                # Skills are placed vertically, last button is "back"
                                                # So we need to click the button before the last one
                                                num_buttons = len(smsg.buttons)
                                                if num_buttons >= 2:
                                                    # Click the second-to-last button (last skill)
                                                    skill_index = num_buttons - 2
                                                    await self.human_delay()
                                                    await smsg.click(skill_index, 0)
                                                    logger.info(f"Selected last skill (button {skill_index})")
                                                else:
                                                    # Fallback: if only 1 button, click it
                                                    await self.human_delay()
                                                    await smsg.click(0, 0)
                                                    logger.info("Selected only available skill")
                                                break
                                        break
                                if clicked:
                                    break
                        
                        # Priority 4: Otherwise attack
                        if not clicked:
                            for row_idx, row in enumerate(msg.buttons):
                                for btn_idx, btn in enumerate(row):
                                    if btn.text and "Атака" in btn.text:
                                        await self.human_delay()
                                        await msg.click(row_idx, btn_idx)
                                        logger.info(f"Clicked attack (round {rounds}, HP: {current_hp})")
                                        clicked = True
                                        break
                                if clicked:
                                    break
                        
                        break  # Only process one battle message
        
        if should_escape:
            logger.info(f"Battle ended after {rounds} rounds")
        await asyncio.sleep(3)
    
    async def main_loop(self):
        """Main bot loop"""
        logger.info("=== MAIN LOOP STARTED ===")
        
        while self.is_running:
            try:
                logger.info("=" * 50)  # Separator for new exploration cycle
                
                # 🧍 Check character status
                await self.check_character_status()
                
                # ❤️ Wait for full HP if needed
                if self.current_hp < self.max_hp:
                    await self.wait_for_full_hp()
                    continue
                
                # ⚡ Check if we have energy
                if self.current_energy < 1:
                    await self.wait_for_energy()
                    continue
                
                # 🚫 Check exploration restrictions (time window + energy limit)
                if not self.energy_tracker.can_explore_now():
                    # Check what's preventing exploration
                    if not self.energy_tracker.is_in_exploration_window():
                        time_until_window = self.energy_tracker.get_time_until_exploration_window()
                        start_hour = self.energy_tracker.exploration_start_hour
                        logger.warning(f"Outside exploration window (starts at {start_hour:02d}:00)! "
                                     f"Waiting {time_until_window} until exploration time")
                        
                        # Wait until exploration window opens (check every 10 minutes)
                        while not self.energy_tracker.is_in_exploration_window():
                            await asyncio.sleep(600)  # 10 minutes
                            time_remaining = self.energy_tracker.get_time_until_exploration_window()
                            logger.info(f"Still waiting for exploration window... {time_remaining} remaining")
                        
                        logger.info(f"Exploration window opened! ({start_hour:02d}:00 - 12:00)")
                        continue
                    
                    elif not self.energy_tracker.can_use_energy():
                        remaining_energy = self.energy_tracker.get_remaining_energy()
                        time_until_reset = self.energy_tracker.get_time_until_reset()
                        logger.warning(f"Daily energy limit reached ({self.energy_tracker.daily_limit})! "
                                     f"Waiting {time_until_reset} until reset at 12:00")
                        
                        # Wait until energy resets (check every 5 minutes)
                        while not self.energy_tracker.can_use_energy():
                            await asyncio.sleep(300)  # 5 minutes
                            logger.info(f"Still waiting for energy reset... {self.energy_tracker.get_time_until_reset()} remaining")
                        
                        logger.info("Daily energy limit reset! Now waiting for exploration window...")
                        
                        # After reset, check if we need to wait for exploration window
                        if not self.energy_tracker.is_in_exploration_window():
                            time_until_window = self.energy_tracker.get_time_until_exploration_window()
                            start_hour = self.energy_tracker.exploration_start_hour
                            logger.info(f"Waiting {time_until_window} until exploration window opens at {start_hour:02d}:00")
                            
                            while not self.energy_tracker.is_in_exploration_window():
                                await asyncio.sleep(600)  # 10 minutes
                                time_remaining = self.energy_tracker.get_time_until_exploration_window()
                                logger.info(f"Still waiting for exploration window... {time_remaining} remaining")
                        
                        logger.info("Ready to explore!")
                        continue
                
                # 🗺️ Explore
                await self.explore()
                
                # Track energy usage
                self.energy_tracker.use_energy(1)
                
                # Check response
                messages = await self.client.get_messages(self.game_chat, limit=2)
                
                battle_started = False
                camp_found = False
                
                for msg in messages:
                    if msg.text:
                        # ⚔️ Check if battle started
                        if "З'явився" in msg.text or (msg.buttons and any("Атака" in btn.text for row in msg.buttons for btn in row if btn.text)):
                            battle_started = True
                            break
                        # ⛺ Check for camp opportunity
                        elif ("покинутий табір" in msg.text or "табір" in msg.text.lower()) and msg.buttons:
                            logger.info(f"Camp found: {msg.text[:80]}...")
                            # Click the first available button (usually "Дослідити")
                            await self.human_delay()
                            await msg.click(0, 0)
                            logger.info("Clicked camp exploration button")
                            camp_found = True
                            await asyncio.sleep(3)
                            break
                        # 👋 Check for player greeting
                        elif ("який подорожує неподалік" in msg.text or "ви бачите" in msg.text.lower()) and msg.buttons:
                            logger.info(f"Other player found: {msg.text[:80]}...")
                            # Click the first available button (usually "Привітати")
                            await self.human_delay()
                            await msg.click(0, 0)
                            logger.info("Clicked player greeting button")
                            camp_found = True
                            await asyncio.sleep(3)
                            break
                        # 🪤 Check for guild trap
                        elif ("Ви знайшли стару пастку" in msg.text or "полагодити її?" in msg.text.lower()) and msg.buttons:
                            logger.info(f"Found oportunity to create a trap: {msg.text[:80]}...")
                            # Click the first available button (usually "Встановити пастку")
                            await self.human_delay()
                            await msg.click(0, 0)
                            logger.info("Clicked trap creation button, trap installed")
                            camp_found = True
                            await asyncio.sleep(3)
                            break
                        # ❌ Check if no energy
                        elif "Недостатньо енергії" in msg.text:
                            logger.info("Out of energy")
                            self.current_energy = 0
                            break
                
                # ⚔️ Handle battle if started (either from exploration or camp)
                if battle_started:
                    await self.handle_battle()
                elif camp_found:
                    logger.info("Camp exploration completed")
                
                # 🕑 Small delay before next iteration (shorter if we found something interesting)
                if battle_started or camp_found:
                    await asyncio.sleep(1)  # Quick continuation after action
                else:
                    await asyncio.sleep(2)  # Normal delay
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(10)
    
    async def stop(self):
        """Stop the bot"""
        self.is_running = False
        logger.info("Bot stopped")
