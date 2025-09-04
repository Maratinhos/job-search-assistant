import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, User as TUser, Message, Chat, CallbackQuery, ReplyKeyboardRemove
from telegram.ext import ConversationHandler, Application, ContextTypes

from bot.handlers.states import MAIN_MENU, AWAITING_SURVEY_ANSWER
from bot.handlers.survey import start_survey, handle_survey_answer, cancel_survey
from db import crud
from db.models import User, Survey, SurveyAnswer

@pytest.fixture
def mock_db_session():
    """Фикстура для мока сессии БД."""
    db_session = MagicMock()
    user = User(id=1, chat_id=12345)

    # Мокаем get_or_create_user, чтобы он возвращал нашего пользователя
    with patch('db.crud.get_or_create_user', return_value=user):
        # Мокаем create_survey_answer
        with patch('db.crud.create_survey_answer', return_value=SurveyAnswer(id=1, user_id=1, survey_id=1, answer="Хорошо")):
            yield db_session

@pytest.mark.asyncio
async def test_start_survey_with_active_survey(mock_db_session):
    """Тест начала опроса при наличии активного опроса."""
    active_survey = Survey(id=1, question="Как дела?", options="Хорошо,Нормально,Плохо", is_active=True)
    with patch('bot.handlers.survey.get_db', return_value=iter([mock_db_session])), \
         patch('db.crud.get_active_survey', return_value=active_survey):

        update = AsyncMock(spec=Update)
        update.callback_query = AsyncMock(spec=CallbackQuery)
        update.callback_query.message = AsyncMock(spec=Message)
        update.callback_query.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}

        result = await start_survey(update, context)

        update.callback_query.answer.assert_called_once()
        update.callback_query.message.reply_text.assert_called_once()
        assert "Опрос: Как дела?" in update.callback_query.message.reply_text.call_args[0][0]
        assert context.user_data["active_survey_id"] == 1
        assert result == AWAITING_SURVEY_ANSWER

@pytest.mark.asyncio
async def test_start_survey_no_active_survey(mock_db_session):
    """Тест начала опроса при отсутствии активных опросов."""
    with patch('bot.handlers.survey.get_db', return_value=iter([mock_db_session])), \
         patch('db.crud.get_active_survey', return_value=None), \
         patch('bot.handlers.survey.show_main_menu', new_callable=AsyncMock) as mock_show_main_menu:

        update = AsyncMock(spec=Update)
        update.callback_query = AsyncMock(spec=CallbackQuery)
        update.callback_query.edit_message_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        result = await start_survey(update, context)

        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_with("Спасибо, но сейчас нет активных опросов.")
        mock_show_main_menu.assert_called_once()
        assert result == MAIN_MENU

@pytest.mark.asyncio
async def test_handle_survey_answer(mock_db_session):
    """Тест обработки ответа на опрос."""
    with patch('bot.handlers.survey.get_db', return_value=iter([mock_db_session])), \
         patch('bot.handlers.survey.show_main_menu', new_callable=AsyncMock) as mock_show_main_menu:

        update = AsyncMock(spec=Update)
        update.message = AsyncMock(spec=Message)
        update.message.text = "Хорошо"
        update.effective_chat = Chat(id=12345, type="private")
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {"active_survey_id": 1}

        result = await handle_survey_answer(update, context)

        crud.create_survey_answer.assert_called_once()
        update.message.reply_text.assert_called_once_with("Спасибо за ваш ответ!", reply_markup=update.message.reply_text.call_args[1]['reply_markup'])
        assert "active_survey_id" not in context.user_data
        mock_show_main_menu.assert_called_once()
        assert result == MAIN_MENU

@pytest.mark.asyncio
async def test_cancel_survey(mock_db_session):
    """Тест отмены опроса."""
    with patch('bot.handlers.survey.show_main_menu', new_callable=AsyncMock) as mock_show_main_menu:
        update = AsyncMock(spec=Update)
        update.message = AsyncMock(spec=Message)
        update.message.reply_text = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {"active_survey_id": 1}

        result = await cancel_survey(update, context)

        update.message.reply_text.assert_called_once_with("Опрос отменен.", reply_markup=update.message.reply_text.call_args[1]['reply_markup'])
        assert "active_survey_id" not in context.user_data
        mock_show_main_menu.assert_called_once()
        assert result == MAIN_MENU
