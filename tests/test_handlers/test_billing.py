import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from telegram import Update, User as TUser, Chat
from telegram.ext import CallbackContext

from bot.handlers.billing import balance, buy, handle_package_selection, POINT_PACKAGES
from db import crud, models

@pytest.mark.asyncio
@patch('bot.handlers.billing.get_db')
@patch('bot.handlers.billing.crud')
async def test_balance_command(mock_crud, mock_get_db, update_mock, context_mock):
    """Тестирует команду /balance."""
    mock_db = MagicMock()
    mock_get_db.return_value = iter([mock_db])
    mock_crud.get_or_create_user.return_value = MagicMock(id=1)
    mock_crud.get_user_balance.return_value = MagicMock(balance=5)

    await balance(update_mock, context_mock)

    update_mock.message.reply_text.assert_called_once_with("Текущий баланс: 5 баллов.")

@pytest.mark.asyncio
@patch('bot.handlers.billing.keyboards')
async def test_buy_command(mock_keyboards, update_mock, context_mock):
    """Тестирует команду /buy."""
    await buy(update_mock, context_mock)

    update_mock.message.reply_text.assert_called_once()
    assert "Выберите пакет для пополнения:" in update_mock.message.reply_text.call_args[0][0]
    mock_keyboards.points_packages_keyboard.assert_called_once_with(POINT_PACKAGES)

@pytest.mark.asyncio
@patch('bot.handlers.billing.get_db')
@patch('bot.handlers.billing.crud')
async def test_package_selection(mock_crud, mock_get_db, update_mock, context_mock):
    """Тестирует выбор и 'покупку' пакета баллов."""
    mock_db = MagicMock()
    mock_get_db.return_value = iter([mock_db])
    mock_user = MagicMock(id=1)
    mock_crud.get_or_create_user.return_value = mock_user
    mock_crud.get_user_balance.return_value = MagicMock(balance=30)

    package_to_buy = "points_30"
    package_key = package_to_buy.split('_')[1]

    chat_id = 789
    update = AsyncMock(spec=Update)
    update.callback_query = AsyncMock()
    update.callback_query.data = f"buy_{package_key}"
    update.callback_query.effective_chat.id = chat_id
    update.callback_query.message = AsyncMock()


    context = AsyncMock(spec=CallbackContext)

    await handle_package_selection(update, context)

    # Проверяем баланс
    mock_crud.update_user_balance.assert_called_once_with(
        mock_db,
        user_id=mock_user.id,
        amount=POINT_PACKAGES[package_to_buy]["points"],
        description=f"Покупка пакета: {POINT_PACKAGES[package_to_buy]['points']} баллов",
        cost=POINT_PACKAGES[package_to_buy]["price"]
    )

    # Проверяем сообщения
    update.callback_query.edit_message_text.assert_called_once()
    assert "Оплата прошла успешно" in update.callback_query.edit_message_text.call_args[0][0]

    update.callback_query.message.reply_text.assert_called_once()
    assert f"Текущий баланс: 30 баллов." in update.callback_query.message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_initial_bonus(db_session):
    """Тестирует начисление приветственных баллов новому пользователю."""
    chat_id = 1001
    user = crud.get_or_create_user(db_session, chat_id=chat_id)

    balance = crud.get_user_balance(db_session, user_id=user.id)
    assert balance is not None
    assert balance.balance == 6

    # Проверяем транзакцию
    transactions = db_session.query(crud.models.Transaction).filter_by(user_id=user.id).all()
    assert len(transactions) == 1
    assert transactions[0].type == "deposit"
    assert transactions[0].amount == 6
    assert transactions[0].description == "Приветственный бонус"
