import asyncio
from pyrogram import Client
from pyrogram.errors import FloodWait, RPCError
from pyrogram.types import InlineKeyboardMarkup # Додано імпорт для перевірки типу клавіатури
import re # Додано імпорт для регулярних виразів
import traceback # Додано імпорт для виводу повного стеку викликів
import sys # Додано імпорт sys для налаштування кодування виводу

# Налаштування кодування виводу консолі на UTF-8 для підтримки емодзі
# Це вирішує UnicodeEncodeError на деяких системах Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Параметри API та чату бота
api_id = 22491271
api_hash = "c731b2060f7471a7b858d38cbaf93f67"
session_name = "ostro_session"
bot_chat = "ostromag_game_bot"

DELAY = 3  # Секунд між діями (загальна затримка збільшена для стабільності)

# Ініціалізація клієнта Pyrogram
app = Client(session_name, api_id=api_id, api_hash=api_hash)

async def click_button(chat_id, keyword, message_to_click_on=None, wait_after=3, retries=5, retry_delay=1, exclude_keyword=None):
    """
    Натискає кнопку, що містить задане ключове слово, у чаті.
    Може працювати з конкретним повідомленням або шукати в історії.
    Збільшено логування та обробку помилок для кращої діагностики.
    Додано механізм повторних спроб для пошуку кнопки.
    Додано параметр exclude_keyword для виключення кнопок.
    """
    await asyncio.sleep(wait_after)
    print(f"🔍 Шукаю кнопку '{keyword}' (спроба 1/{retries})...")

    for attempt in range(1, retries + 1):
        target_message = None
        if message_to_click_on:
            try:
                # Завжди намагаємося отримати найновішу версію конкретного повідомлення, якщо воно надано
                target_message = await app.get_messages(chat_id, message_to_click_on.id)
                print(f"🔄 Повідомлення (ID: {message_to_click_on.id}) оновлено для спроби {attempt}.")
            except Exception as e:
                print(f"⚠️ Помилка при оновленні повідомлення (ID: {message_to_click_on.id}): {e}. Спроба {attempt}/{retries}. Спробую пошукати в історії.")
                traceback.print_exc()
                target_message = None # Переходимо до пошуку в історії
        
        if not target_message: # Якщо конкретне повідомлення не надано або оновлення не вдалося, шукаємо в історії
            messages_to_check_in_history = []
            async for msg_hist in app.get_chat_history(chat_id, limit=20): # Збільшено ліміт для кращого шансу
                messages_to_check_in_history.append(msg_hist)
            
            for msg_hist in messages_to_check_in_history:
                if msg_hist.reply_markup and isinstance(msg_hist.reply_markup, InlineKeyboardMarkup):
                    for row in msg_hist.reply_markup.inline_keyboard:
                        for button in row:
                            button_text_stripped = button.text.lower().strip()
                            if keyword.lower().strip() in button_text_stripped:
                                if exclude_keyword and exclude_keyword.lower().strip() in button_text_stripped:
                                    continue
                                # Знайдено кнопку в історії, намагаємося натиснути
                                try:
                                    await msg_hist.click(button.text)
                                    print(f"✅ Кнопку '{button.text}' успішно натиснуто з історії.")
                                    return True
                                except FloodWait as e:
                                    print(f"⚠️ FloodWait: Зачекайте {e.value} секунд.")
                                    await asyncio.sleep(e.value + 5)
                                    return False
                                except (TimeoutError, RPCError) as e:
                                    print(f"⚠️ Помилка при натисканні '{button.text}' з історії: {e}")
                                    # Пригнічуємо трасування TimeoutError, якщо це кнопка "Так"
                                    if isinstance(e, TimeoutError) and keyword.lower().strip() == "так":
                                        print(f"ℹ️ TimeoutError для кнопки 'Так' з історії. Очікую підтвердження розбирання.")
                                    else:
                                        traceback.print_exc() # Виводимо трасування для інших помилок
                                    continue # Продовжуємо до наступної кнопки/повідомлення в історії
                                except Exception as e:
                                    print(f"⚠️ Невідома помилка при натисканні '{button.text}' з історії: {e}")
                                    traceback.print_exc()
                                    return False
            print(f"⛔ Кнопку '{keyword}' не знайдено в історії чату. Спроба {attempt}/{retries}.")
            if attempt < retries:
                await asyncio.sleep(retry_delay)
            continue # Переходимо до наступної спроби

        # Якщо у нас є дійсне target_message (оригінальне або оновлене)
        print(f"💬 Перевіряю повідомлення з InlineKeyboardMarkup (ID: {target_message.id}, Текст: '{target_message.text}')")
        for row in target_message.reply_markup.inline_keyboard:
            for button in row:
                button_text_stripped = button.text.lower().strip()
                print(f"🧩 Знайдено кнопку: '{button.text}' (очищений: '{button_text_stripped}')")
                
                if keyword.lower().strip() in button_text_stripped:
                    if exclude_keyword and exclude_keyword.lower().strip() in button_text_stripped:
                        print(f"🚫 Пропускаю кнопку '{button.text}', оскільки вона містить виключене ключове слово '{exclude_keyword}'.")
                        continue
                        
                    print(f"➡️ Натискаю: '{button.text}'")
                    try:
                        await target_message.click(button.text)
                        print(f"✅ Кнопку '{button.text}' успішно натиснуто.")
                        return True
                    except FloodWait as e:
                        print(f"⚠️ FloodWait: Зачекайте {e.value} секунд перед наступною дією.")
                        await asyncio.sleep(e.value + 5)
                        return False
                    except (TimeoutError, RPCError) as e:
                        print(f"⚠️ Помилка при натисканні '{button.text}': {e}. Спроба {attempt}/{retries}.")
                        # Пригнічуємо трасування TimeoutError, якщо це кнопка "Так"
                        if isinstance(e, TimeoutError) and keyword.lower().strip() == "так":
                            print(f"ℹ️ TimeoutError для кнопки 'Так' на останній спробі. Очікую підтвердження розбирання.")
                        else:
                            traceback.print_exc() # Виводимо трасування для інших помилок
                        
                        if attempt < retries:
                            await asyncio.sleep(retry_delay * 2) # Чекаємо довше перед повторною спробою
                            break # Виходимо з внутрішнього циклу, щоб повторно оцінити target_message (що призведе до пошуку в історії)
                        else:
                            print(f"❌ Кнопку '{button.text}' не вдалося натиснути після {retries} спроб.")
                            return False
                    except Exception as e:
                        print(f"⚠️ Невідома помилка при натисканні '{button.text}': {e}")
                        traceback.print_exc()
                        return False
        print(f"⛔ Кнопку '{keyword}' не знайдено в цьому InlineKeyboardMarkup повідомленні (ID: {target_message.id}).")
        
        if attempt < retries:
            print(f"⏳ Кнопку '{keyword}' не знайдено на спробі {attempt}/{retries}. Чекаю {retry_delay} сек. перед наступною спробою.")
            await asyncio.sleep(retry_delay)
        
    print(f"⛔ Кнопку '{keyword}' не знайдено після {retries} спроб.")
    return False

