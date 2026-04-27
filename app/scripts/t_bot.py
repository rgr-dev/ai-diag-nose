# Telegram bot utilities (async).
# python-telegram-bot v20+ requires async calls. Usage from sync code:
#
#   import asyncio
#   from app.scripts.t_bot import send_message, get_last_interacted_chat_ids
#
#   results = asyncio.run(send_message("Hello!"))
#   chat_ids = asyncio.run(get_last_interacted_chat_ids())
#
# From async code, just await directly:
#
#   results = await send_message("Hello!")
#
# Environment variables required:
#   TELEGRAM_BOT_TOKEN  - Bot token from BotFather
#   TELEGRAM_CHAT_IDS   - Comma-separated chat IDs (e.g. "123456,789012")

import asyncio
import logging
import os
import uuid
from typing import Any, Callable, Coroutine

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import TelegramError
from telegram.ext import filters, ApplicationBuilder, CallbackQueryHandler, ContextTypes, MessageHandler

from app.constants import Constants

logger = logging.getLogger(__name__)


def _parse_chat_ids() -> list[str]:
    return [cid.strip() for cid in os.getenv("TELEGRAM_CHAT_IDS", "").split(",") if cid.strip()]


async def post_init(app):
    # Remove any existing webhook to avoid conflict with polling
    await app.bot.delete_webhook(drop_pending_updates=True)
    info = await app.bot.get_me()
    logger.info(f"Bot iniciado como @{info.username}")


async def send_message(text: str, chat_ids: list[str] | None = None) -> dict[str, bool]:
    """Send a text message to one or more Telegram users.

    Args:
        text: The message body.
        chat_ids: Optional explicit list of chat IDs. Falls back to TELEGRAM_CHAT_IDS env var.

    Returns:
        A dict mapping each chat_id to True (sent) or False (failed).
    """
    _bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    targets = chat_ids or _parse_chat_ids()
    results: dict[str, bool] = {}

    for chat_id in targets:
        try:
            await _bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
            results[chat_id] = True
        except TelegramError:
            logger.exception("Failed to send Telegram message to chat_id=%s", chat_id)
            results[chat_id] = False

    return results


async def get_last_interacted_chat_ids() -> list[int]:
    """Retrieve chat IDs from the most recent updates the bot has received.

    Returns:
        A deduplicated list of chat IDs that recently interacted with the bot.
    """
    try:
        _bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        updates = await _bot.get_updates()
        chat_ids: set[int] = set()
        for update in updates:
            message = update.message or update.edited_message or update.channel_post
            if message and message.chat:
                chat_ids.add(message.chat.id)
        return sorted(chat_ids)
    except TelegramError:
        logger.exception("Failed to fetch recent updates from Telegram")
        return []


async def send_confirmation_message(
    text: str,
    confirm_label: str = Constants.HUMAN_APPROVE,
    cancel_label: str = Constants.HUMAN_REJECT,
    advice_label: str = Constants.HUMAN_ADVICE,
    chat_ids: list[str] | None = None,
    callback_data_prefix: str | None = None,
) -> dict[str, Any]:
    """Send a message with confirm/cancel inline buttons.

    Args:
        text: The message body.
        confirm_label: Label for the confirm button.
        cancel_label: Label for the cancel button.
        chat_ids: Optional explicit list of chat IDs. Falls back to TELEGRAM_CHAT_IDS env var.
        callback_data_prefix: Optional prefix for callback data. A unique one is generated if omitted.

    Returns:
        A dict mapping each chat_id to a result dict with keys ``sent`` (bool) and
        ``callback_data_prefix`` (str) that can be used to match button taps.
    """
    _bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    targets = chat_ids or _parse_chat_ids()
    prefix = callback_data_prefix or uuid.uuid4().hex[:8]

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(confirm_label, callback_data=f"{prefix}:{confirm_label}"),
            InlineKeyboardButton(cancel_label, callback_data=f"{prefix}:{cancel_label}"),
            InlineKeyboardButton(advice_label, callback_data=f"{prefix}:{advice_label}"),
        ]
    ])

    results: dict[str, Any] = {}
    for chat_id in targets:
        try:
            await _bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard, parse_mode="HTML")
            results[chat_id] = {"sent": True, "callback_data_prefix": prefix}
        except TelegramError:
            logger.exception("Failed to send confirmation message to chat_id=%s", chat_id)
            logger.error("chat message text was: %s", text)
            results[chat_id] = {"sent": False, "callback_data_prefix": prefix}

    return results


async def listen_for_confirmation(
    callback_data_prefix: str,
    custom_callback_handler: Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]],
    custom_message_handler: Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]],
    timeout: float = 300,
) -> None:
    """Listen for a user button tap matching *callback_data_prefix* and execute the given callback.

    This starts a polling loop that waits for an inline-button callback whose ``data``
    starts with *callback_data_prefix*. When the confirm button is tapped the
    *on_confirm* callable is executed; when cancel is tapped *on_cancel* is executed
    (if provided). The listener stops after handling the first matching tap or after
    *timeout* seconds, whichever comes first.

    Args:
        callback_data_prefix: The prefix returned by :func:`send_confirmation_message`.
        on_confirm: Sync or async callable invoked when the user taps **Confirm**.
            Receives the full ``callback_data`` string (e.g. ``"prefix:confirm"``).
        on_cancel: Optional sync or async callable invoked when the user taps **Cancel**.
            Receives the full ``callback_data`` string (e.g. ``"prefix:cancel"``).
        timeout: Maximum seconds to wait for a button tap before giving up.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    matched = asyncio.Event()
    
    def build_handler(custom_handler):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            try:
                await custom_handler(update, context)
            finally:
                matched.set()
        return wrapper

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CallbackQueryHandler(build_handler(custom_callback_handler), pattern=f"^{callback_data_prefix}"))
    app.add_handler(CallbackQueryHandler(build_handler(custom_message_handler), pattern=f"^{callback_data_prefix}"))
    app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, build_handler(custom_message_handler)))

    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=[Update.CALLBACK_QUERY, Update.MESSAGE])

    try:
        await asyncio.wait_for(matched.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning("Confirmation listener timed out after %.0fs (prefix=%s)", timeout, callback_data_prefix)
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


async def get_recent_chat_ids():
    """
     This method is just for get the chat ids that recently interacted with the bot, to be used in the .env variable TELEGRAM_CHAT_IDS for testing purposes.
    """
    try:
        _bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        updates = await _bot.get_updates()
        chat_ids: list[str] = []
        seen: set[int] = set()
        for update in reversed(updates):
            message = update.message or update.edited_message or update.channel_post
            if not message or not message.chat:
                continue
            chat_id = message.chat.id
            if chat_id in seen:
                continue
            chat_ids.append(str(chat_id))
            seen.add(chat_id)
            if len(chat_ids) >= 3:
                break
        logger.info("Recent chat IDs: %s", chat_ids)
    except TelegramError:
        logger.exception("Failed to fetch recent updates from Telegram")

if __name__ == "__main__":
    import asyncio
    asyncio.run(get_recent_chat_ids())