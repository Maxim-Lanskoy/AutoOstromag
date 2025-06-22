//
//  🤖 Ostromag.swift
//  👩🏼‍🔬 Auto Ostromag
//
//  Created by ⛩️ Karl Shinobi on 07.06.2025.
//
//  Architecture: Each OstromagBot instance has its own GameState actor
//  that tracks player stats and game state in a thread-safe way.
//

import Foundation
import SwiftDotenv
import ArgumentParser
@preconcurrency import TDLibKit

fileprivate let isTest: Bool = true
internal let ownerId:    Int64 = 327887608
internal let ostromagId: Int64 = 7841884680
internal let beeHunters: Int64 = -1002850991157

@main private struct Ostromag: AsyncParsableCommand {
    
    static fileprivate let configuration = CommandConfiguration(
        commandName: "AutoOstromag",
        abstract: "A Telegram user-bot for automating the Ostromag game.",
        discussion: "Automatically explores, fights enemies, and manages resources in the game."
    )
    
    @Option(name: .shortAndLong, help: "Path to the .env file")
    private var envFile: String?
            
    mutating fileprivate func run() async throws {
        // Determine the .env file path
        let envPath: String
        
        if let customPath = self.envFile {
            envPath = customPath
            print("📁 Using custom .env file: \(envPath)")
        } else {
            // Default path
            let this: [Substring] = #file.split(separator: "/")
            let array:  [String]  = this.map({String($0)}).dropLast()
            let filePath: String  = array.joined(separator: "/")
            let prefix: String    = isTest ? "/Users/maximlanskoy/" : "/home/rpi5/"
            envPath = prefix + filePath + "/.env"
            print("📁 Using default .env file: \(envPath)")
        }
        
        // Check if the .env file exists
        if !FileManager.default.fileExists(atPath: envPath) {
            print("⚠️ Warning: .env file not found at \(envPath)")
            print("💡 You can specify a custom path with --env-file option")
            print("💡 Or you'll be prompted to enter credentials manually")
        }
        
        let bot = try OstromagBot(envPath: envPath)
        try await bot.start()
    }
}

class OstromagBot {
    private let manager: TDLibClientManager
    private var client: TDLibClient?
    internal let sessionName: String
    internal let gameState = GameState()
    
    fileprivate init(envPath: String) throws {
        
        // Determine session name from env file path
        let envFileName = URL(fileURLWithPath: envPath).lastPathComponent
        if envFileName.hasPrefix(".env") && envFileName != ".env" {
            // Extract suffix from .env.something -> "something"
            let suffix = String(envFileName.dropFirst(4))
            self.sessionName = suffix.isEmpty ? "Default" : suffix
        } else if envFileName == ".env" {
            self.sessionName = "Default"
        } else {
            // Use the whole filename without extension
            self.sessionName = URL(fileURLWithPath: envPath).deletingPathExtension().lastPathComponent
        }
        
        // Try to load the .env file
        if FileManager.default.fileExists(atPath: envPath) {
            try Dotenv.configure(atPath: envPath, overwrite: false)
            print("🔍 Loaded .env file from: \(envPath)")
            print("🔍 Using session name: \(self.sessionName)")
        } else {
            print("🔍 No .env file found, will prompt for credentials")
            print("🔍 Using session name: \(self.sessionName)")
        }
        
        self.manager = TDLibClientManager()
    }
    
    fileprivate func start() async throws {
        print("🚀 Starting Ostromag automation bot...")
        
        let sessionName = self.sessionName
        let gameState = self.gameState
        self.client = self.manager.createClient { data, client in
            DispatchQueue.global().async {
                Task {
                    await OstromagBot.handleStaticUpdate(data: data, client: client, sessionName: sessionName, gameState: gameState)
                }
            }
        }
        
        guard let client = self.client else {
            fatalError("Client Error. Failed to create client.")
        }
        
        // Try to suppress TDLib logs
        do {
             _ = try await client.setLogStream(logStream: .logStreamFile(.init(maxFileSize: 10485760, path: "/dev/null", redirectStderr: true)))
        } catch let error {
            print("❌ Failed to set log stream: \(error)")
            fatalError("Log Stream Error: \(error)")
        }
        
        try await self.authenticateIfNeeded(client: client)
        
        print("✅ Bot authenticated successfully!")
        
        let me = try await client.getMe()
        
        let chat = try await client.createPrivateChat(force: nil, userId: me.id)
        
        await self.gameState.setReportingChat(chat.id)
                
        // Report bot startup
        await OstromagBot.reportAction(
            GameAction.botStarted(session: self.sessionName), 
            client: client, 
            gameState: self.gameState
        )
        
        // Report authentication success
        await OstromagBot.reportAction(
            GameAction.authenticated(), 
            client: client, 
            gameState: self.gameState
        )
        
        print("🎮 Bot initialized. Waiting for /start command...")
        
        await self.runGameLoop()
    }
                
    private func runGameLoop() async {
        print("🎮 Game automation ready. Send /start to begin.")
        
        guard let client = self.client else {
            print("❌ No client available for game loop")
            return
        }
        
        while true {
            do {
                // Only process if bot is running
                if await gameState.isRunning() {
                    // Initial status check if just started
                    let currentState = await gameState.playState
                    if currentState == .idle {
                        await OstromagBot.sendStaticInlineButton(client: client, chatId: ostromagId, text: "🧍 Персонаж")
                        try? await Task.sleep(seconds: 3) // Wait for response
                        
                        // Report initial status
                        await OstromagBot.reportActionWithLevel(
                            GameAction.initialStatus(), 
                            client: client, 
                            gameState: self.gameState
                        )
                        
                        // Set to exploring state
                        _ = await gameState.setPlayState(.exploring)
                    }
                    
                    // Check if waiting for energy
                    if let seconds = await gameState.secondsUntilEnergy() {
                        print("⏳ Waiting \(seconds) seconds for energy...")
                        try await Task.sleep(seconds: UInt64(min(seconds + 5, 300)))
                        
                        // Check status after waiting
                        await OstromagBot.sendStaticInlineButton(client: client, chatId: ostromagId, text: "🧍 Персонаж")
                        try? await Task.sleep(seconds: 2)
                        
                        // Report energy restored if we can explore now
                        if await gameState.canExplore() {
                            await OstromagBot.reportActionWithLevel(
                                GameAction.energyRestored(), 
                                client: client, 
                                gameState: self.gameState
                            )
                        }
                        continue
                    }
                    
                    // If ready to explore, send command
                    if await gameState.canExplore() {
                        print("🗺️ Sending explore command...")
                        await OstromagBot.sendStaticInlineButton(client: client, chatId: ostromagId, text: "🗺️ Досліджувати (⚡1)")
                    }
                    
                    // Wait before next check
                    try await Task.sleep(seconds: 30)
                } else {
                    // Bot is stopped, wait longer
                    try await Task.sleep(seconds: 60)
                }
                
            } catch {
                print("❌ Error in game loop: \(error)")
                try? await Task.sleep(seconds: 10)
            }
        }
    }
}
