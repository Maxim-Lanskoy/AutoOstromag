//
//  Ostromag.swift
//  Auto Ostromag
//
//  Created by LLabs Tech on 07.06.2025.
//

import Foundation
import SwiftDotenv
import ArgumentParser
@preconcurrency import TDLibKit

fileprivate let isTest: Bool = true
internal let ostromagId: Int64 = 7841884680

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
        
        self.client = self.manager.createClient { data, client in
            DispatchQueue.global().async {
                Task {
                    await OstromagBot.handleStaticUpdate(data: data, client: client)
                }
            }
        }
        
        guard let client = self.client else {
            fatalError("Client Error. Failed to create client.")
        }
        
        try await self.authenticateIfNeeded(client: client)
        
        print("✅ Bot authenticated successfully!")
        print("🎮 Starting game automation...")
        
        await self.runGameLoop()
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
