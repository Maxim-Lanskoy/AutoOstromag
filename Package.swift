// swift-tools-version: 6.1
//
//  📦 Package.swift
//  👩🏼‍🔬 Auto Ostromag
//
//  Created by ⛩️ Karl Shinobi on 07.06.2025.
//

import PackageDescription

let package = Package(
    name: "AutoOstromag",
    platforms: [
        .macOS(.v15)
    ],
    products: [
        // 🏃 The main executable for the AutoOstromag project.
        .executable(name: "AutoOstromag", targets: ["AutoOstromag"])
    ],
    dependencies: [
        // 🐦 A Swift Telegram TDLib API library.
        .package(url: "https://github.com/Swiftgram/TDLibKit.git", from: "1.5.2-tdlib-1.8.47-971684a3"),
        // 🔑 A dotenv library for Swift.
        .package(url: "https://github.com/thebarndog/swift-dotenv.git", from: "2.1.0"),
        // 🎯 Command line argument parser.
        .package(url: "https://github.com/apple/swift-argument-parser.git", from: "1.5.1")
    ],
    targets: [
        .executableTarget(name: "AutoOstromag", dependencies: [
                .product(name: "SwiftDotenv", package: "swift-dotenv"),
                .product(name: "TDLibKit", package: "TDLibKit"),
                .product(name: "ArgumentParser", package: "swift-argument-parser")
            ], path: "Swift", swiftSettings: swiftSettings
        )
    ]
)


var swiftSettings: [SwiftSetting] { [
    .enableUpcomingFeature("ExistentialAny"),
] }
