"""Обработка ошибок и логирование"""
import traceback
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class BotErrorHandler:
    """Централизованная обработка ошибок бота"""
    
    def __init__(self, bot=None, admin_ids=None):
        self.bot = bot
        self.admin_ids = admin_ids or []
    
    async def handle_exception(self, error: Exception, context: str = "Unknown"):
        """Обработать исключение"""
        error_msg = f"❌ <b>ОШИБКА: {context}</b>\n\n{str(error)}"
        tb = traceback.format_exc()
        
        # Логируем локально
        logger.error(f"Error in {context}: {error}\n{tb}")
        
        # Отправляем админам
        if self.bot and self.admin_ids:
            full_msg = f"🚨 <b>БОТ УПАЛ</b>\n\n<b>Контекст:</b> {context}\n<b>Ошибка:</b> {error}\n\n<pre>{tb[:2000]}</pre>"
            for admin_id in self.admin_ids:
                try:
                    await self.bot.send_message(admin_id, full_msg, parse_mode="HTML")
                except Exception as e:
                    logger.error(f"Failed to send error to admin {admin_id}: {e}")
    
    def log_and_notify(self):
        """Декоратор для функций"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    await self.handle_exception(e, func.__name__)
                    raise
            return wrapper
        return decorator