async def get_current_buttons_message(chat_id, wait_after=3):
    """
    Отримує найновіше повідомлення, що містить InlineKeyboardMarkup.
    """
    await asyncio.sleep(wait_after)
    print("🔍 Шукаю найновіше повідомлення з кнопками...")
    async for msg in app.get_chat_history(chat_id, limit=5): # Перевіряємо останні 5 повідомлень
        if msg.reply_markup and isinstance(msg.reply_markup, InlineKeyboardMarkup):
            print(f"✅ Знайдено найновіше повідомлення з кнопками (ID: {msg.id}, Текст: '{msg.text}')")
            return msg
    print("⛔ Не знайдено жодного повідомлення з InlineKeyboardMarkup в останніх 5 повідомленнях.")
    return None

async def wait_for_new_buttons_message(chat_id, last_known_message_id, timeout=25, check_interval=1):
    """
    Чекає на нове повідомлення з InlineKeyboardMarkup, що має ID більше, ніж last_known_message_id.
    """
    print(f"⏳ Чекаю на нове повідомлення з кнопками (після ID: {last_known_message_id}). Макс. очікування: {timeout} сек.")
    start_time = asyncio.get_event_loop().time()
    
    while asyncio.get_event_loop().time() - start_time < timeout:
        current_messages = []
        # Збільшено ліміт для get_chat_history, щоб перевіряти більше повідомлень
        async for msg in app.get_chat_history(chat_id, limit=10): 
            current_messages.append(msg)

        found_new_message_candidate = False # Прапорець, що вказує, чи знайшли ми повідомлення, яке може бути новим
        for msg in current_messages:
            if msg.id > last_known_message_id:
                found_new_message_candidate = True # Знайшли повідомлення новіше за попереднє
                if msg.reply_markup and isinstance(msg.reply_markup, InlineKeyboardMarkup):
                    print(f"✅ Знайдено нове повідомлення з кнопками (ID: {msg.id}, Текст: '{msg.text}')")
                    return msg
                elif msg.text and "будь ласка, не поспішайте" in msg.text.lower():
                    print(f"⚠️ Отримано повідомлення 'Будь ласка, не поспішайте'. Чекаю додатково {DELAY * 3} секунд.")
                    await asyncio.sleep(DELAY * 3)
                    # Оновлюємо last_known_message_id на ID цього повідомлення, щоб наступний пошук був після нього
                    last_known_message_id = msg.id 
                    # Продовжуємо цикл while, щоб знову перевірити повідомлення після паузи
                    break 
            else:
                # Логуємо повідомлення, які не є новішими, щоб бачити, що бот бачить
                print(f"ℹ️ Повідомлення (ID: {msg.id}, Текст: '{msg.text}') не є новішим за {last_known_message_id}.")
        
        if not found_new_message_candidate: # Якщо не знайшли жодного повідомлення новішого за last_known_message_id
             print(f"⏳ Нових повідомлень не знайдено. Чекаю {check_interval} сек. (залишилось {round(timeout - (asyncio.get_event_loop().time() - start_time))} сек.)")
        
        await asyncio.sleep(check_interval)
    
    print(f"❌ Не отримано нове повідомлення з кнопками після {timeout} секунд.")
    return None

