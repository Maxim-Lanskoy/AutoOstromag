// swift-tools-version: 6.1
//
//  Package.swift
//  Auto Ostromag
//
//  Created by LLabs Tech on 07.06.2025.
//

import PackageDescription

let package = Package(
    name: "AutoOstromag",
    platforms: [
        .macOS(.v14)
    ],
    products: [
        // 🏃 The main executable for the AutoOstromag project.
        .executable(name: "AutoOstromag", targets: ["AutoOstromag"])
    ],
    dependencies: [
        // 🐦 A Swift Telegram TDLib API library.
        .package(url: "https://github.com/Swiftgram/TDLibKit", branch: "main"),
        // 🔑 A dotenv library for Swift.
        .package(url: "https://github.com/thebarndog/swift-dotenv.git", from: "2.1.0"),
    ],
    targets: [
        .executableTarget(name: "AutoOstromag", dependencies: [
                .product(name: "SwiftDotenv", package: "swift-dotenv"),
                .product(name: "TDLibKit", package: "TDLibKit")
            ], path: "Swift"
        )
    ]
)
