from openai import AsyncOpenAI

from src.config import settings
from src.logconfig import get_logger
from src.database import db

logger = get_logger("ai_service")


class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_url,
        )

    async def get_ai_response(self, user_id: int, chat_id: int, user_message: str, photo_url: str = None) -> str:
        """Получить ответ от AI с учетом контекста беседы из БД"""
        try:
            # Сохраняем сообщение пользователя
            # Если есть фото, добавляем пометку в текст для истории
            stored_message = user_message
            if photo_url:
                stored_message = f"{user_message} (Attached Image: {photo_url})"
            
            await db.add_message(chat_id, "user", stored_message)
            
            # Получаем историю сообщений для контекста
            # Ограничиваем контекст последними 20 сообщениями
            history = await db.get_chat_messages(chat_id, limit=20)
            
            # Формируем контент текущего сообщения
            current_content = [{"type": "text", "text": user_message}]
            if photo_url:
                current_content.append({
                    "type": "image_url",
                    "image_url": {"url": photo_url}
                })
            
            # Собираем сообщения для API: system + history + current
            # Важно: историю передаем как есть (text), а текущее сообщение как object (text + image)
            # Но history мы уже взяли из БД, где лежит stored_message.
            # API OpenAI не любит, когда последнее сообщение дублируется, если мы его уже добавили в историю?
            # Нет, мы обычно отправляем user message в messages.
            # В моем коде выше: await db.add_message(...) -> history = await db.get_chat_messages(...)
            # То есть history УЖЕ содержит текущее сообщение (stored_message).
            # Проблема: в БД оно лежит как строка string, а нам нужно отправить его как vision-структуру.
            
            # Решение: Берем history[:-1] (все кроме последнего), и добавляем последнее в нужном формате.
            
            messages_payload = [
                {
                    "role": "system",
                    "content": "Ты полезный AI-помощник в ВКонтакте. Отвечай дружелюбно и по делу.",
                }
            ]
            
            if history:
                # Все старые сообщения
                messages_payload.extend(history[:-1])
                
                # Последнее сообщение (текущее) формируем правильно
                messages_payload.append({
                    "role": "user",
                    "content": current_content
                })
            else:
                 # Если истории нет (странно, так как мы только что добавили), то просто текущее
                messages_payload.append({
                    "role": "user",
                    "content": current_content
                })

            logger.debug(f"Отправка запроса к AI для пользователя {user_id} (чат {chat_id}, фото: {bool(photo_url)})")

            # Отправляем запрос с полной историей
            response = await self.client.chat.completions.create(
                model=settings.ai_model,
                messages=messages_payload,
                max_tokens=1000,
                temperature=0.7,
            )

            ai_message = response.choices[0].message.content

            # Сохраняем ответ AI
            await db.add_message(chat_id, "assistant", ai_message)
            
            # Если это первое сообщение в чате (история была пустой до этого запроса, сейчас там user + system),
            # можно обновить заголовок чата, но для простоты оставим "New Chat" или обновим позже.
            # Здесь мы просто возвращаем ответ.

            logger.info(f"Успешный ответ AI для пользователя {user_id}")
            return ai_message

        except Exception as e:
            logger.error(f"Ошибка при запросе к AI: {e}")
            return "Извините, произошла ошибка при обработке вашего запроса. Попробуйте позже."


# Singleton экземпляр
ai_service = AIService()
