//
//  📥 Extensions.swift
//  👩🏼‍🔬 Auto Ostromag
//
//  Created by ⛩️ Karl Shinobi on 08.06.2025.
//

extension Task where Success == Never, Failure == Never {
    public static func sleep(seconds duration: UInt64) async throws {
        try await sleep(nanoseconds: 1_000_000_000 * duration)
    }
    
    public static func sleep(minutes count: UInt64) async throws {
        try await sleep(nanoseconds: 1_000_000_000 * (60 * count))
    }
    
    @available(*, deprecated, message: "Seems helpful but complicated. Use sleep(seconds:) instead.")
    public static func sleep(floatSeconds preciseDuration: Double) async throws {
        let nanosecond: Double = 1_000_000_000
        let timeInterval = preciseDuration * nanosecond
        let duration = UInt64(timeInterval)
        try await sleep(nanoseconds: duration)
    }
}
