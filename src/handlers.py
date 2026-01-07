from vkbottle.bot import BotLabeler, Message, rules, MessageEvent
from vkbottle import Keyboard, KeyboardButtonColor, Text, Callback
from vkbottle_types.events import GroupEventType

from src.ai_service import ai_service
from src.database import db
from src.logconfig import get_logger

logger = get_logger("handlers")
labeler = BotLabeler()

# Общая клавиатура
MAIN_MENU_KEYBOARD = (
    Keyboard(one_time=False, inline=False)
    .add(Text("Новый чат"), color=KeyboardButtonColor.POSITIVE)
    .add(Text("История чатов"), color=KeyboardButtonColor.PRIMARY)
    .get_json()
)

@labeler.message(text="Новый чат")
async def create_new_chat(message: Message):
    chat_id = await db.create_chat(message.from_id, title="Новый чат")
    await message.answer(
        f"Начат новый чат (ID: {chat_id}). Пишите!",
        keyboard=MAIN_MENU_KEYBOARD
    )

@labeler.message(text="История чатов")
async def show_chat_history(message: Message):
    chats = await db.get_user_chats(message.from_id, limit=5)
    
    if not chats:
        await message.answer("У вас нет истории чатов.", keyboard=MAIN_MENU_KEYBOARD)
        return

    # Inline клавиатура со списком чатов
    keyboard = Keyboard(inline=True)
    for chat in chats:
        # payload должен быть валидным JSON
        title = chat['title'] or f"Chat {chat['id']}"
        # Ограничиваем длину заголовка
        if len(title) > 30:
            title = title[:27] + "..."
            
        emoji = "🟢 " if chat['is_active'] else ""
        
        keyboard.add(
            Callback(f"{emoji}{title}", {"cmd": "open_chat", "chat_id": chat['id']}),
            color=KeyboardButtonColor.SECONDARY if not chat['is_active'] else KeyboardButtonColor.POSITIVE
        )
        keyboard.row()
    
    # Можно добавить навигацию, но пока просто последние 5
    
    await message.answer("Ваши последние чаты:", keyboard=keyboard.get_json())


@labeler.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent)
async def handle_callback(event: MessageEvent):
    # Обработка нажатий на инлайн кнопки
    if event.payload and isinstance(event.payload, dict):
        cmd = event.payload.get("cmd")
        if cmd == "open_chat":
            chat_id = event.payload.get("chat_id")
            await db.set_active_chat(event.user_id, chat_id)
            
            await event.ctx_api.messages.send_message_event_answer(
                event_id=event.event_id,
                peer_id=event.peer_id,
                user_id=event.user_id,
                event_data='{"type": "show_snackbar", "text": "Чат выбран!"}'
            )

            # Опционально: отправить сообщение, что чат переключен
            # Но у нас нет объекта message здесь, это event. 
            # Можно отправить новое от бота
            await event.ctx_api.messages.send(
                peer_id=event.peer_id,
                message=f"Переключились на чат {chat_id}. История загружена.",
                random_id=0,
                keyboard=MAIN_MENU_KEYBOARD
            )

@labeler.message()
async def chat_message_handler(message: Message):
    user_id = message.from_id
    user_text = message.text or "" # Text might be empty if only photo

    # Проверяем вложения на наличие фото
    photo_url = None
    if message.attachments:
        for attachment in message.attachments:
            if attachment.photo:
                # Берем самый большой размер (обычно последний в списке sizes или конкретные типы)
                # vkbottle sizes: sorted by generic algorithm usually?
                # Let's verify. Usually picking the last one is safe for 'largest'
                sizes = attachment.photo.sizes
                if sizes:
                    # Sort just in case by width/height if needed, but last is usually best
                    # Or find type 'z', 'y', 'x' etc.
                    # Simple heuristic: last one
                    photo_url = sizes[-1].url
                    break # Only one photo for now

    if not user_text and not photo_url:
        return

    # Определяем активный чат
    active_chat_id = await db.get_active_chat(user_id)
    
    if not active_chat_id:
        # Если чата нет, создаем новый автоматически
        title = user_text[:50] if user_text else "Photo Message"
        active_chat_id = await db.create_chat(user_id, title=title)
        await message.answer(
            "Создан новый чат. Обрабатываю запрос...", 
            keyboard=MAIN_MENU_KEYBOARD
        )
    
    # Отправляем "печатает..."
    # await message.ctx_api.messages.set_activity(type="typing", peer_id=message.peer_id)

    response = await ai_service.get_ai_response(user_id, active_chat_id, user_text, photo_url=photo_url)
    
    await message.answer(response, keyboard=MAIN_MENU_KEYBOARD)

