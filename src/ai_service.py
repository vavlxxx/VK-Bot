from typing import Dict, List

from openai import AsyncOpenAI

from src.config import settings
from src.logconfig import get_logger

logger = get_logger("ai_service")


class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_url,
        )
        # Хранилище истории разговоров: {user_id: [messages]}
        self.conversations: Dict[int, List[Dict[str, str]]] = {}

    async def get_ai_response(self, user_id: int, user_message: str) -> str:
        """Получить ответ от AI с учетом контекста беседы"""
        try:
            # Получаем или создаем историю беседы для пользователя
            if user_id not in self.conversations:
                self.conversations[user_id] = [
                    {
                        "role": "system",
                        "content": "Ты полезный AI-помощник в ВКонтакте. Отвечай дружелюбно и по делу.",
                    }
                ]

            # Добавляем сообщение пользователя в историю
            self.conversations[user_id].append(
                {"role": "user", "content": user_message}
            )

            logger.debug(f"Отправка запроса к AI для пользователя {user_id}")

            # Отправляем запрос с полной историей
            response = await self.client.chat.completions.create(
                model=settings.ai_model,
                messages=self.conversations[user_id],
                max_tokens=1000,
                temperature=0.7,
            )

            ai_message = response.choices[0].message.content

            # Добавляем ответ AI в историю
            self.conversations[user_id].append(
                {"role": "assistant", "content": ai_message}
            )

            # Ограничиваем историю (например, последние 20 сообщений)
            if len(self.conversations[user_id]) > 20:
                # Оставляем системное сообщение и последние 19
                self.conversations[user_id] = [
                    self.conversations[user_id][0]
                ] + self.conversations[user_id][-19:]

            logger.info(f"Успешный ответ AI для пользователя {user_id}")
            return ai_message

        except Exception as e:
            logger.error(f"Ошибка при запросе к AI: {e}")
            return "Извините, произошла ошибка при обработке вашего запроса. Попробуйте позже."

    def clear_conversation(self, user_id: int) -> None:
        """Очистить историю беседы пользователя"""
        if user_id in self.conversations:
            del self.conversations[user_id]
            logger.info(f"История беседы очищена для пользователя {user_id}")


# Singleton экземпляр
ai_service = AIService()