async def wait_for_specific_text_message(chat_id, keyword, last_known_message_id, timeout=10, check_interval=0.5):
    """
    Чекає на нове текстове повідомлення, що містить задане ключове слово.
    """
    print(f"⏳ Чекаю на повідомлення з текстом '{keyword}' (після ID: {last_known_message_id}). Макс. очікування: {timeout} сек.")
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < timeout:
        async for msg in app.get_chat_history(chat_id, limit=5):
            if msg.id > last_known_message_id and msg.text and keyword.lower() in msg.text.lower():
                print(f"✅ Знайдено повідомлення з текстом: '{msg.text}' (ID: {msg.id})")
                return msg
        await asyncio.sleep(check_interval)
    print(f"❌ Не знайдено повідомлення з текстом '{keyword}' після {timeout} секунд.")
    return None


async def find_and_recycle_boots():
    """
    Переходить на останню сторінку інвентарю, потім шукає та переробляє шкіряні чоботи.
    """
    print("\n➡️ Переходжу на останню сторінку інвентарю...")

    # Отримуємо повідомлення з кнопками сторінок
    inventory_msg = await get_current_buttons_message(bot_chat, wait_after=DELAY)
    if not inventory_msg:
        print("❌ Не вдалося отримати повідомлення з кнопками інвентарю.")
        return False

    total_pages = 1
    # Шукаємо кнопку з номером сторінки (наприклад, "1/13")
    page_button_found = False
    for row in inventory_msg.reply_markup.inline_keyboard:
        for button in row:
            match = re.search(r'(\d+)/(\d+)', button.text)
            if match:
                current_page = int(match.group(1))
                total_pages = int(match.group(2))
                print(f"📄 Знайдено кнопку сторінки: '{button.text}'. Поточна: {current_page}, Всього: {total_pages}")
                
                # Натискаємо на кнопку сторінки, щоб викликати введення номера
                print(f"➡️ Натискаю на кнопку '{button.text}' для введення номера сторінки.")
                try:
                    await inventory_msg.click(button.text)
                    print(f"✅ Кнопку '{button.text}' успішно натиснуто.")
                    page_button_found = True
                    break # Виходимо з внутрішнього циклу після знаходження кнопки сторінки
                except Exception as e:
                    print(f"⚠️ Помилка при натисканні кнопки сторінки '{button.text}': {e}")
                    traceback.print_exc()
                    return False
        if page_button_found:
            break # Виходимо з зовнішнього циклу після знаходження кнопки сторінки

    if not page_button_found:
        print("❌ Не знайдено кнопку з номером сторінки (наприклад, '1/13').")
        return False

    if total_pages > 1:
        # Додаємо 5-секундну затримку перед надсиланням номера сторінки
        print(f"⏳ Чекаю 5 секунд перед надсиланням номера останньої сторінки.")
        await asyncio.sleep(5) 

        print(f"✉️ Надсилаю номер останньої сторінки ({total_pages}) до чату.")
        await app.send_message(bot_chat, str(total_pages))
        
        # Після надсилання номера сторінки, чекаємо на нове повідомлення, що підтверджує перехід
        inventory_msg_on_last_page = await wait_for_new_buttons_message(bot_chat, inventory_msg.id, timeout=25) 
        if not inventory_msg_on_last_page:
            print("❌ Не вдалося отримати повідомлення з кнопками після переходу на останню сторінку.")
            return False
    else:
        print("ℹ️ Інвентар має лише одну сторінку.")
        inventory_msg_on_last_page = inventory_msg # Якщо сторінка одна, використовуємо поточне повідомлення

    # Додаємо 10-секундну затримку перед пошуком чобіт
    print(f"⏳ Чекаю 10 секунд перед тим, як шукати чоботи на останній сторінці.")
    await asyncio.sleep(10)

    print("🔎 Шукаю чоботи на останній сторінці.")
    # Тепер, коли ми на останній сторінці, шукаємо чоботи
    found_boots_to_recycle = False
    
    # Проходимося по кнопках в актуальному повідомленні (inventory_msg_on_last_page)
    for row in inventory_msg_on_last_page.reply_markup.inline_keyboard:
        for button in row:
            button_text_stripped = button.text.lower().strip()
            if "👢 шкіряні чоботи" in button_text_stripped:
                print(f"➡️ Натискаю: '{button.text}'")
                try: # Try block starts here
                    await inventory_msg_on_last_page.click(button.text)
                    print(f"✅ Кнопку '{button.text}' успішно натиснуто.")
                    
                    # Додано невелику затримку, щоб дати Telegram час оновити повідомлення
                    await asyncio.sleep(DELAY) 

                    # Отримуємо оновлене повідомлення за тим самим ID
                    item_details_msg = await app.get_messages(bot_chat, inventory_msg_on_last_page.id)
                    print(f"ℹ️ Отримано оновлене повідомлення ID: {item_details_msg.id}") # Додано логування

                    if not item_details_msg or not item_details_msg.reply_markup:
                        print("❌ Не вдалося отримати оновлене повідомлення з кнопками після натискання на чоботи.")
                        return False

                    # Тепер шукаємо кнопку "Розібрати на брухт" у цьому повідомленні
                    if await click_button(bot_chat, "🔨 Розібрати на брухт", message_to_click_on=item_details_msg, wait_after=DELAY):
                        await asyncio.sleep(DELAY)

                        # Чекаємо на повідомлення з текстом підтвердження та кнопками "Так" / "Ні"
                        confirm_buttons_msg = None
                        for _ in range(5): # Try a few times to get the confirmation message
                            temp_msg = await get_current_buttons_message(bot_chat, wait_after=1)
                            if temp_msg and temp_msg.text and "ви впевнені що хочете розібрати" in temp_msg.text.lower():
                                confirm_buttons_msg = temp_msg
                                print(f"✅ Знайдено повідомлення з підтвердженням (ID: {confirm_buttons_msg.id}, Текст: '{confirm_buttons_msg.text}')")
                                break
                            print(f"⏳ Очікую повідомлення з підтвердженням 'Так'/'Ні'...")
                            await asyncio.sleep(1)

                        if not confirm_buttons_msg:
                            print("❌ Не вдалося отримати повідомлення з кнопками підтвердження 'Так'/'Ні'.")
                            return False

                        # --- NEW LOGIC FOR CLICKING 'ТАК' AND VERIFYING DISMANTLE ---
                        print("➡️ Спробую натиснути кнопку 'Так' для підтвердження розбирання та очікування результату.")
                        
                        # Виконуємо одну спробу натиснути "Так"
                        # Ми не чекаємо на її успіх тут, а одразу перевіряємо повідомлення про розбирання
                        # Змінено: Викликаємо click() напряму, щоб уникнути логування click_button
                        tak_button_clicked_attempted = False
                        if confirm_buttons_msg and confirm_buttons_msg.reply_markup:
                            for row in confirm_buttons_msg.reply_markup.inline_keyboard:
                                for button in row:
                                    if "так" in button.text.lower().strip():
                                        try:
                                            await confirm_buttons_msg.click(button.text)
                                            print(f"✅ Кнопку 'Так' для підтвердження успішно натиснуто (спроба 1).")
                                            tak_button_clicked_attempted = True
                                            break
                                        except (FloodWait, TimeoutError, RPCError) as e:
                                            print(f"⚠️ Помилка при натисканні 'Так' (спроба 1): {e}. Продовжую перевіряти повідомлення про розбирання.")
                                            # Пригнічуємо трасування тут, оскільки це очікувана помилка
                                            pass 
                                            tak_button_clicked_attempted = True # Вважаємо, що спроба була
                                            break
                                        except Exception as e:
                                            print(f"⚠️ Невідома помилка при натисканні 'Так' (спроба 1): {e}")
                                            traceback.print_exc() # Виводимо трасування для несподіваних помилок
                                            break
                                if tak_button_clicked_attempted:
                                    break

                        # Одразу після спроби натиснути "Так", перевіряємо наявність повідомлення про успішне розбирання
                        dismantle_success_msg = await wait_for_specific_text_message(bot_chat, "розібрано на 1 брухту", confirm_buttons_msg.id, timeout=10) 

                        if dismantle_success_msg:
                            print(f"✅ Предмет успішно розібрано: '{dismantle_success_msg.text}'")
                            # Якщо розбирання успішне, одразу надсилаємо /menu і завершуємо функцію
                            print("➡️ Надсилаю команду '/menu' для перезапуску циклу.")
                            await app.send_message(bot_chat, "/menu")
                            await asyncio.sleep(DELAY) 
                            return True # Успішно розібрано та відправлено /menu
                        else:
                            print("❌ Не отримано повідомлення про успішне розбирання після спроби натиснути 'Так'.")
                            # Якщо повідомлення про успішне розбирання не з'явилося,
                            # ми все одно надсилаємо /menu, щоб скинути стан і продовжити цикл.
                            print("➡️ Надсилаю команду '/menu' для скидання стану.")
                            await app.send_message(bot_chat, "/menu")
                            await asyncio.sleep(DELAY)
                            return False # Розбирання, ймовірно, не вдалося або повідомлення не з'явилося

                    else: # Цей else відноситься до if await click_button(bot_chat, "🔨 Розібрати на брухт", ...)
                        print("⚠️ Кнопка '🔨 Розібрати на брухт' не знайдена.")
                        return False
                except Exception as e: # Цей блок except відноситься до try, що починається на рядку 258
                    print(f"⚠️ Помилка при натисканні на чоботи '{button.text}': {e}")
                    traceback.print_exc()
                    return False
    
    if not found_boots_to_recycle:
        print("👢 Чоботи не знайдені на останній сторінці.")
    return found_boots_to_recycle


