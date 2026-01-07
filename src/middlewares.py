from vkbottle import BaseMiddleware
from vkbottle.bot import Message

from src.logconfig import get_logger

logger = get_logger("middleware")


class LoggingMiddleware(BaseMiddleware[Message]):
    async def pre(self):
        logger.info(
            "Incoming message: user_id=%s, peer_id=%s, text='%s'",
            self.event.from_id,
            self.event.peer_id,
            self.event.text,
        )

    async def post(self):
        logger.debug("Successfully processed message from %s", self.event.from_id)
