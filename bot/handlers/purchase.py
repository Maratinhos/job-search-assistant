import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)

from bot.handlers.states import MAIN_MENU
from bot import messages, keyboards
from db import crud
from db.database import get_db

logger = logging.getLogger(__name__)


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет пользователю его текущий баланс."""
    chat_id = update.effective_chat.id
    db_session_gen = get_db()
    db = next(db_session_gen)
    try:
        user = crud.get_or_create_user(db, chat_id=chat_id)
        active_purchase = crud.get_active_purchase(db, user_id=user.id)

        if active_purchase:
            message = messages.BALANCE_MESSAGE.format(
                runs_left=active_purchase.runs_left,
                runs_total=active_purchase.runs_total
            )
        else:
            # Случай, когда бесплатный тариф уже закончился, а нового нет
            message = messages.BALANCE_MESSAGE.format(runs_left=0, runs_total=0)

        await update.message.reply_text(message)
    finally:
        db.close()


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начинает процесс 'покупки'."""
    chat_id = update.effective_chat.id
    db_session_gen = get_db()
    db = next(db_session_gen)
    try:
        user = crud.get_or_create_user(db, chat_id=chat_id)
        active_purchase = crud.get_active_purchase(db, user_id=user.id)

        # Запрещаем покупку, если текущий пакет не израсходован
        if active_purchase and active_purchase.runs_left > 0:
            await update.message.reply_text(messages.CANNOT_PURCHASE_YET)
            return

        tariffs = crud.get_tariffs(db)
        if not tariffs:
            await update.message.reply_text(messages.PURCHASE_ERROR)
            return

        await update.message.reply_text(
            messages.CHOOSE_TARIFF,
            reply_markup=keyboards.tariffs_keyboard(tariffs)
        )
    finally:
        db.close()


async def handle_tariff_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор тарифа."""
    query = update.callback_query
    await query.answer()

    tariff_id = int(query.data.split('_')[1])
    chat_id = query.effective_chat.id

    db_session_gen = get_db()
    db = next(db_session_gen)
    try:
        user = crud.get_or_create_user(db, chat_id=chat_id)
        tariff = crud.get_tariff_by_id(db, tariff_id)

        if not tariff:
            await query.edit_message_text(messages.PURCHASE_ERROR)
            return

        # Эмуляция успешной покупки
        crud.create_purchase(db, user_id=user.id, tariff_id=tariff.id)

        await query.edit_message_text(
            messages.PURCHASE_SUCCESS.format(runs_count=tariff.runs_count)
        )

        # Показываем новый баланс
        await balance(query, context)

    except Exception as e:
        logger.error(f"Ошибка при покупке тарифа: {e}", exc_info=True)
        await query.edit_message_text(messages.PURCHASE_ERROR)
    finally:
        db.close()


balance_handler = CommandHandler("balance", balance)
buy_handler = CommandHandler("buy", buy)
tariff_selection_handler = CallbackQueryHandler(handle_tariff_selection, pattern="^tariff_")
