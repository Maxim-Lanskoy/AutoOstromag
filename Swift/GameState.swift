//
//  🎮 GameState.swift
//  👩🏼‍🔬 Auto Ostromag
//
//  Created by ⛩️ Karl Shinobi on 08.06.2025.
//

import Foundation

/// Thread-safe actor for game state
actor GameState {
    
    // Logging level
    enum LogLevel: String {
        case all = "all"
        case important = "important"
    }
    
    // Bot operation state
    enum BotState: String {
        case stopped = "stopped"
        case running = "running"
    }
    
    // Game play state
    enum PlayState: String {
        case idle = "idle"
        case exploring = "exploring"
        case inBattle = "in_battle"
        case waitingEnergy = "waiting_energy"
        case waitingHealth = "waiting_health"
    }
    
    private(set) var reportingChat: Int64 = 327887608
    
    // Current player stats
    private(set) var health: (current: Int, max: Int) = (0, 0)
    private(set) var energy: (current: Int, max: Int) = (0, 0)
    private(set) var level: Int = 0
    private(set) var gold: Int = 0
    private(set) var experience: (current: Int, max: Int) = (0, 0)
    private(set) var name: String = "Unknown"
    
    // Current states
    private(set) var botState: BotState = .stopped
    private(set) var playState: PlayState = .idle
    private(set) var logLevel: LogLevel = .all
    private(set) var energyWaitUntil: Date?
    
    // State tracking for change detection
    private var lastPlayState: PlayState = .idle
    
    // Bot control methods
    func startBot() {
        botState = .running
        playState = .idle
    }
    
    func stopBot() {
        botState = .stopped
        playState = .idle
    }
    
    func setLogLevel(_ level: LogLevel) {
        logLevel = level
    }
    
    // Play state management
    func setPlayState(_ newState: PlayState) -> (changed: Bool, from: PlayState, to: PlayState) {
        let oldState = playState
        if oldState != newState {
            lastPlayState = oldState
            playState = newState
            return (true, oldState, newState)
        }
        return (false, oldState, newState)
    }
    
    func isRunning() -> Bool {
        return botState == .running
    }
    
    // Update from character info message
    func updateFromCharacterInfo(_ text: String) {
        // Extract name: "⚔️ Karl {🌪️}{🐊} Shinobi - Рівень 8"
        if let match = text.firstMatch(of: /⚔️\s*(.+?)\s*-\s*Рівень\s*(\d+)/) {
            // Clean up the name by removing emoji tags
            var cleanName = String(match.1).trimmingCharacters(in: .whitespaces)
            cleanName = cleanName.replacingOccurrences(of: #"\{[^}]+\}"#, with: "", options: .regularExpression)
            name = cleanName.trimmingCharacters(in: .whitespaces)
            level = Int(match.2) ?? 0
        }
        
        // "❤️ Здоров'я: 233/307"
        if let match = text.firstMatch(of: /❤️\s*Здоров'я:\s*(\d+)\/(\d+)/) {
            health = (Int(match.1) ?? 0, Int(match.2) ?? 0)
        }
        
        // "⚡ Енергія: 2/10"
        if let match = text.firstMatch(of: /⚡\s*Енергія:\s*(\d+)\/(\d+)/) {
            energy = (Int(match.1) ?? 0, Int(match.2) ?? 0)
        }
        
        // "💰 Золото: 277"
        if let match = text.firstMatch(of: /💰\s*Золото:\s*(\d+)/) {
            gold = Int(match.1) ?? 0
        }
        
        // "✨ Досвід: 393/1500"
        if let match = text.firstMatch(of: /✨\s*Досвід:\s*(\d+)\/(\d+)/) {
            experience = (Int(match.1) ?? 0, Int(match.2) ?? 0)
        }
    }
    
    // Update health from various messages
    func updateHealth(_ text: String) {
        let oldHealth = health
        
        // "❤️ Ваше здоров'я повністю відновлено. (307/307)"
        if text.contains("здоров'я повністю відновлено"),
           let match = text.firstMatch(of: /\((\d+)\/(\d+)\)/) {
            let maxHP = Int(match.2) ?? health.max
            health = (maxHP, maxHP)
        }
        
        // Battle round: "👤 Ви (193/307)"
        if let match = text.firstMatch(of: /👤\s*Ви\s*\((\d+)\/(\d+)\)/) {
            health = (Int(match.1) ?? 0, Int(match.2) ?? 0)
        }
        
        // Damage taken: "(-15 ❤️ здоров'я)"
        if let match = text.firstMatch(of: /\(-(\d+)\s*❤️\s*здоров'я\)/) {
            let damage = Int(match.1) ?? 0
            health.current = max(0, health.current - damage)
        }
        
        // Health potion: "Відновлено 33 здоров'я!"
        if text.contains("Зілля Здоров'я"),
           let match = text.firstMatch(of: /Відновлено\s*(\d+)\s*здоров'я/) {
            let restored = Int(match.1) ?? 0
            health.current = min(health.max, health.current + restored)
        }
        
        // Health from meditation: "(+10 ❤️ здоров'я)"
        if let match = text.firstMatch(of: /\(\+(\d+)\s*❤️\s*здоров'я\)/) {
            let gained = Int(match.1) ?? 0
            health.current = min(health.max, health.current + gained)
        }
        
        if oldHealth != health {
            print("❤️ Health updated: \(oldHealth.current)/\(oldHealth.max) → \(health.current)/\(health.max)")
        }
    }
    
    // Update energy from various messages
    func updateEnergy(_ text: String) {
        let oldEnergy = energy
        
        // "❌ Недостатньо енергії! У вас 0/10 очків енергії."
        if let match = text.firstMatch(of: /У\s*вас\s*(\d+)\/(\d+)\s*очків\s*енергії/) {
            energy = (Int(match.1) ?? 0, Int(match.2) ?? 0)
        }
        
        // Energy potion: "Відновлено 5 енергії!"
        if text.contains("зілля енергії"),
           let match = text.firstMatch(of: /Відновлено\s*(\d+)\s*енергії/) {
            let restored = Int(match.1) ?? 0
            energy.current = min(energy.max, energy.current + restored)
            // Clear wait time if energy was restored
            energyWaitUntil = nil
        }
        
        // Energy from events: "(+2 ⚡ енергія)"
        if let match = text.firstMatch(of: /\(\+(\d+)\s*⚡\s*енергія\)/) {
            let gained = Int(match.1) ?? 0
            energy.current = min(energy.max, energy.current + gained)
        }
        
        if oldEnergy != energy {
            print("⚡ Energy updated: \(oldEnergy.current)/\(oldEnergy.max) → \(energy.current)/\(energy.max)")
        }
    }
    
    // Set energy wait time
    func setEnergyWait(minutes: Int) {
        energy.current = 0
        energyWaitUntil = Date().addingTimeInterval(TimeInterval(minutes * 60))
    }
    
    // Check if ready to explore
    func canExplore() -> Bool {
        let hasEnoughHealth = Double(health.current) >= Double(health.max) * 0.95
        let hasEnergy = energy.current > 0
        return hasEnoughHealth && hasEnergy && playState != .inBattle && botState == .running
    }
    
    // Battle state
    func startBattle() {
        playState = .inBattle
    }
    
    func endBattle() {
        playState = .exploring
    }
    
    // Update from battle rewards
    func updateBattleRewards(_ text: String) {
        // "💰 8 золота"
        if let match = text.firstMatch(of: /💰\s*(\d+)\s*золота/) {
            gold += Int(match.1) ?? 0
        }
        
        // "⭐ 15 досвіду"
        if let match = text.firstMatch(of: /⭐\s*(\d+)\s*досвіду/) {
            experience.current += Int(match.1) ?? 0
        }
    }
    
    // Update level
    func updateLevel(_ text: String) {
        // "🎉 Рівень підвищено! 🎉\n5 → 6"
        if text.contains("Рівень підвищено"),
           let match = text.firstMatch(of: /(\d+)\s*→\s*(\d+)/) {
            level = Int(match.2) ?? level
            print("🎆 Level up! \(match.1) → \(match.2)")
        }
        
        // Also update max health if it changed
        if text.contains("❤️ Здоров'я: +"),
           let match = text.firstMatch(of: /❤️\s*Здоров'я:\s*\+(\d+)/) {
            let increase = Int(match.1) ?? 0
            health.max += increase
            health.current = health.max // Level up restores health
        }
    }
    
    // Get seconds until energy available
    func secondsUntilEnergy() -> Int? {
        guard let waitUntil = energyWaitUntil else { return nil }
        let seconds = Int(waitUntil.timeIntervalSinceNow)
        return seconds > 0 ? seconds : nil
    }
    
    // Get formatted status string
    func getStatusString() -> String {
        let healthPercent = health.max > 0 ? Int(Double(health.current) * 100 / Double(health.max)) : 0
        let expPercent = experience.max > 0 ? Int(Double(experience.current) * 100 / Double(experience.max)) : 0
        
        var status = "🔹 \(name) (Lvl \(level))\n"
        status += "❤️ \(health.current)/\(health.max) (\(healthPercent)%) | "
        status += "⚡ \(energy.current)/\(energy.max)\n"
        status += "✨ \(experience.current)/\(experience.max) (\(expPercent)%)\n"
        
        // Add bot state if stopped
        if botState == .stopped {
            status += "🛑 Bot stopped"
            return status
        }
        
        // Add play state
        switch playState {
        case .idle:
            status += "💬 Waiting for command"
        case .exploring:
            status += "✅ Ready to explore"
        case .inBattle:
            status += "⚔️ In battle"
        case .waitingEnergy:
            if let seconds = secondsUntilEnergy() {
                let minutes = seconds / 60
                let secs = seconds % 60
                status += "⏳ Energy in \(minutes)m \(secs)s"
            } else {
                status += "⏳ Waiting for energy"
            }
        case .waitingHealth:
            status += "💤 Waiting for health"
        }
        
        return status
    }
    
    // Set reporting chat
    func setReportingChat(_ chatId: Int64) {
        reportingChat = chatId
    }
}
