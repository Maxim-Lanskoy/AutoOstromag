"""
Main game bot logic - Improved version with better state tracking
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
    """Main game bot controller - improved state tracking"""
    
    def __init__(self, client, config):
        self.client = client
        self.config = config
        self.parser = GameParser()
        
        # State
        self.game_chat = None
        self.is_running = False
        
        # Track HP, energy and other stats
        self.current_hp = 245
        self.max_hp = 245
        self.current_energy = 10
        self.max_energy = 10
        self.level = 1
        self.gold = 0
        
        # Energy tracking
        self.last_energy_use = datetime.now()
        self.energy_regen_time = None
        
    async def human_delay(self, min_seconds=0.5, max_seconds=2.0):
        """Add randomized delay to simulate human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def start(self):
        """Start the bot"""
        try:
            # Find game bot chat
            self.game_chat = await self.client.get_entity(self.config.GAME_BOT_USERNAME)
            logger.info(f"Found game bot: {self.game_chat.username}")
            
            # Send /start command only once
            await self.human_delay(1, 3)  # Human reads the screen first
            await self.client.send_message(self.game_chat, '/start')
            await asyncio.sleep(2)
            
            # Get response and click button if exists
            messages = await self.client.get_messages(self.game_chat, limit=3)
            for msg in messages:
                if msg.buttons:
                    await self.human_delay()  # Human reaction time
                    await msg.click(0)
                    logger.info("Clicked start button")
                    await asyncio.sleep(1)
                    break
            
            # Check character status once at start
            await self.check_character_status()
            
            # Start main loop
            self.is_running = True
            await self.main_loop()
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
    
    async def check_character_status(self):
        """Check character status to get real HP/energy state"""
        try:
            logger.info("Checking character status...")
            await self.human_delay(0.5, 1.5)
            await self.client.send_message(self.game_chat, "🧍 Персонаж")
            await asyncio.sleep(2)
            
            messages = await self.client.get_messages(self.game_chat, limit=5)
            
            for msg in messages:
                if msg.text and "Рівень" in msg.text and "Здоров'я:" in msg.text:
                    # Parse character info
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
                    
                    # Check if energy regeneration info is present
                    regen_match = re.search(r'(\d+)хв до відновлення енергії', msg.text)
                    if regen_match:
                        minutes = int(regen_match.group(1))
                        self.energy_regen_time = datetime.now() + timedelta(minutes=minutes)
                    
                    logger.info(f"Character status - Level: {self.level}, "
                              f"HP: {self.current_hp}/{self.max_hp}, "
                              f"Energy: {self.current_energy}/{self.max_energy}, "
                              f"Gold: {self.gold}")
                    break
            
            # Go back to menu
            await self.human_delay(0.5, 1.0)
            await self.client.send_message(self.game_chat, "🔙 Назад")
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Error checking character status: {e}")
    
    async def parse_energy_wait_time(self, text):
        """Parse energy regeneration wait time from message"""
        match = re.search(r'відновиться через (\d+) хв', text)
        if match:
            minutes = int(match.group(1))
            return minutes * 60  # Convert to seconds
        return 300  # Default 5 minutes if can't parse
    
    async def wait_for_energy(self, wait_seconds):
        """Wait for energy regeneration with periodic status checks"""
        self.energy_regen_time = datetime.now() + timedelta(seconds=wait_seconds)
        logger.info(f"Waiting {wait_seconds} seconds for energy regeneration...")
        
        # Check status every 30 seconds to detect manual potion usage
        check_interval = self.config.ENERGY_STATUS_CHECK_INTERVAL
        elapsed = 0
        
        while elapsed < wait_seconds:
            # Wait for the smaller of remaining time or check interval
            wait_time = min(check_interval, wait_seconds - elapsed)
            await asyncio.sleep(wait_time)
            elapsed += wait_time
            
            # Check character status to see if energy was restored manually
            if elapsed % check_interval == 0 and elapsed < wait_seconds:
                logger.info("Checking if energy was restored manually...")
                await self.check_character_status()
                
                # If we have energy now, stop waiting
                if self.current_energy > 0:
                    logger.info(f"Energy restored! Current: {self.current_energy}/{self.max_energy}")
                    self.energy_regen_time = None
                    return
                
            # Log remaining time
            remaining = wait_seconds - elapsed
            if remaining > 0 and elapsed % 60 == 0:
                logger.info(f"Still waiting {int(remaining)} seconds for energy...")
        
        # Final buffer
        await asyncio.sleep(5)
        self.current_energy = 1  # We'll have at least 1 energy after wait
        self.energy_regen_time = None
    
    async def main_loop(self):
        """Main loop with better state tracking"""
        consecutive_failures = 0
        
        while self.is_running:
            try:
                # Check if we're still waiting for energy
                if self.energy_regen_time and datetime.now() < self.energy_regen_time:
                    wait_time = (self.energy_regen_time - datetime.now()).total_seconds()
                    if wait_time > 0:
                        # Check if energy was restored manually
                        await self.check_character_status()
                        if self.current_energy > 0:
                            logger.info(f"Energy already restored! Current: {self.current_energy}/{self.max_energy}")
                            self.energy_regen_time = None
                        else:
                            logger.info(f"Still waiting {int(wait_time)} seconds for energy...")
                            await asyncio.sleep(min(wait_time + 5, 60))
                        continue
                
                # Check HP - need at least 80% HP to fight safely
                hp_percentage = (self.current_hp / self.max_hp) * 100
                if hp_percentage < 80:
                    logger.info(f"Low HP: {self.current_hp}/{self.max_hp} ({hp_percentage:.1f}%). Waiting for regeneration...")
                    # HP regenerates ~0.6 per minute
                    hp_needed = (self.max_hp * 0.8) - self.current_hp
                    wait_minutes = 5  # Add buffer
                    logger.info(f"Waiting {wait_minutes} minutes for HP regeneration to 80%...")
                    
                    # Check status every 2 minutes to detect manual healing
                    check_interval_minutes = self.config.HP_STATUS_CHECK_INTERVAL / 60
                    elapsed_minutes = 0
                    
                    while elapsed_minutes < wait_minutes:
                        wait_time_minutes = min(check_interval_minutes, wait_minutes - elapsed_minutes)
                        await asyncio.sleep(wait_time_minutes * 60)
                        elapsed_minutes += wait_time_minutes
                        
                        # Check if HP was restored manually
                        await self.check_character_status()
                        hp_percentage = (self.current_hp / self.max_hp) * 100
                        
                        if hp_percentage >= 80:
                            logger.info(f"HP restored to {self.current_hp}/{self.max_hp} ({hp_percentage:.1f}%)!")
                            break
                        else:
                            remaining_minutes = wait_minutes - elapsed_minutes
                            if remaining_minutes > 0:
                                logger.info(f"HP: {self.current_hp}/{self.max_hp} ({hp_percentage:.1f}%). Still waiting {remaining_minutes} minutes...")
                    
                    continue
                
                # Check if we think we have energy
                if self.current_energy < 1:
                    # Double-check by trying to explore
                    logger.info("Energy might have regenerated, checking...")
                    self.current_energy = 1
                
                # Try to explore
                logger.info(f"Exploring... (HP: {self.current_hp}/{self.max_hp}, Energy: {self.current_energy}/{self.max_energy})")
                await self.human_delay(0.5, 1.5)  # Human decides what to do
                await self.client.send_message(self.game_chat, "🗺️ Досліджувати (⚡1)")
                
                # Wait for response
                await asyncio.sleep(2)
                
                # Get latest messages
                messages = await self.client.get_messages(self.game_chat, limit=10)
                
                # Process what happened
                battle_started = False
                energy_wait_time = 0
                exploration_successful = False
                
                for msg in messages:
                    if not msg.text:
                        continue
                    
                    # Always click first button if present
                    if msg.buttons and len(msg.buttons) > 0:
                        try:
                            await self.human_delay()  # Human reaction time
                            await msg.click(0)
                            logger.debug("Clicked button in message")
                            await asyncio.sleep(1)
                        except:
                            pass
                    
                    # Check if battle started
                    if "З'явився" in msg.text:
                        battle_started = True
                        exploration_successful = True
                        # Try to parse initial HP from battle start message
                        if "Ваші характеристики:" in msg.text:
                            hp_match = re.search(r'Здоров\'я: (\d+)/(\d+)', msg.text.split('Ваші характеристики:')[1])
                            if hp_match:
                                self.current_hp = int(hp_match.group(1))
                                self.max_hp = int(hp_match.group(2))
                                logger.info(f"Battle started! Current HP: {self.current_hp}/{self.max_hp}")
                        # Special case: wooden chest (weak enemy)
                        if "📦🪵 Дерев'яна Скринька" in msg.text:
                            logger.info("Fighting wooden chest - easy target")
                        break
                    
                    # Check for no energy
                    elif "Недостатньо енергії" in msg.text:
                        logger.info("Out of energy")
                        self.current_energy = 0
                        # Parse wait time
                        energy_wait_time = await self.parse_energy_wait_time(msg.text)
                        break
                    
                    # Check for low health
                    elif "замало здоров'я" in msg.text:
                        logger.info("Not enough health to explore")
                        self.current_hp = int(self.max_hp * 0.15)  # Assume ~15% HP
                        break
                    
                    # Greeting other players (costs energy!)
                    elif "Ви привітали" in msg.text or "подорожує поруч" in msg.text:
                        logger.info(f"Greeted another player: {msg.text[:80]}...")
                        exploration_successful = True
                        self.current_energy = max(0, self.current_energy - 1)
                        break
                    
                    # Other exploration results
                    elif any(phrase in msg.text for phrase in ["Ви помітили", "Ви натрапили", 
                                                               "Ви відкрили", "Ви виявили", "Ви чуєте",
                                                               "Ви знайшли", "знайшли"]):
                        logger.info(f"Exploration result: {msg.text[:80]}...")
                        exploration_successful = True
                        self.current_energy = max(0, self.current_energy - 1)
                        # Check for energy gain
                        if "+2 ⚡ енергія" in msg.text:
                            self.current_energy = min(self.max_energy, self.current_energy + 2)
                            logger.info(f"Gained 2 energy! Current: {self.current_energy}/{self.max_energy}")
                        break
                    
                    # Special case: bee sting
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
                    # Handle battle - it will update our HP
                    final_hp = await self.handle_battle_simplified()
                    self.current_hp = final_hp
                    self.current_energy = max(0, self.current_energy - 1)
                    consecutive_failures = 0
                elif energy_wait_time > 0:
                    # Wait for energy regeneration
                    await self.wait_for_energy(energy_wait_time)
                    consecutive_failures = 0
                elif exploration_successful:
                    # Successful exploration without battle
                    consecutive_failures = 0
                else:
                    # Something went wrong, might be in wrong state
                    consecutive_failures += 1
                    if consecutive_failures > 3:
                        logger.warning("Multiple failures, checking character status...")
                        await self.check_character_status()
                        consecutive_failures = 0
                
                # Small delay before next iteration
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(10)
    
    async def handle_battle_simplified(self):
        """Simplified battle handler - just keep attacking"""
        try:
            battle_ended = False
            rounds = 0
            final_hp = self.current_hp
            last_round_time = datetime.now()
            
            while not battle_ended and rounds < 20:
                rounds += 1
                
                # Dynamic delay based on time since last round
                time_since_last = (datetime.now() - last_round_time).total_seconds()
                if time_since_last < self.config.BATTLE_DELAY:
                    await asyncio.sleep(self.config.BATTLE_DELAY - time_since_last)
                
                # Get latest messages
                messages = await self.client.get_messages(self.game_chat, limit=5)
                
                clicked_this_round = False
                
                for msg in messages:
                    if not msg.text:
                        continue
                    
                    # Check if battle ended
                    if "Ви отримали:" in msg.text:
                        battle_ended = True
                        rewards = self.parser.parse_battle_rewards(msg.text)
                        if rewards:
                            if 'gold' in rewards:
                                self.gold += rewards['gold']
                            if 'items' in rewards:
                                for item in rewards.get('items', []):
                                    if "🏺 Стародавня Реліквія" in item:
                                        logger.info("🏺 Found Ancient Relic!")
                            logger.info(f"Battle won! Rewards: {rewards}")
                        
                        # Try to get final HP from previous messages
                        for prev_msg in messages:
                            if prev_msg.text and "Раунд" in prev_msg.text and "👤 Ви" in prev_msg.text:
                                hp_match = re.search(r'👤 Ви \((\d+)/(\d+)\)', prev_msg.text)
                                if hp_match:
                                    final_hp = int(hp_match.group(1))
                                    self.max_hp = int(hp_match.group(2))
                                    break
                        break
                    
                    elif "Ви зазнали поразки!" in msg.text:
                        battle_ended = True
                        logger.warning("Battle lost!")
                        final_hp = 1  # Game sets HP to 1 after defeat
                        break
                    
                    # Check for enemy flee
                    elif "занудьгував і втік" in msg.text:
                        battle_ended = True
                        logger.info("Enemy fled!")
                        break
                    
                    # Check for level up
                    elif "Рівень підвищено!" in msg.text:
                        level_match = re.search(r'(\d+) → (\d+)', msg.text)
                        if level_match:
                            self.level = int(level_match.group(2))
                            logger.info(f"🎉 Level up! Now level {self.level}")
                    
                    # Find the most recent battle round message with buttons
                    elif msg.buttons and "Раунд" in msg.text and not clicked_this_round:
                        # Parse current HP from round
                        hp_match = re.search(r'👤 Ви \((\d+)/(\d+)\)', msg.text)
                        if hp_match:
                            final_hp = int(hp_match.group(1))
                            self.max_hp = int(hp_match.group(2))
                            logger.debug(f"Round {rounds}: HP {final_hp}/{self.max_hp}")
                        
                        # Click attack button (index 0)
                        try:
                            await self.human_delay(1.0, 2.5)  # Human thinking time in battle
                            await msg.click(0)
                            logger.debug(f"Clicked attack in round {rounds}")
                            clicked_this_round = True
                            last_round_time = datetime.now()
                        except Exception as e:
                            logger.error(f"Failed to click battle button: {e}")
                        break
                
                # If no button was clicked this iteration, wait a bit more
                if not clicked_this_round and not battle_ended:
                    await asyncio.sleep(1)
            
            logger.info(f"Battle ended after {rounds} rounds. Final HP: {final_hp}/{self.max_hp}")
            return final_hp
            
        except Exception as e:
            logger.error(f"Error in battle: {e}")
            return self.current_hp
    
    async def stop(self):
        """Stop the bot"""
        self.is_running = False
        logger.info("Bot stopped")
