//
//  Handlers.swift
//  AutoOstromag
//
//  Created by Maxim Lanskoy on 07.06.2025.
//

import TDLibKit
import Foundation

internal extension OstromagBot {
        
    static func handleStaticUpdate(data: Data, client: TDLibClient) async {
        do {
            let update = try client.decoder.decode(Update.self, from: data)
            
            switch update {
            case .updateNewMessage(let newMessage):
                await handleStaticGameMessage(message: newMessage.message, client: client)
            default:
                break
            }
        } catch {
            print("❌ Error handling update: \(error)")
        }
    }
    
    static func handleStaticGameMessage(message: Message, client: TDLibClient) async {
        guard let chat = try? await client.getChat(chatId: message.chatId),
              chat.title == "Таємниці Королівства Остромаг" else {
            return
        }
        
        guard case .messageText(let textContent) = message.content else {
            return
        }
        
        let text = textContent.text.text
        print("📨 Game message: \(text)")
        
        await processStaticGameState(text: text, client: client, chatId: message.chatId)
    }
    
    static func processStaticGameState(text: String, client: TDLibClient, chatId: Int64) async {
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
            await sendStaticInlineButton(client: client, chatId: chatId, text: "🗺️ Досліджувати (⚡1)")
            return
        }
        
        // Exploration events - continue exploring
        if text.contains("🕯️") || text.contains("🐝") || text.contains("🔍") || text.contains("📖") || 
           text.contains("🗿") || text.contains("🤝") || text.contains("🗺️") {
            print("🎯 Found something - continuing exploration...")
            try? await Task.sleep(nanoseconds: 1_000_000_000)
            await sendStaticInlineButton(client: client, chatId: chatId, text: "🗺️ Досліджувати (⚡1)")
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
            await sendStaticInlineButton(client: client, chatId: chatId, text: "🗺️ Досліджувати (⚡1)")
        }
    }
    
    static func sendStaticInlineButton(client: TDLibClient, chatId: Int64, text: String) async {
        do {
            _ = try await client.sendMessage(
                chatId: chatId,
                inputMessageContent: .inputMessageText(
                    .init(
                        clearDraft: false,
                        linkPreviewOptions: nil,
                        text: .init(entities: [], text: text)
                    )
                ),
                messageThreadId: nil,
                options: nil,
                replyMarkup: nil,
                replyTo: nil
            )
            print("📤 Sent: \(text)")
        } catch {
            print("❌ Error sending message: \(error)")
        }
    }
    
    static func sendStaticFirstInlineButton(client: TDLibClient, chatId: Int64) async {
        do {
            let chatHistory = try await client.getChatHistory(
                chatId: chatId,
                fromMessageId: 0,
                limit: 1,
                offset: 0,
                onlyLocal: false
            )
            
            if let lastMessage = chatHistory.messages?.first,
               case .messageText(_) = lastMessage.content,
               let replyMarkup = lastMessage.replyMarkup,
               case .replyMarkupInlineKeyboard(let keyboard) = replyMarkup,
               let firstRow = keyboard.rows.first,
               let firstButton = firstRow.first {
                
                _ = try await client.getCallbackQueryAnswer(
                    chatId: chatId,
                    messageId: lastMessage.id,
                    payload: .callbackQueryPayloadData(.init(data: Data(firstButton.text.utf8)))
                )
                print("🔘 Pressed first button")
            }
        } catch {
            print("❌ Error pressing button: \(error)")
        }
    }
}
