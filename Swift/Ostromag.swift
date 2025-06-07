//
//  Ostromag.swift
//  Auto Ostromag
//
//  Created by LLabs Tech on 07.06.2025.
//

import Foundation
import SwiftDotenv
@preconcurrency import TDLibKit

struct Config: Codable {
    let api_id: String
    let api_hash: String
    let phone_number: String
}

@main
class Ostromag {
    static func main() async throws {
        let bot = try OstromagBot()
        try await bot.start()
    }
}

class OstromagBot {
    private let manager: TDLibClientManager
    private var client: TDLibClient?
    
    init() throws {
        let projectFolder: String = "/Users/maximlanskoy/AutoOstromag"
        let path: String = projectFolder + "/.env"
        try Dotenv.configure(atPath: path, overwrite: false)
        self.manager = TDLibClientManager()
    }
    
    func start() async throws {
        print("🚀 Starting Ostromag automation bot...")
        
        client = manager.createClient { data, client in
            DispatchQueue.global().async {
                Task {
                    await OstromagBot.handleStaticUpdate(data: data, client: client)
                }
            }
        }
        
        guard let client = client else {
            throw NSError(domain: "ClientError", code: 1, userInfo: [NSLocalizedDescriptionKey: "Failed to create client"])
        }
        
        try await authenticateIfNeeded(client: client)
        
        print("✅ Bot authenticated successfully!")
        print("🎮 Starting game automation...")
        
        await runGameLoop()
    }
    
    private func authenticateIfNeeded(client: TDLibClient) async throws {
        var authState = try await client.getAuthorizationState()
        
        while true {
            switch authState {
            case .authorizationStateWaitTdlibParameters:
                print("⚙️ Setting TDLib parameters...")
                
                // Try to load .env variables
                let rawAppId = Dotenv["API_ID"]?.stringValue
                let rawAppHash = Dotenv["API_HASH"]?.stringValue
                
                let tgAppId: Int
                let tgHash: String
                
                if let apiIdString = rawAppId, let apiHash = rawAppHash, !apiIdString.isEmpty, !apiHash.isEmpty, let apiId = Int(apiIdString) {
                    print("📋 Using credentials from .env file")
                    tgAppId = apiId
                    tgHash = apiHash
                } else {
                    print("📱 Enter your Telegram API ID:")
                    guard let apiIdString = readLine()?.trimmingCharacters(in: .whitespacesAndNewlines),
                          let apiIdInt = Int(apiIdString) else {
                        throw NSError(domain: "AuthError", code: 5, userInfo: [NSLocalizedDescriptionKey: "Invalid API ID"])
                    }
                    tgAppId = apiIdInt
                    print("🔑 Enter your Telegram API Hash:")
                    guard let hash = readLine()?.trimmingCharacters(in: .whitespacesAndNewlines) else {
                        throw NSError(domain: "AuthError", code: 6, userInfo: [NSLocalizedDescriptionKey: "No API Hash provided"])
                    }
                    tgHash = hash
                }
                
                // Create persistent session directory
                let sessionDir = FileManager.default.currentDirectoryPath + "/TGDB/Session"
                let filesDir = FileManager.default.currentDirectoryPath + "/TGDB/Files"
                
                // Create directories if they don't exist
                try? FileManager.default.createDirectory(atPath: sessionDir, withIntermediateDirectories: true)
                try? FileManager.default.createDirectory(atPath: filesDir, withIntermediateDirectories: true)
                
                _ = try await client.setTdlibParameters(
                    apiHash: tgHash,
                    apiId: tgAppId,
                    applicationVersion: "1.0",
                    databaseDirectory: sessionDir,
                    databaseEncryptionKey: nil,
                    deviceModel: "Desktop",
                    filesDirectory: filesDir,
                    systemLanguageCode: "en",
                    systemVersion: "macOS",
                    useChatInfoDatabase: true,
                    useFileDatabase: true,
                    useMessageDatabase: true,
                    useSecretChats: false,
                    useTestDc: false
                )
                
            case .authorizationStateWaitPhoneNumber:
                // Try to load phone number from .env
                var phoneNumber: String
                
                
                if let phone = Dotenv["PHONE_NUMBER"]?.stringValue, !phone.isEmpty {
                    print("📱 Using phone number from .env: \(phone)")
                    phoneNumber = phone
                } else {
                    print("📱 Enter your phone number (with country code):")
                    guard let phone = readLine()?.trimmingCharacters(in: .whitespacesAndNewlines) else {
                        throw NSError(domain: "AuthError", code: 1, userInfo: [NSLocalizedDescriptionKey: "No phone number provided"])
                    }
                    phoneNumber = phone
                }
                
                _ = try await client.setAuthenticationPhoneNumber(phoneNumber: phoneNumber, settings: nil)
                
            case .authorizationStateWaitCode:
                print("📥 Enter the verification code:")
                guard let code = readLine()?.trimmingCharacters(in: .whitespacesAndNewlines) else {
                    throw NSError(domain: "AuthError", code: 2, userInfo: [NSLocalizedDescriptionKey: "No code provided"])
                }
                
                _ = try await client.checkAuthenticationCode(code: code)
                
            case .authorizationStateWaitPassword:
                print("🔒 2FA required. Enter your password:")
                guard let password = readLine()?.trimmingCharacters(in: .whitespacesAndNewlines) else {
                    throw NSError(domain: "AuthError", code: 3, userInfo: [NSLocalizedDescriptionKey: "No password provided"])
                }
                _ = try await client.checkAuthenticationPassword(password: password)
                
            case .authorizationStateReady:
                print("✅ Authentication complete!")
                return
                
            default:
                print("⏳ Waiting for auth state change...")
            }
            
            try await Task.sleep(nanoseconds: 1_000_000_000)
            authState = try await client.getAuthorizationState()
        }
    }
    
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
    
    
    private func runGameLoop() async {
        print("🎮 Game automation active. Listening for messages...")
        
        while true {
            do {
                try await Task.sleep(nanoseconds: 30_000_000_000)
                print("🤖 Bot is running...")
            } catch {
                print("❌ Error in game loop: \(error)")
            }
        }
    }
}
