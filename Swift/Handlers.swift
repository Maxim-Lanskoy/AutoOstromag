//
//  Handlers.swift
//  Auto Ostromag
//
//  Created by LLabs Tech on 07.06.2025.
//

import TDLibKit
import Foundation

internal extension OstromagBot {
        
    static func handleStaticUpdate(data: Data, client: TDLibClient) async {
        do {
            let update = try client.decoder.decode(Update.self, from: data)
            
            switch update {
            case .updateNewMessage(let newMessage):
                await self.handleStaticGameMessage(message: newMessage.message, client: client)
            default:
                break
            }
        } catch {
            print("❌ Error handling update: \(error)")
        }
    }
    
    static private func handleStaticGameMessage(message: Message, client: TDLibClient) async {
        guard let chat = try? await client.getChat(chatId: message.chatId), chat.id == ostromagId else {
            return
        }
        
        guard case .messageText(let textContent) = message.content else {
            return
        }
        
        let text = textContent.text.text
        print("📨 Game message: \(text)")
        
        await self.processStaticGameState(text: text, client: client, chatId: message.chatId)
    }
    
    static private func processStaticGameState(text: String, client: TDLibClient, chatId: Int64) async {
        try? await Task.sleep(nanoseconds: 2_000_000_000)
        
        // Check for energy shortage - wait longer
        if text.contains("❌ Недостатньо енергії!") {
            print("⚡ No energy - waiting 5 minutes...")
            try? await Task.sleep(nanoseconds: 300_000_000_000) // 5 minutes
            return
        }
        
        // Battle situations - just wait for auto-combat
        if text.contains("З'явився") && (text.contains("🐗") || text.contains("🐍") || text.contains("🐺") || text.contains("🦂")) {
            print("⚔️ Monster appeared - battle starting...")
            return
        }
        
        if text.contains("--- Раунд") {
            print("⚔️ Battle in progress...")
            return
        }
        
        if text.contains("Ви отримали:") && text.contains("золота") {
            print("🏆 Battle won! Continuing exploration...")
            try? await Task.sleep(nanoseconds: 2_000_000_000)
            await self.sendStaticInlineButton(client: client, chatId: chatId, text: "🗺️ Досліджувати (⚡1)")
            return
        }
        
        // Exploration events - continue exploring
        if text.contains("🕯️") || text.contains("🐝") || text.contains("🔍") || text.contains("📖") || 
           text.contains("🗿") || text.contains("🤝") || text.contains("🗺️") {
            print("🎯 Found something - continuing exploration...")
            try? await Task.sleep(nanoseconds: 1_000_000_000)
            await self.sendStaticInlineButton(client: client, chatId: chatId, text: "🗺️ Досліджувати (⚡1)")
            return
        }
        
        // Greetings from other players
        if text.contains("👋") && text.contains("привітав") {
            print("👋 Player greeting detected")
            return
        }
        
        // Default exploration if no specific case
        if !text.contains("❌") && !text.contains("---") {
            print("🗺️ Default: Starting exploration...")
            await self.sendStaticInlineButton(client: client, chatId: chatId, text: "🗺️ Досліджувати (⚡1)")
        }
    }
}