async def recycle_boots():
    """
    Головна функція для переробки чобіт:
    - Починає цикл пошуку та переробки чобіт.
    """
    print("\n♻️ Починаю переробку чобіт")

    # Цикл переробки чобіт
    for i in range(25): # Повторюємо 25 разів
        print(f"\n♻️ Спроба переробки {i+1}/25")

        # Навігація до інвентарю та спорядження на початку кожної ітерації
        print("➡️ Надсилаю команду '/menu' для початкової навігації.")
        await app.send_message(bot_chat, "/menu")
        await asyncio.sleep(DELAY)
        
        print("➡️ Надсилаю команду 'Назад' (ReplyKeyboardMarkup) для початкової навігації.")
        await app.send_message(bot_chat, "Назад")
        await asyncio.sleep(DELAY)

        print("➡️ Надсилаю команду '🎒 Інвентар' (ReplyKeyboardMarkup).")
        await app.send_message(bot_chat, "🎒 Інвентар")
        await asyncio.sleep(DELAY) 

        inventory_entry_msg = await get_current_buttons_message(bot_chat, wait_after=DELAY * 2) 
        if not inventory_entry_msg:
            print("❌ Не вдалося отримати повідомлення з кнопками інвентарю після початкового входу.")
            return # Зупиняємо, якщо не можемо отримати кнопки

        # Змінено: Скорочено час очікування для кнопки "Спорядження" вдвічі
        if not await click_button(bot_chat, "🎽 Спорядження", message_to_click_on=inventory_entry_msg, wait_after=DELAY): # Змінено DELAY * 2 на DELAY
            print("❌ Не вдалося відкрити Спорядження під час початкової навігації. Перевірте назву кнопки або час очікування.")
            return # Зупиняємо, якщо не можемо потрапити в спорядження

        found = await find_and_recycle_boots()
        if not found:
            print(f"✅ Чоботи більше не знайдено після {i+1} спроб.")
            break
        # Невелика затримка між ітераціями (повна навігація вже виконана у find_and_recycle_boots)
        await asyncio.sleep(DELAY) 

