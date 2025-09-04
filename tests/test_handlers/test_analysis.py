import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.handlers import analysis
from ai.actions import ACTION_REGISTRY

@pytest.mark.anyio
@patch('bot.handlers.analysis.read_text_from_file')
@patch('bot.handlers.analysis.save_text_to_file')
@patch('bot.handlers.analysis.get_ai_client')
@patch('bot.handlers.analysis.models')
@patch('bot.handlers.analysis.crud')
@patch('bot.handlers.analysis.get_db')
@patch('builtins.open', new_callable=MagicMock)
async def test_perform_analysis_new_analysis_success(
    mock_open, mock_get_db, mock_crud, mock_models, mock_get_ai,
    mock_save_text, mock_read_text, update_mock, context_mock
):
    """
    Тестирует успешное выполнение нового анализа, сохранение результатов в файлы
    и отправку результата пользователю.
    """
    user_id, resume_id, vacancy_id = 1, 10, 20
    action = "analyze_match"
    context_mock.user_data['selected_vacancy_id'] = vacancy_id

    mock_db = MagicMock()
    mock_get_db.return_value = iter([mock_db])

    mock_crud.get_or_create_user.return_value = MagicMock(id=user_id)
    mock_crud.get_user_resume.return_value = MagicMock(id=resume_id, file_path="resume.txt")
    mock_crud.get_vacancy_by_id.return_value = MagicMock(id=vacancy_id, file_path="vacancy.txt")
    mock_crud.get_analysis_result.return_value = None  # No cached result

    mock_ai_client = MagicMock()
    mock_analysis_data = {
        "match_analysis": "Match analysis content.",
        "cover_letter": "Cover letter content.",
    }
    mock_ai_response = {"json": mock_analysis_data, "usage": {"cost": 0.005, "total_tokens": 300}}
    mock_ai_client.get_consolidated_analysis.return_value = mock_ai_response
    mock_get_ai.return_value = mock_ai_client

    # Мокируем файловые операции
    mock_open.return_value.read.return_value = "file content"
    mock_save_text.side_effect = lambda text, subfolder: f"storage/{subfolder}/{text[:5]}.txt"

    def read_side_effect(file_path):
        if "Match" in file_path:
            return "Match analysis content."
        elif "Cover" in file_path:
            return "Cover letter content."
        return None

    mock_read_text.side_effect = read_side_effect

    await analysis._perform_analysis(update_mock, context_mock, action)

    mock_ai_client.get_consolidated_analysis.assert_called_once()
    assert mock_save_text.call_count == 2
    mock_save_text.assert_any_call("Match analysis content.", "analysis_results")
    mock_save_text.assert_any_call("Cover letter content.", "analysis_results")

    mock_analysis_result = mock_models.AnalysisResult.return_value
    mock_db.add.assert_called_once_with(mock_analysis_result)
    assert mock_analysis_result.match_analysis == "storage/analysis_results/Match.txt"
    assert mock_analysis_result.cover_letter == "storage/analysis_results/Cover.txt"
    mock_db.commit.assert_called_once()

    update_mock.callback_query.message.reply_text.assert_called()
    last_call_args = update_mock.callback_query.message.reply_text.call_args
    assert "Match analysis content." in last_call_args.kwargs['text']

@pytest.mark.anyio
@patch('bot.handlers.analysis.read_text_from_file')
@patch('bot.handlers.analysis.get_ai_client')
@patch('bot.handlers.analysis.crud')
@patch('bot.handlers.analysis.get_db')
async def test_perform_analysis_cached_result_success(
    mock_get_db, mock_crud, mock_get_ai, mock_read_text, update_mock, context_mock
):
    """
    Тестирует успешное получение результата анализа из кэша (файла).
    """
    user_id, resume_id, vacancy_id = 1, 10, 20
    action = "generate_letter"
    context_mock.user_data['selected_vacancy_id'] = vacancy_id

    mock_db = MagicMock()
    mock_get_db.return_value = iter([mock_db])

    mock_crud.get_or_create_user.return_value = MagicMock(id=user_id)
    mock_crud.get_user_resume.return_value = MagicMock(id=resume_id)
    mock_crud.get_vacancy_by_id.return_value = MagicMock(id=vacancy_id)

    cached_path = "storage/analysis_results/cached_letter.txt"
    mock_analysis_result = MagicMock()
    setattr(mock_analysis_result, ACTION_REGISTRY[action]["db_field"], cached_path)
    mock_crud.get_analysis_result.return_value = mock_analysis_result

    cached_content = "This is the cached cover letter."
    mock_read_text.return_value = cached_content

    await analysis._perform_analysis(update_mock, context_mock, action)

    mock_get_ai.assert_not_called()
    mock_read_text.assert_called_once_with(cached_path)

    update_mock.callback_query.message.reply_text.assert_called()
    last_call_args = update_mock.callback_query.message.reply_text.call_args
    action_details = ACTION_REGISTRY.get(action)
    expected_header = action_details["response_header"]
    assert expected_header in last_call_args.kwargs['text']
    assert cached_content in last_call_args.kwargs['text']
