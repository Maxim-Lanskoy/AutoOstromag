//
//  📮 Handlers.swift
//  👩🏼‍🔬 Auto Ostromag
//
//  Created by ⛩️ Karl Shinobi on 07.06.2025.
//

import TDLibKit
import Foundation

internal extension OstromagBot {
        
    static func handleStaticUpdate(data: Data, client: TDLibClient) async -> State? {
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
        guard let chat = try? await client.getChat(chatId: message.chatId) else {
            print("❌ Error fetching chat for message \(message.id)")
            return
        }
                
        guard chat.id == ostromagId || chat.id == beeHunters else {
            // print("Message not from Ostromag or Bee Hunters guild chat")
            return
        }
        
        guard case .messageText(let textContent) = message.content else {
            return
        }
        
        let text = textContent.text.text
        print("📨 Game message: \(text)")
        
        await self.process(text: text, client: client, chatId: message.chatId)
    }
    
    // Represents the different states of the game play
    //      - enum GamePlayState: String
    //    case waitingForStart
    //    case exploring
    //    case battle
    //    case waitingEnergy
    //    case waitingHealth
    
    static private func process(text: String, client: TDLibClient, chatId: Int64) async {
        
        try? await Task.sleep(seconds: 1)
        
        switch ??? state.gameState {
         
        case .waitingForStart:
            print("🔄 Waiting for game to start...")
            return
            
        case .exploring:
            print("🌏 Exploring game world...")
            return
        
        case .battle:
            print("⚔️ Battle in progress...")
            return
        
        case .waitingEnergy:
            print("🔋 Waiting for energy to recharge...")
            return
        
        case .waitingHealth:
            print("💤 Waiting for game to start...")
            return
        
        }
        
        // Check for energy shortage - wait longer
        if text.contains("❌ Недостатньо енергії!") {
            print("⚡ No energy - waiting 5 minutes...")
            try? await Task.sleep(minutes: 5) // 5 minutes
        }
        
        // Battle situations - just wait for auto-combat
        if text.contains("З'явився") && (text.contains("🐗") || text.contains("🐍") || text.contains("🐺") || text.contains("🦂")) {
            print("⚔️ Monster appeared - battle starting...")
        }
        
        if text.contains("--- Раунд") {
            print("⚔️ Battle in progress...")
        }
        
        if text.contains("Ви отримали:") && text.contains("золота") {
            print("🏆 Battle won! Continuing exploration...")
            try? await Task.sleep(seconds: 2)
            await self.sendStaticInlineButton(client: client, chatId: chatId, text: "🗺️ Досліджувати (⚡1)")
        }
        
        // Exploration events - continue exploring
        if text.contains("🕯️") || text.contains("🐝") || text.contains("🔍") || text.contains("📖") || 
           text.contains("🗿") || text.contains("🤝") || text.contains("🗺️") {
            print("🎯 Found something - continuing exploration...")
            try? await Task.sleep(seconds: 1)
            await self.sendStaticInlineButton(client: client, chatId: chatId, text: "🗺️ Досліджувати (⚡1)")
        }
        
        // Greetings from other players
        if text.contains("👋") && text.contains("привітав") {
            print("👋 Player greeting detected")
        }
        
        // Default exploration if no specific case
        if !text.contains("❌") && !text.contains("---") {
            print("🗺️ Default: Starting exploration...")
            await self.sendStaticInlineButton(client: client, chatId: chatId, text: "🗺️ Досліджувати (⚡1)")
        }
    }
}
