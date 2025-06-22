//
//  📮 Handlers.swift
//  👩🏼‍🔬 Auto Ostromag
//
//  Created by ⛩️ Karl Shinobi on 07.06.2025.
//

import TDLibKit
import Foundation

internal extension OstromagBot {
    
    static func handleStaticUpdate(data: Data, client: TDLibClient, sessionName: String, gameState: GameState) async {
        do {
            let update = try client.decoder.decode(Update.self, from: data)
            
            switch update {
            case .updateNewMessage(let newMessage):
                await self.handleStaticGameMessage(message: newMessage.message, client: client, gameState: gameState)
            default:
                break
            }
        } catch {
            print("❌ Error handling update: \(error)")
        }
    }
    
    static private func handleStaticGameMessage(message: Message, client: TDLibClient, gameState: GameState) async {
        guard let chat = try? await client.getChat(chatId: message.chatId) else {
            return
        }
                
        // Only process messages from the game channel, not from reporting channel
        guard chat.id == ostromagId else {
            return
        }
        
        guard case .messageText(let textContent) = message.content else {
            return
        }
        
        let text = textContent.text.text
        print("📨 Game message: \(text)")
        
        await self.process(text: text, client: client, chatId: message.chatId, gameState: gameState)
    }
    
    static private func process(text: String, client: TDLibClient, chatId: Int64, gameState: GameState) async {
        
        // Check for bot control commands
        if text.hasPrefix("/") {
            await handleCommand(text, client: client, chatId: chatId, gameState: gameState)
            return
        }
        
        // Only process game messages if bot is running
        guard await gameState.isRunning() else { return }
        
        // Update stats if character info message
        if text.contains("⚔️") && text.contains("Рівень") && text.contains("❤️ Здоров'я:") {
            await gameState.updateFromCharacterInfo(text)
            print("📊 Updated player stats")
        }
        
        // Update health from various messages
        if text.contains("❤️") || text.contains("👤 Ви") || text.contains("Зілля Здоров'я") {
            await gameState.updateHealth(text)
            
            // Report health restoration
            if text.contains("здоров'я повністю відновлено") {
                await reportActionWithLevel(GameAction.healthRestored(), client: client, gameState: gameState)
            }
            
            // Report damage taken
            if let match = text.firstMatch(of: /\(-(\d+)\s*❤️\s*здоров'я\)/) {
                let damage = Int(match.1) ?? 0
                var source = "unknown"
                if text.contains("🐝") {
                    source = "bee sting"
                }
                await reportActionWithLevel(GameAction.damageTaken(damage, source: source), client: client, gameState: gameState)
            }
            
            // Report potion use
            if text.contains("Зілля Здоров'я") && text.contains("Використано") {
                if let match = text.firstMatch(of: /Відновлено\s*(\d+)\s*здоров'я/) {
                    let amount = Int(match.1) ?? 0
                    let potionType = text.contains("Велике") ? "Large Health Potion" : "Health Potion"
                    await reportActionWithLevel(GameAction.usedItem(potionType, effect: "+\(amount) HP"), client: client, gameState: gameState)
                }
            }
        }
        
        // Update energy from various messages
        if text.contains("енергі") || text.contains("⚡") {
            await gameState.updateEnergy(text)
            
            // Report energy potion use
            if text.contains("зілля енергії") && text.contains("Використано") {
                if let match = text.firstMatch(of: /Відновлено\s*(\d+)\s*енергії/) {
                    let amount = Int(match.1) ?? 0
                    let potionType = text.contains("Мале") ? "Small Energy Potion" : "Energy Potion"
                    await reportActionWithLevel(GameAction.usedItem(potionType, effect: "+\(amount) Energy"), client: client, gameState: gameState)
                }
            }
        }
        
        // Check for level up
        if text.contains("Рівень підвищено") {
            let oldLevel = await gameState.level
            await gameState.updateLevel(text)
            let newLevel = await gameState.level
            if oldLevel != newLevel {
                // Level up is important - always report
                await reportActionWithLevel(GameAction.levelUp(from: oldLevel, to: newLevel), client: client, gameState: gameState, isImportant: true)
            }
        }
        
        // Add human-like delay
        try? await Task.sleep(seconds: 1)
        
        // Check for energy shortage
        if text.contains("❌ Недостатньо енергії!") {
            // Extract wait time: "Наступне очко відновиться через 4 хв."
            if let match = text.firstMatch(of: /через\s*(\d+)\s*хв/) {
                let minutes = Int(match.1) ?? 5
                await gameState.setEnergyWait(minutes: minutes)
                
                // Track state change
                let stateChange = await gameState.setPlayState(.waitingEnergy)
                if stateChange.changed {
                    await reportActionWithLevel(GameAction.stateChanged(from: stateChange.from.rawValue, to: stateChange.to.rawValue), client: client, gameState: gameState)
                }
                
                print("⚡ No energy - waiting \(minutes) minutes...")
                await reportActionWithLevel(GameAction.noEnergy(minutes: minutes), client: client, gameState: gameState)
            }
            return
        }
        
        // Battle detection
        if text.contains("З'явився") && (text.contains("🐗") || text.contains("🐍") || 
           text.contains("🐺") || text.contains("🦂") || text.contains("🐻") || text.contains("📦") ||
           text.contains("🦇") || text.contains("🦜")) {
            await gameState.startBattle()
            
            // Track state change
            let stateChange = await gameState.setPlayState(.inBattle)
            if stateChange.changed {
                await reportActionWithLevel(GameAction.stateChanged(from: stateChange.from.rawValue, to: stateChange.to.rawValue), client: client, gameState: gameState)
            }
            
            // Extract enemy name
            var enemy = "Unknown enemy"
            if let match = text.firstMatch(of: /З'явився\s+(.+?)!/) {
                enemy = String(match.1)
            }
            
            print("⚔️ Monster appeared - battle starting...")
            await reportActionWithLevel(GameAction.battleStarted(enemy), client: client, gameState: gameState)
            return
        }
        
        if text.contains("--- Раунд") {
            print("⚔️ Battle in progress...")
            return
        }
        
        // Battle victory
        if text.contains("Ви отримали:") && (text.contains("золота") || text.contains("досвіду")) {
            await gameState.endBattle()
            
            // Track state change
            let stateChange = await gameState.setPlayState(.exploring)
            if stateChange.changed {
                await reportActionWithLevel(GameAction.stateChanged(from: stateChange.from.rawValue, to: stateChange.to.rawValue), client: client, gameState: gameState)
            }
            
            // Extract rewards
            var gold = 0
            var exp = 0
            if let goldMatch = text.firstMatch(of: /💰\s*(\d+)\s*золота/) {
                gold = Int(goldMatch.1) ?? 0
            }
            if let expMatch = text.firstMatch(of: /⭐\s*(\d+)\s*досвіду/) {
                exp = Int(expMatch.1) ?? 0
            }
            
            await gameState.updateBattleRewards(text)
            print("🏆 Battle won!")
            // Battle victory is important - always report
            await reportActionWithLevel(GameAction.battleWon(gold: gold, exp: exp), client: client, gameState: gameState, isImportant: true)
            
            // Continue exploring if ready
            if await gameState.canExplore() {
                try? await Task.sleep(seconds: 2)
                await self.sendStaticInlineButton(client: client, chatId: chatId, text: "🗺️ Досліджувати (⚡1)")
            }
            return
        }
        
        // Exploration events - continue exploring
        if text.contains("🕯️") || text.contains("🐝") || text.contains("🔍") || 
           text.contains("📖") || text.contains("🗿") || text.contains("🤝") || 
           text.contains("🗺️") || text.contains("🌸") || text.contains("🐣") ||
           text.contains("🗺️") || text.contains("📜") || text.contains("🗣️") ||
           text.contains("🍀") || text.contains("💸") {
            print("🎯 Found something during exploration")
            
            // Extract event description
            var eventDesc = "exploration event"
            if text.contains("🌸") {
                eventDesc = "mysterious garden"
            } else if text.contains("🕯️") {
                eventDesc = "ancient altar"
            } else if text.contains("🗿") {
                eventDesc = "strange monument"
            } else if text.contains("🐣") {
                eventDesc = "mysterious footprints"
            } else if text.contains("📜") {
                eventDesc = "ancient runes"
            } else if text.contains("🗣️") {
                eventDesc = "cave echo"
            } else if text.contains("🍀") {
                eventDesc = "lucky coin"
            } else if text.contains("💸") {
                eventDesc = "meditation spot"
            }
            
            await reportActionWithLevel(GameAction.foundEvent(eventDesc), client: client, gameState: gameState)
            
            if await gameState.canExplore() {
                try? await Task.sleep(seconds: 1)
                await self.sendStaticInlineButton(client: client, chatId: chatId, text: "🗺️ Досліджувати (⚡1)")
            }
            return
        }
        
        // Greetings
        if text.contains("👋") {
            if text.contains("Ви привітали") {
                // We greeted someone
                if let match = text.firstMatch(of: /привітали\s+(.+?)!/) {
                    let player = String(match.1)
                    await reportActionWithLevel(GameAction.greeted(player), client: client, gameState: gameState)
                }
            } else if text.contains("привітав вас") {
                // Someone greeted us - just log it
                print("👋 Player greeting - ignoring")
            }
            return
        }
        
        // "Not in battle" message - ignore
        if text.contains("Ви не перебуваєте в бою") {
            print("🙅 Not in battle - ignoring")
            return
        }
        
        // Check for item findings
        if text.contains("🔍 Ви знайшли") {
            if let match = text.firstMatch(of: /знайшли\s+(.+?)!/) {
                let item = String(match.1)
                // Item findings are important - always report
                await reportActionWithLevel(GameAction.foundItem(item), client: client, gameState: gameState, isImportant: true)
            }
        }
        
        // Check for items found after battle
        if text.contains("Знайдені предмети:") {
            let lines = text.split(separator: "\n")
            for line in lines {
                if !line.contains("Знайдені") && !line.contains("Ви отримали") && line.count > 3 {
                    // Item findings are important - always report
                    await reportActionWithLevel(GameAction.foundItem(String(line)), client: client, gameState: gameState, isImportant: true)
                }
            }
        }
        
        // Default: try to explore if no specific event
        let canExplore = await gameState.canExplore()
        if !text.contains("❌") && !text.contains("---") {
            if canExplore {
                // Track state change to exploring
                let stateChange = await gameState.setPlayState(.exploring)
                if stateChange.changed {
                    await reportActionWithLevel(GameAction.stateChanged(from: stateChange.from.rawValue, to: stateChange.to.rawValue), client: client, gameState: gameState)
                }
                
                print("🗺️ Continuing exploration...")
                await reportActionWithLevel(GameAction.explored(), client: client, gameState: gameState)
                await self.sendStaticInlineButton(client: client, chatId: chatId, text: "🗺️ Досліджувати (⚡1)")
            } else {
                // Check why we can't explore
                let health = await gameState.health
                let healthPercent = health.max > 0 ? Double(health.current) * 100 / Double(health.max) : 0
                if healthPercent < 90 {
                    // Track state change to waiting for health
                    let stateChange = await gameState.setPlayState(.waitingHealth)
                    if stateChange.changed {
                        await reportActionWithLevel(GameAction.stateChanged(from: stateChange.from.rawValue, to: stateChange.to.rawValue), client: client, gameState: gameState)
                    }
                    
                    print("💔 Health too low to explore")
                    await reportActionWithLevel(GameAction.lowHealth(), client: client, gameState: gameState)
                }
            }
        }
    }
}

// MARK: - Command Handler

extension OstromagBot {
    
