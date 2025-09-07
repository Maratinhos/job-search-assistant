import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)

from bot import messages, keyboards
from db import crud
from db.database import get_db

logger = logging.getLogger(__name__)

# --- Новые пакеты баллов ---
POINT_PACKAGES = {
    "points_10": {"price": 149, "points": 10},
    "points_30": {"price": 399, "points": 30},
    "points_100": {"price": 999, "points": 100},
}


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет пользователю его текущий баланс."""
    chat_id = update.effective_chat.id
    db_session_gen = get_db()
    db = next(db_session_gen)
    try:
        user = crud.get_or_create_user(db, chat_id=chat_id)
        user_balance = crud.get_user_balance(db, user_id=user.id)

        balance_value = user_balance.balance if user_balance else 0
        message = messages.BALANCE_MESSAGE.format(balance=balance_value)

        await update.message.reply_text(message)
    finally:
        db.close()


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начинает процесс покупки баллов."""
    await update.message.reply_text(
        messages.CHOOSE_TARIFF,
        reply_markup=keyboards.points_packages_keyboard(POINT_PACKAGES)
    )


async def handle_package_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор пакета баллов."""
    query = update.callback_query
    await query.answer()

    package_key = query.data.split('_')[1] # e.g., "10" from "buy_10"
    package_id = f"points_{package_key}"
    package = POINT_PACKAGES.get(package_id)

    if not package:
        await query.edit_message_text(messages.PURCHASE_ERROR)
        return

    chat_id = query.effective_chat.id
    db_session_gen = get_db()
    db = next(db_session_gen)
    try:
        user = crud.get_or_create_user(db, chat_id=chat_id)

        # Эмуляция успешной покупки
        crud.update_user_balance(
            db,
            user_id=user.id,
            amount=package["points"],
            description=f"Покупка пакета: {package['points']} баллов",
            cost=package["price"]
        )

        await query.edit_message_text(
            messages.PURCHASE_SUCCESS.format(points_count=package["points"])
        )

        # Показываем новый баланс
        user_balance = crud.get_user_balance(db, user_id=user.id)
        await query.message.reply_text(
            messages.BALANCE_MESSAGE.format(balance=user_balance.balance)
        )

    except Exception as e:
        logger.error(f"Ошибка при покупке пакета: {e}", exc_info=True)
        await query.edit_message_text(messages.PURCHASE_ERROR)
    finally:
        db.close()


balance_handler = CommandHandler("balance", balance)
buy_handler = CommandHandler("buy", buy)
package_selection_handler = CallbackQueryHandler(handle_package_selection, pattern="^buy_")