async def main():
    """
    Основна функція, яка запускає бота.
    Додано загальну обробку винятків для запобігання вильотам.
    """
    print("🚀 Спроба запуску бота...")
    try:
        async with app:
            print("✅ Бот успішно підключено до Telegram.")
            await recycle_boots() # Виклик функції переробки
    except FloodWait as e:
        print(f"⚠️ Глобальна FloodWait: Зачекайте {e.value} секунд. Бот був занадто активним.")
        await asyncio.sleep(e.value + 5)
    except RPCError as e:
        print(f"❌ Глобальна RPC Помилка: {e}. Перевірте підключення або параметри API. Деталі: {e}")
        traceback.print_exc()
    except Exception as e:
        print(f"❌ Неочікувана помилка в основній функції: {e}")
        traceback.print_exc() # Виводимо повний стек викликів для діагностики
    finally:
        print("\n--- Завершення роботи бота ---")
        # Додаємо значну затримку перед зупинкою Pyrogram
        print("⏳ Завершення роботи, чекаю 60 секунд перед відключенням Pyrogram...")
        await asyncio.sleep(60) # Додаткова затримка перед зупинкою
        
        # Використовуємо is_running для більш надійної перевірки стану клієнта
        if app.is_running: 
            print("Бот відключається від Telegram...")
            await app.stop()
            print("Бот відключено від Telegram.")
        else:
            print("Бот не був підключений або вже відключився.")


# Запуск асинхронної функції
if __name__ == "__main__":
    try:
        app.run(main()) # Використовуємо app.run() для коректного управління циклом подій
    except Exception as e:
        print(f"❌ Критична помишка перед запуском Pyrogram або під час його виконання: {e}")
        traceback.print_exc()