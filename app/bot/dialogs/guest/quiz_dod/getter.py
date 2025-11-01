from aiogram_dialog import DialogManager

from .questions import QUESTIONS


async def get_intro_data(dialog_manager: DialogManager, **kwargs) -> dict:
	"""Подготавливает данные для стартового окна квиза."""
	best_score = dialog_manager.dialog_data.get("quiz_dod_score")
	return {
		"best_score": best_score,
		"max_questions": len(QUESTIONS),
		"has_previous_score": best_score is not None,
	}


async def get_question_data(dialog_manager: DialogManager, **kwargs) -> dict:
	"""Возвращает текущий вопрос и варианты ответов."""
	question_index = dialog_manager.dialog_data.get("quiz_dod_question_index", 0)
	question_index = max(0, min(question_index, len(QUESTIONS) - 1))
	question = QUESTIONS[question_index]

	return {
		"current_question": question_index + 1,
		"max_questions": len(QUESTIONS),
		"question_text": question.text,
		"answer_options": "\n".join(question.options),
		"options": [
			{"id": str(idx), "text": option}
			for idx, option in enumerate(question.options)
		],
	}


async def get_results_data(dialog_manager: DialogManager, **kwargs) -> dict:
	"""Готовит данные для окна с результатами квиза."""
	score = dialog_manager.dialog_data.get("quiz_dod_last_score", 0)
	best_score = dialog_manager.dialog_data.get("quiz_dod_score")
	name = dialog_manager.dialog_data.get("quiz_dod_name", "друг")
	passed_threshold = score >= len(QUESTIONS)

	return {
		"name": name,
		"correct_answers": score,
		"max_questions": len(QUESTIONS),
		"best_score": best_score,
		"has_previous_score": best_score is not None,
		"passed_threshold": passed_threshold,
		"best_updated": dialog_manager.dialog_data.get("quiz_dod_best_updated", False),
	}
