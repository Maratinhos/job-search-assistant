import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from bot import messages

logger = logging.getLogger(__name__)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Отменяет текущий диалог.
    Удаляет клавиатуру и отправляет сообщение об отмене.
    """
    query = update.callback_query
    if query:
        await query.answer()
        try:
            await query.edit_message_text(text=messages.ACTION_CANCELED)
        except Exception:
            # Message might have been deleted or is not editable, just log it
            logger.warning("Could not edit message on cancel, probably already gone.")
    else:
        await update.message.reply_text(text=messages.ACTION_CANCELED, reply_markup=None)

    # Очищаем user_data, чтобы не оставлять мусор от прерванного диалога
    context.user_data.clear()

    logger.info(f"User {update.effective_chat.id} cancelled the conversation.")
    return ConversationHandler.END
