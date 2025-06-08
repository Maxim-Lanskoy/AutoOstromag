//
//  ♻️ StateMachine.swift
//  👩🏼‍🔬 Auto Ostromag
//
//  Created by ⛩️ Karl Shinobi on 07.06.2025.
//

// This file defines the different states of the gameplay.
internal struct State: Codable {
    
    // Game state properties
    public var currentHealth: Int  /* --- | */
    public var totalHealth:   Int  /* - - | */
    public var currentEnergy: Int  /* --- | */
    public var maxEnergy:     Int  /* - - | */
                                   /* --- | */
    // Player stats                /* - - | */
    public var damage:         Int  /* -- | */
    public var defence:         Int  /* - | */
    public var power:            Int  /*  | */
    public var currentExperience: Int  /* | */
    public var totalExperience:   Int  /* | */
    public var gold:              Int  /* | */
    public var dailyEnergy:       Int  /* | */
    
    // Game state
    public var gameState: GamePlayState = .waitingForStart
    
    // Initializer with GamePlayState
    public init(_ state: GamePlayState) {
        self.currentHealth = 0
        self.totalHealth   = 0
        self.currentEnergy = 0
        self.maxEnergy     = 0
        
        // Player stats
        self.damage         = 0
        self.defence         = 0
        self.power            = 0
        self.currentExperience = 0
        self.totalExperience   = 0
        self.gold              = 0
        self.dailyEnergy       = 0
        self.gameState     = state
    }
    
    // Initializer with health and energy
    public init(currentHealth: Int, totalHealth: Int, currentEnergy: Int, _ state: GamePlayState) {
        self.currentHealth = currentHealth
        self.totalHealth   = totalHealth
        self.currentEnergy = currentEnergy
        self.gameState     = state
        self.maxEnergy     = 0
        
        // Player stats
        self.damage         = 0
        self.defence         = 0
        self.power            = 0
        self.currentExperience = 0
        self.totalExperience   = 0
        self.gold              = 0
        self.dailyEnergy       = 0
    }
    
    // Convenience initializer with default values
    public init(currentHealth: Int, totalHealth: Int, currentEnergy: Int, damage: Int, defence: Int, power: Int, gold: Int,
                currentExperience: Int, totalExperience: Int, maxEnergy: Int, dailyEnergy: Int, gameState: GamePlayState) {
        self.currentHealth = currentHealth; self.totalHealth = totalHealth
        self.currentEnergy = currentEnergy;  self.maxEnergy  =  maxEnergy
        self.damage = damage; self.defence = defence; self.power = power
        self.currentExperience = currentExperience
        self.totalExperience = totalExperience
        self.dailyEnergy = dailyEnergy
        self.gameState = gameState
        self.gold = gold
    }
}

// Represents the different states of the game play
enum GamePlayState: String, Codable, CaseIterable {
    
    case waitingForStart
    
    case exploring
    
    case battle
    
    case waitingEnergy
    
    case waitingHealth
    
}
