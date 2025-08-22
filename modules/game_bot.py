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
import random
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
        
        # Human-like behavior tracking
        self.battle_session_count = 0  # Track consecutive battles in current session
        self.last_activity_time = None  # Track last exploration/battle time
        self.energy_full_timestamp = None  # Track when energy became full
        self.session_battles_target = 0  # Random target for battles in current session
        self.waiting_for_full_energy = False  # Whether we're waiting for full energy
        self.session_start_time = None  # Track when current session started (for fatigue)
        self.total_battles_today = 0  # Track total battles for fatigue simulation
        self.last_mode_was_working = None  # Track mode changes
    
    async def human_delay(self, min_seconds=None, max_seconds=None):
        """Simulate human-like reaction time with scaling based on HUMAN_LIKE level"""
        # Only apply human delays when HUMAN_LIKE > 0 AND we're outside working hours
        if self.config.HUMAN_LIKE == 0 or await self.is_in_working_hours():
            return  # No delay in efficient mode or during working hours
        
        if min_seconds is None:
            min_seconds = self.config.HUMAN_DELAY_MIN
        if max_seconds is None:
            max_seconds = self.config.HUMAN_DELAY_MAX
        
        # Scale delays based on human-like level (rebalanced levels)
        level_multipliers = {
            1: 0.3,   # 30% of configured delays
            2: 0.6,   # 60% of configured delays
            3: 0.8,   # 80% of configured delays (new level between 2 and 4)
            4: 1.0,   # 100% of configured delays (was old 3)
            5: 1.5    # 150% of configured delays (was old 4)
        }
        
        multiplier = level_multipliers.get(self.config.HUMAN_LIKE, 1.0)
        
        # Apply fatigue factor at levels 4+ (slower reactions after playing for a while)
        fatigue_multiplier = 1.0
        if self.config.HUMAN_LIKE >= 4 and self.session_start_time:
            session_duration = (datetime.now() - self.session_start_time).total_seconds() / 3600  # hours
            if session_duration > 1:  # After 1 hour
                # Gradually increase delays up to 50% at level 4, 75% at level 5
                max_fatigue = {4: 0.5, 5: 0.75}.get(self.config.HUMAN_LIKE, 0.5)
                fatigue_multiplier = 1 + (min(session_duration - 1, 2) / 2) * max_fatigue
        
        delay = random.uniform(min_seconds * multiplier * fatigue_multiplier, 
                              max_seconds * multiplier * fatigue_multiplier)
        await asyncio.sleep(delay)
    
    async def start(self):
        """Initialize bot and start main loop"""
        try:
            logger.info("=== BOT STARTING ===")
            
            # Connect to game bot
            self.game_chat = await self.client.get_entity(self.config.GAME_BOT_USERNAME)
            logger.info(f"Connected to game bot: {self.game_chat.username}")
            
            # Don't send /start automatically - it's suspicious
            # Just proceed to main loop directly
            await self.human_delay(2, 4)
            
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
            
            # Check for special messages
            for msg in messages:
                if msg.text:
                    # Check if we're in battle (shouldn't check status during battle)
                    if "Ви в бою!" in msg.text:
                        logger.warning("Still in battle! Cannot check character status now")
                        # Return current known values, battle will be handled in main loop
                        return
                    # Check for "don't rush" message
                    elif "Будь ласка, не поспішайте" in msg.text or "не поспішайте" in msg.text:
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
            # After waiting, check status to update energy values
            await self.check_character_status()
        else:
            # Wait 5 minutes as default
            logger.info("Waiting 5 minutes for energy...")
            await asyncio.sleep(300)
            # After waiting, check status to update energy values
            await self.check_character_status()
    
    async def explore(self):
        """Send explore command"""
        logger.info(f"Exploring... (HP: {self.current_hp}/{self.max_hp}, Energy: {self.current_energy}/{self.max_energy})")
        await self.human_delay()
        await self.client.send_message(self.game_chat, "🗺️ Досліджувати (⚡1)")
        await asyncio.sleep(3)
    
    async def handle_battle(self):
        """Handle battle with simple logic and human-like delays"""
        battle_ended = False
        rounds = 0
        should_escape = False
        escape_attempts = 0
        max_escape_attempts = 5
        mob_name = "Unknown"
        
        logger.info("Battle started!")
        
        # Add reaction delay for human-like behavior (only outside working hours)
        if self.config.HUMAN_LIKE > 0 and not await self.is_in_working_hours():
            # Longer initial reaction when battle starts
            reaction_delay = await self.get_human_like_pause("message_reading")
            await asyncio.sleep(reaction_delay)
        
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
    
    async def get_human_like_pause(self, pause_type="between_battles"):
        """Get random pause duration based on context and human-like level"""
        level = self.config.HUMAN_LIKE
        if level == 0:
            return 0  # No delays

        # Base delays that scale with level
        delay_multipliers = {
            0: 0,
            1: 0.1,   # 10% of base delays
            2: 0.3,   # 30% of base delays
            3: 0.6,   # 60% of base delays (new mid level)
            4: 1.0,   # 100% of base delays (was old 3)
            5: 2.0    # 200% of base delays (was old 4)
        }
        
        multiplier = delay_multipliers.get(level, 1.0)
        
        if pause_type == "between_battles":
            # Short pause between consecutive battles in a session
            base_min, base_max = 30, 120  # 30 seconds to 2 minutes
            return random.uniform(base_min * multiplier, base_max * multiplier)
        elif pause_type == "session_break":
            # Longer break after completing a battle session
            base_min, base_max = 900, 2700  # 15 to 45 minutes
            return random.uniform(base_min * multiplier, base_max * multiplier)
        elif pause_type == "before_energy_use":
            # Pause before using newly available energy
            base_min, base_max = 120, 600  # 2 to 10 minutes
            return random.uniform(base_min * multiplier, base_max * multiplier)
        elif pause_type == "waiting_for_full":
            # Additional wait when deciding to wait for full energy
            base_min, base_max = 300, 900  # 5 to 15 minutes
            return random.uniform(base_min * multiplier, base_max * multiplier)
        elif pause_type == "message_reading":
            # Time to "read" a message based on length
            base_min, base_max = 0.5, 2  # 0.5 to 2 seconds base
            return random.uniform(base_min * multiplier, base_max * multiplier)
        else:
            base_min, base_max = 60, 180  # Default 1-3 minutes
            return random.uniform(base_min * multiplier, base_max * multiplier)
    
    async def should_wait_for_full_energy(self):
        """Decide if we should wait for full energy (human-like decision)"""
        level = self.config.HUMAN_LIKE
        if level == 0:
            return False
        
        # Chance to wait for full energy scales with level
        wait_chances = {
            1: 0.05,  # 5%
            2: 0.12,  # 12%
            3: 0.20,  # 20%
            4: 0.30,  # 30% (was old 3)
            5: 0.45   # 45% (was old 4)
        }
        
        chance = wait_chances.get(level, 0.3)
        
        # Higher chance to wait if we have less than max energy
        if self.current_energy < self.max_energy:
            return random.random() < chance
        return False
    
    async def is_in_working_hours(self):
        """Check if we're in the configured working time window"""
        now = datetime.now()
        current_hour = now.hour

        # Special raid days: Tuesday(1), Thursday(3), Sunday(6)
        weekday = now.weekday()
        is_raid_day = weekday in (1, 3, 6)

        # Raid days:
        # - 20:00-22:00: always working hours (efficient mode)
        # - >=22: enforce efficient mode until configured working hours take over or end (prevents human-like)
        if is_raid_day:
            if 20 <= current_hour < 22:
                return True
            if current_hour >= 22:
                return True

        # Non-raid days: follow configured working hours
        if self.config.EXPLORATION_START_HOUR == -1:
            return False  # No time window configured

        start_hour = self.config.EXPLORATION_START_HOUR
        end_hour = 12  # Always ends at noon

        if start_hour > end_hour:
            # Handles midnight crossover (e.g., 23:00 - 12:00)
            return current_hour >= start_hour or current_hour < end_hour
        else:
            # Normal time range (e.g., 6:00 - 12:00)
            return start_hour <= current_hour < end_hour
    
    async def get_message_reading_delay(self, text):
        """Calculate delay for 'reading' a message based on its length"""
        if self.config.HUMAN_LIKE == 0 or not text:
            return 0
        
        # Estimate word count (rough approximation)
        word_count = len(text.split())
        
        # Base reading speed: 200-300 words per minute (3-5 words per second)
        # Scales with human-like level
        base_time = word_count / 4  # Base ~250 wpm
        
        level_multipliers = {
            1: 0.2,   # Very fast reading
            2: 0.5,   # Fast reading
            3: 0.8,   # Between fast and normal
            4: 1.0,   # Normal reading speed (was old 3)
            5: 1.5    # Careful reading (was old 4)
        }
        
        multiplier = level_multipliers.get(self.config.HUMAN_LIKE, 1.0)
        reading_time = base_time * multiplier
        
        # Add some randomness (±20%)
        reading_time *= random.uniform(0.8, 1.2)
        
        # Cap between 0.5 and 10 seconds
        return min(max(reading_time, 0.5), 10)
    
    async def main_loop(self):
        """Main bot loop"""
        logger.info("=== MAIN LOOP STARTED ===")
        if self.config.HUMAN_LIKE > 0:
            level_descriptions = {
                1: "Minimal - slight randomization",
                2: "Light - basic patterns",
                3: "Balanced - moderate human-like",
                4: "Realistic - human-like patterns",
                5: "Heavy - very human-like"
            }
            desc = level_descriptions.get(self.config.HUMAN_LIKE, "Unknown")
            logger.info(f"Human-like mode enabled - Level {self.config.HUMAN_LIKE} ({desc})")
            
            if self.config.EXPLORATION_START_HOUR != -1:
                logger.info(f"Will use efficient mode during working hours ({self.config.EXPLORATION_START_HOUR}:00 - 12:00)")
                logger.info(f"Human-like behavior active outside working hours")
        
        while self.is_running:
            try:
                logger.info("=" * 50)  # Separator for new exploration cycle
                
                # Check if we switched modes
                if self.config.HUMAN_LIKE > 0 and self.config.EXPLORATION_START_HOUR != -1:
                    is_working_hours = await self.is_in_working_hours()
                    if self.last_mode_was_working is not None and self.last_mode_was_working != is_working_hours:
                        if is_working_hours:
                            logger.info("⚡ Switched to EFFICIENT MODE (working hours started)")
                        else:
                            logger.info("🤖 Switched to HUMAN-LIKE MODE (working hours ended)")
                    self.last_mode_was_working = is_working_hours
                
                # 🧍 Check character status only when needed
                # Always check on first iteration
                if self.current_hp == 0 and self.max_hp == 1:  # Initial values, never checked
                    await self.check_character_status()
                
                # Check if we're in an ongoing battle (status check might have detected it)
                messages = await self.client.get_messages(self.game_chat, limit=2)
                for msg in messages:
                    if msg.buttons:
                        for row in msg.buttons:
                            for btn in row:
                                if btn.text and "Атака" in btn.text:
                                    logger.warning("Detected ongoing battle! Handling it now...")
                                    await self.handle_battle()
                                    # Check status after handling the battle
                                    await self.check_character_status()
                                    self._last_status_check_time = datetime.now()  # Mark that we just checked
                                    continue  # Continue main loop after battle
                
                # ❤️ Wait for full HP if needed
                if self.current_hp < self.max_hp:
                    await self.wait_for_full_hp()
                    # HP should be full now, but double-check
                    if self.current_hp < self.max_hp:
                        await self.check_character_status()
                    continue
                
                # ⚡ Check if we have energy
                if self.current_energy < 1:
                    await self.wait_for_energy()
                    # After waiting and checking, if we still have no energy, continue waiting
                    if self.current_energy < 1:
                        continue
                    # Otherwise we now have energy and can proceed
                
                # 🤖 Human-like: Decide if we should wait for full energy (only outside working hours)
                if self.config.HUMAN_LIKE > 0 and not await self.is_in_working_hours():
                    if self.waiting_for_full_energy or await self.should_wait_for_full_energy():
                        # Check current status to get fresh energy value
                        await self.check_status()
                        if self.current_energy < self.max_energy:
                            if not self.waiting_for_full_energy:
                                wait_time = await self.get_human_like_pause("waiting_for_full")
                                logger.info(f"Human-like: Decided to wait for full energy. Waiting {wait_time/60:.1f} minutes...")
                                self.waiting_for_full_energy = True
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                # Continue waiting for full energy
                                logger.info("Human-like: Still waiting for full energy...")
                                await asyncio.sleep(60)
                                continue
                        else:
                            # Energy is now full
                            self.waiting_for_full_energy = False
                            logger.info("Human-like: Energy is full, proceeding with exploration session")
                
                # 🚫 Check exploration restrictions (time window + energy limit)
                # IMPORTANT: When HUMAN_LIKE > 0 and outside working hours, ignore ALL restrictions
                # Only apply restrictions in two cases:
                # 1. HUMAN_LIKE == 0 (efficient mode always)
                # 2. HUMAN_LIKE > 0 BUT currently in working hours (efficient mode during work)
                
                is_human_mode_active = self.config.HUMAN_LIKE > 0 and not await self.is_in_working_hours()
                
                if is_human_mode_active:
                    # Human-like mode is active - ignore all restrictions and continue with human-like behavior
                    # Track when energy becomes full
                    if self.current_energy >= self.max_energy:
                        if self.energy_full_timestamp is None:
                            self.energy_full_timestamp = datetime.now()
                            logger.info("Human-like: Energy is full, tracking timestamp")
                        else:
                            # Check if energy has been full for too long
                            time_since_full = (datetime.now() - self.energy_full_timestamp).total_seconds()
                            if time_since_full > 1500:  # 25 minutes
                                logger.warning(f"Human-like: Energy has been full for {time_since_full/60:.1f} minutes! Must use it soon.")
                                # Force exploration to avoid wasting energy
                    else:
                        self.energy_full_timestamp = None
                    
                    # Add human-like pause before starting new session
                    if self.battle_session_count == 0:
                        # Check if we just finished a session and need a break
                        if self.last_activity_time:
                            time_since_last = (datetime.now() - self.last_activity_time).total_seconds()
                            if time_since_last < 60:  # Just finished a session
                                pause = await self.get_human_like_pause("session_break")
                                logger.info(f"Human-like: Taking a break between sessions for {pause/60:.1f} minutes")
                                await asyncio.sleep(pause)
                        
                        # Set new session target (varies by level)
                        if self.config.HUMAN_LIKE <= 2:
                            self.session_battles_target = random.randint(5, 8)  # More battles at lower levels
                        elif self.config.HUMAN_LIKE == 3:
                            self.session_battles_target = random.randint(3, 5)  # Moderate
                        else:
                            self.session_battles_target = random.randint(2, 4)  # Fewer battles at higher levels

                        # Daytime boost (12:00 - 19:00): subtly increase chance to spend all energy
                        # Keep original randomness but probabilistically push target higher
                        try:
                            hour_now = datetime.now().hour
                            if 12 <= hour_now < 19 and self.current_energy > 0:
                                # Probability scales mildly with human-like level
                                p = min(0.15 + 0.05 * max(0, self.config.HUMAN_LIKE - 1), 0.45)
                                if random.random() < p:
                                    # Push target toward depleting current energy in this session
                                    desired = self.battle_session_count + self.current_energy
                                    jitter = random.randint(-1, 2)  # small randomness
                                    desired = max(1, desired + jitter)
                                    self.session_battles_target = max(self.session_battles_target, desired)
                        except Exception:
                            pass
                        
                        # Mark session start time for fatigue tracking
                        if not self.session_start_time:
                            self.session_start_time = datetime.now()
                        
                        logger.info(f"Human-like: Starting new session, target: {self.session_battles_target} battles")
                        
                        # Small pause before starting
                        pause = await self.get_human_like_pause("before_energy_use")
                        logger.info(f"Human-like: Waiting {pause/60:.1f} minutes before starting exploration")
                        await asyncio.sleep(pause)
                    
                    # In human-like mode outside working hours, we ALWAYS continue without checking restrictions
                    # The bot should explore regardless of energy limits or time windows
                    
                else:
                    # Efficient mode (either HUMAN_LIKE == 0 or we're in working hours)
                    # Apply all restrictions normally
                    if not self.energy_tracker.can_explore_now():
                        # Check what's preventing exploration
                        if not self.energy_tracker.is_in_exploration_window():
                            time_until_window = self.energy_tracker.get_time_until_exploration_window()
                            start_hour = self.energy_tracker.exploration_start_hour
                            
                            # If HUMAN_LIKE > 0, we should switch to human mode when window closes
                            if self.config.HUMAN_LIKE > 0:
                                logger.info(f"Working hours ended. Switching to human-like mode (Level {self.config.HUMAN_LIKE})")
                                # Don't wait, just continue in human-like mode
                                continue
                            else:
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
                            
                            # If HUMAN_LIKE > 0 and we're outside working hours now, switch to human mode
                            if self.config.HUMAN_LIKE > 0 and not await self.is_in_working_hours():
                                logger.info(f"Energy limit reached but outside working hours. Switching to human-like mode (Level {self.config.HUMAN_LIKE})")
                                # Don't wait, just continue in human-like mode
                                continue
                            else:
                                logger.warning(f"Daily energy limit reached ({self.energy_tracker.daily_limit})! "
                                             f"Waiting {time_until_reset} until reset at 12:00")
                                
                                # Wait until energy resets (check every 5 minutes)
                                while not self.energy_tracker.can_use_energy():
                                    # Check if we should switch to human mode
                                    if self.config.HUMAN_LIKE > 0 and not await self.is_in_working_hours():
                                        logger.info(f"Working hours ended. Switching to human-like mode (Level {self.config.HUMAN_LIKE})")
                                        break  # Exit wait loop and continue in human mode
                                    
                                    await asyncio.sleep(300)  # 5 minutes
                                    logger.info(f"Still waiting for energy reset... {self.energy_tracker.get_time_until_reset()} remaining")
                                
                                # If we broke out due to mode switch, continue
                                if self.config.HUMAN_LIKE > 0 and not await self.is_in_working_hours():
                                    continue
                                
                                logger.info("Daily energy limit reset!")
                                
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
                # Check status before exploring to catch manual play or changes
                # But only if we haven't checked recently (avoid double checks)
                should_check_before_explore = False
                
                # Check if we need to update status
                if not hasattr(self, '_last_status_check_time'):
                    should_check_before_explore = True
                else:
                    time_since_last_check = (datetime.now() - self._last_status_check_time).total_seconds()
                    # Check if more than 30 seconds passed since last check
                    if time_since_last_check > 30:
                        # Random chance to check (70%) or always if HP might not be full
                        if random.random() < 0.7 or self.current_hp < self.max_hp:
                            should_check_before_explore = True
                
                if should_check_before_explore:
                    await self.check_character_status()
                    self._last_status_check_time = datetime.now()
                    
                    # Only explore if we still have HP and energy after the check
                    if self.current_hp < self.max_hp:
                        logger.info("HP not full after status check, need to wait")
                        continue
                    if self.current_energy < 1:
                        logger.info("No energy after status check")
                        continue
                    
                await self.explore()
                
                # Decrease energy after exploration (we just used 1 energy)
                if self.current_energy > 0:
                    self.current_energy -= 1
                
                # Track energy usage for daily limits
                # - During raid window: spend energy regardless of limit, but only count usage up to the limit
                # - Otherwise: count only in efficient mode (HUMAN_LIKE == 0 OR during working hours)
                is_working = await self.is_in_working_hours()
                if hasattr(self.energy_tracker, "_is_raid_window_now") and self.energy_tracker._is_raid_window_now():
                    if self.energy_tracker.daily_limit <= 0 or self.energy_tracker.energy_used < self.energy_tracker.daily_limit:
                        self.energy_tracker.use_energy(1)
                else:
                    if self.config.HUMAN_LIKE == 0 or is_working:
                        self.energy_tracker.use_energy(1)
                
                # Update human-like tracking (only relevant outside working hours)
                if self.config.HUMAN_LIKE > 0 and not await self.is_in_working_hours():
                    self.last_activity_time = datetime.now()
                    self.energy_full_timestamp = None  # Reset since we just used energy
                
                # Check response
                messages = await self.client.get_messages(self.game_chat, limit=3)  # Get more messages to be sure
                
                battle_started = False
                camp_found = False
                
                for msg in messages:
                    # Check for battle buttons first (most reliable)
                    if msg.buttons:
                        for row in msg.buttons:
                            for btn in row:
                                if btn.text and "Атака" in btn.text:
                                    battle_started = True
                                    logger.info("Battle detected via attack button")
                                    break
                            if battle_started:
                                break
                    
                    if msg.text and not battle_started:
                        # Add reading delay for human-like behavior (only outside working hours)
                        if self.config.HUMAN_LIKE > 0 and not await self.is_in_working_hours():
                            reading_delay = await self.get_message_reading_delay(msg.text)
                            if reading_delay > 0:
                                await asyncio.sleep(reading_delay)
                        
                        # ⚔️ Check if battle started by text
                        if "З'явився" in msg.text or "Ви в бою!" in msg.text:
                            battle_started = True
                            logger.info("Battle detected via message text")
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
                    # ALWAYS check status after battle to update HP
                    await self.check_character_status()
                    self._last_status_check_time = datetime.now()  # Mark that we just checked
                    if self.config.HUMAN_LIKE > 0 and not await self.is_in_working_hours():
                        self.battle_session_count += 1
                        if self.config.HUMAN_LIKE >= 4:  # Only log at moderate level or higher
                            logger.info(f"Human-like: Battle {self.battle_session_count}/{self.session_battles_target} in current session")
                elif camp_found:
                    logger.info("Camp exploration completed")
                    # Check status after camp in case rewards affected HP/energy
                    await self.check_character_status()
                    self._last_status_check_time = datetime.now()  # Mark that we just checked
                    if self.config.HUMAN_LIKE > 0 and not await self.is_in_working_hours():
                        self.battle_session_count += 1  # Camps count as activity
                
                # 🤖 Human-like: Check if we should take a session break (only outside working hours)
                if self.config.HUMAN_LIKE > 0 and not await self.is_in_working_hours():
                    # Daytime incremental bias: occasionally extend target to spend remaining energy
                    try:
                        hour_now = datetime.now().hour
                        if 12 <= hour_now < 19 and self.current_energy > 0 and (battle_started or camp_found):
                            p_ext = min(0.1 + 0.04 * max(0, self.config.HUMAN_LIKE - 1), 0.35)
                            if random.random() < p_ext:
                                desired = self.battle_session_count + self.current_energy
                                jitter = random.randint(-1, 1)
                                desired = max(1, desired + jitter)
                                self.session_battles_target = max(self.session_battles_target, desired)
                    except Exception:
                        pass
                    if self.battle_session_count >= self.session_battles_target:
                        logger.info(f"Human-like: Completed session with {self.battle_session_count} battles")
                        self.battle_session_count = 0
                        self.last_activity_time = datetime.now()
                        # The break will be applied at the start of next loop iteration
                    elif battle_started or camp_found:
                        # Add human-like pause between battles in a session
                        pause = await self.get_human_like_pause("between_battles")
                        logger.info(f"Human-like: Pausing {pause:.0f} seconds between battles")
                        await asyncio.sleep(pause)
                    else:
                        await asyncio.sleep(2)  # Normal delay when nothing found
                else:
                    # Normal mode or during working hours - minimal delays
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
