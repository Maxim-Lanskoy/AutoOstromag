//
//  Authorise.swift
//  Auto Ostromag
//
//  Created by LLabs Tech on 07.06.2025.
//

import TDLibKit
import Foundation
import SwiftDotenv

internal extension OstromagBot {
        
    func authenticateIfNeeded(client: TDLibClient) async throws {
        var authState = try await client.getAuthorizationState()
        
        while true {
            switch authState {
            case .authorizationStateWaitTdlibParameters:
                print("⚙️ Setting TDLib parameters...")
                
                // Try to load .env variables
                let rawAppId = Dotenv.apiId?.stringValue
                let rawAppHash = Dotenv.apiHash?.stringValue
                
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
                        fatalError("Auth Error.Invalid API ID.")
                    }
                    tgAppId = apiIdInt
                    print("🔑 Enter your Telegram API Hash:")
                    guard let hash = readLine()?.trimmingCharacters(in: .whitespacesAndNewlines) else {
                        fatalError("Auth Error. No API Hash provided.")
                    }
                    tgHash = hash
                }
                
                // Create persistent session directory unique to this account
                let sessionDir = FileManager.default.currentDirectoryPath + "/TGDB_\(self.sessionName)/Session"
                let filesDir = FileManager.default.currentDirectoryPath + "/TGDB_\(self.sessionName)/Files"
                
                print("📂 Session directory: \(sessionDir)")
                print("📂 Files directory: \(filesDir)")
                
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
                
                if let phone = Dotenv.phoneNumber?.stringValue, !phone.isEmpty {
                    print("📱 Using phone number from .env: \(phone)")
                    phoneNumber = phone
                } else {
                    print("📱 Enter your phone number (with country code):")
                    guard let phone = readLine()?.trimmingCharacters(in: .whitespacesAndNewlines) else {
                        fatalError("Auth Error. No phone number provided.")
                    }
                    phoneNumber = phone
                }
                
                _ = try await client.setAuthenticationPhoneNumber(phoneNumber: phoneNumber, settings: nil)
                
            case .authorizationStateWaitCode:
                print("📥 Enter the verification code:")
                guard let code = readLine()?.trimmingCharacters(in: .whitespacesAndNewlines) else {
                    fatalError("Auth Error. No code provided.")
                }
                
                _ = try await client.checkAuthenticationCode(code: code)
                
            case .authorizationStateWaitPassword:
                print("🔒 2FA required. Enter your password:")
                guard let password = readLine()?.trimmingCharacters(in: .whitespacesAndNewlines) else {
                    fatalError("Auth Error. No password provided.")
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
}
