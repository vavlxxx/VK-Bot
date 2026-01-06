from vkbottle.bot import BotLabeler, Message

from src.ai_service import ai_service
from src.logconfig import get_logger

# Создаем отдельный labeler для модуля
labeler = BotLabeler()
logger = get_logger("handlers")


@labeler.message(text="/start")
async def start_handler(message: Message):
    """Обработчик команды /start"""
    await message.answer(
        "Привет! Я AI-помощник на базе нейросети.\n"
        "Задай мне любой вопрос!\n\n"
        "Команды:\n"
        "/clear - очистить историю беседы"
    )


@labeler.message(text="/clear")
async def clear_handler(message: Message):
    """Очистка истории беседы пользователя"""
    ai_service.clear_conversation(message.from_id)
    await message.answer("История беседы очищена. Начнем сначала!")


@labeler.message()
async def ai_handler(message: Message):
    """Обработчик всех сообщений с AI"""
    try:
        # Показываем, что бот печатает
        await message.ctx_api.messages.set_activity(
            peer_id=message.peer_id, type="typing"
        )

        # Получаем ответ от AI
        ai_response = await ai_service.get_ai_response(
            user_id=message.from_id, user_message=message.text
        )

        # Отправляем ответ
        await message.answer(ai_response)

    except Exception as e:
        logger.error(f"Ошибка в обработчике AI: {e}")
        await message.answer("Произошла ошибка при обработке сообщения.")
