//
//  TGActions.swift
//  Auto Ostromag
//
//  Created by LLabs Tech on 07.06.2025.
//

import TDLibKit
import Foundation

internal extension OstromagBot {
    
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