    static func handleCommand(_ text: String, client: TDLibClient, chatId: Int64, gameState: GameState) async {
        let command = text.lowercased().trimmingCharacters(in: .whitespaces)
        
        switch command {
        case "/start":
            await gameState.startBot()
            print("🎮 Bot started by command")
            await reportAction(GameAction.botStarted(session: "Manual"), client: client, gameState: gameState)
            
        case "/stop":
            await gameState.stopBot()
            print("🛑 Bot stopped by command")
            await reportAction(GameAction.botStopped(), client: client, gameState: gameState)
            
        case "/log all":
            await gameState.setLogLevel(.all)
            await reportAction("📝 Logging level set to: ALL", client: client, gameState: gameState)
            
        case "/log important":
            await gameState.setLogLevel(.important)
            await reportAction("📝 Logging level set to: IMPORTANT only", client: client, gameState: gameState)
            
        case "/status":
            await reportAction(GameAction.initialStatus(), client: client, gameState: gameState)
            
        case "/help":
            let help = """
            🤖 Bot Commands:
            /start - Start bot automation
            /stop - Stop bot automation
            /status - Show current status
            /log all - Log all actions
            /log important - Log only important actions
            /help - Show this help
            """
            await sendMessage(client: client, chatId: gameState.reportingChat, text: help)
            
        default:
            if command.hasPrefix("/") {
                await sendMessage(client: client, chatId: gameState.reportingChat, text: "⚠️ Unknown command. Use /help for available commands.")
            }
        }
    }
}
