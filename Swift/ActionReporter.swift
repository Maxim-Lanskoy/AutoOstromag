//
//  📢 ActionReporter.swift
//  👩🏼‍🔬 Auto Ostromag
//
//  Created by ⛩️ Karl Shinobi on 08.06.2025.
//

import TDLibKit
import Foundation

internal extension OstromagBot {
    
    /// Send action report to reporting channel
    static func reportAction(
        _ action: String,
        client: TDLibClient,
        gameState: GameState
    ) async {
        let status = await gameState.getStatusString()
        let message = "\(action)\n\n\(status)"
        
        await sendMessage(client: client, chatId: gameState.reportingChat, text: message)
    }
    
    /// Send action report with logging level check
    static func reportActionWithLevel(
        _ action: String,
        client: TDLibClient,
        gameState: GameState,
        isImportant: Bool = false
    ) async {
        let logLevel = await gameState.logLevel
        
        // Always send if logging all, or if important and logging important only
        if logLevel == .all || (logLevel == .important && isImportant) {
            await reportAction(action, client: client, gameState: gameState)
        }
    }
    
    /// Send simple message to a chat
    static func sendMessage(
        client: TDLibClient,
        chatId: Int64,
        text: String
    ) async {
        do {
            // For now, send plain text without markdown parsing
            let cleanText = text.replacingOccurrences(of: "**", with: "")
            
            _ = try await client.sendMessage(
                chatId: chatId,
                inputMessageContent: .inputMessageText(
                    .init(
                        clearDraft: false,
                        linkPreviewOptions: nil,
                        text: .init(entities: [], text: cleanText)
                    )
                ),
                messageThreadId: nil,
                options: nil,
                replyMarkup: nil,
                replyTo: nil
            )
        } catch {
            print("❌ Error sending report: \(error)")
            let me = try? await client.getMe()
            print("⚠️ Failed to send message as \(me?.firstName ?? "unknown user"), id: \(me?.id ?? 0)")
            print("📝 Message content: \(text)")
            // Optionally, log to console or file
            print("📝 Full error: \(error.localizedDescription)")
        }
    }
}

// MARK: - Action Types

struct GameAction {
    static func explored() -> String {
        "🗺️ Exploring the world"
    }
    
    static func foundItem(_ item: String) -> String {
        "🎁 Found: \(item)"
    }
    
    static func battleStarted(_ enemy: String) -> String {
        "⚔️ Battle started: \(enemy)"
    }
    
    static func battleWon(gold: Int, exp: Int) -> String {
        "🏆 Victory! +\(gold)💰 +\(exp)⭐"
    }
    
    static func levelUp(from: Int, to: Int) -> String {
        "🎉 LEVEL UP! \(from) → \(to)"
    }
    
    static func noEnergy(minutes: Int) -> String {
        "🔋 Out of energy, waiting \(minutes) minutes"
    }
    
    static func lowHealth() -> String {
        "💔 Health too low, waiting for recovery"
    }
    
    static func damageTaken(_ damage: Int, source: String) -> String {
        "🤕 Took \(damage) damage from \(source)"
    }
    
    static func healthRestored() -> String {
        "❤️‍🩹 Health fully restored!"
    }
    
    static func foundEvent(_ event: String) -> String {
        "📍 Event: \(event)"
    }
    
    static func usedItem(_ item: String, effect: String) -> String {
        "🧪 Used \(item): \(effect)"
    }
    
    static func greeted(_ player: String) -> String {
        "👋 Greeted \(player)"
    }
    
    // Technical actions
    static func botStarted(session: String) -> String {
        "🚀 Bot started (session: \(session))"
    }
    
    static func botStopped() -> String {
        "🛑 Bot stopped"
    }
    
    static func authenticated() -> String {
        "✅ Authentication successful"
    }
    
    static func stateChanged(from: String, to: String) -> String {
        "🔄 State: \(from) → \(to)"
    }
    
    static func energyRestored() -> String {
        "⚡ Energy restored, resuming exploration"
    }
    
    static func healthRecovered() -> String {
        "💚 Health recovered, resuming exploration"
    }
    
    static func initialStatus() -> String {
        "📊 Initial character status"
    }
}
