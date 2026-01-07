import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.handlers import labeler as handlers_labeler
from vkbottle.bot import Bot

from src.config import settings
from src.logconfig import configurate_logging, get_logger
from src.middlewares import LoggingMiddleware

# Настройка логирования
configurate_logging()
logger = get_logger("main")

# Инициализация бота
bot = Bot(token=settings.vk_api_key)

# Регистрация middleware
bot.labeler.message_view.register_middleware(LoggingMiddleware)

# Подключение labeler с обработчиками
bot.labeler.load(handlers_labeler)


if __name__ == "__main__":
    logger.info("Bot has been started...")
    # Инициализация БД
    import asyncio
    from src.database import db
    
    # We need to run async init. Bot.run_forever() manages loop, 
    # but we need DB ready before requests. 
    # vkbottle manages its own loop. Let's make a wrapper.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    loop.run_until_complete(db.init_db())
    bot.run_forever()
