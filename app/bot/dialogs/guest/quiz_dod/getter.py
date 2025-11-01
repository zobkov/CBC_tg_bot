import logging

from aiogram_dialog import DialogManager

from app.infrastructure.database.database.db import DB

from .questions import QUESTIONS

logger = logging.getLogger(__name__)


async def _ensure_best_score(dialog_manager: DialogManager) -> None:
	"""Гарантирует наличие лучшего результата в состоянии диалога."""
	if "quiz_dod_score" in dialog_manager.dialog_data:
		return

	db: DB | None = dialog_manager.middleware_data.get("db")
	event = getattr(dialog_manager, "event", None)
	user = getattr(event, "from_user", None) if event else None

	if not db or not user:
		return

	try:
		best_score = await db.quiz_dod.get_best_result(user_id=user.id)
	except Exception:
		logger.exception("[QUIZ_DOD] Failed to load best score for user=%s", getattr(user, "id", "unknown"))
		return

	if best_score is not None:
		dialog_manager.dialog_data["quiz_dod_score"] = best_score


async def get_intro_data(dialog_manager: DialogManager, **kwargs) -> dict:
	"""Подготавливает данные для стартового окна квиза."""
	await _ensure_best_score(dialog_manager)
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
	await _ensure_best_score(dialog_manager)
	score = dialog_manager.dialog_data.get("quiz_dod_last_score", 0)
	best_score = dialog_manager.dialog_data.get("quiz_dod_score")
	name = dialog_manager.dialog_data.get("quiz_dod_name", "друг")
	passed_threshold = score >= len(QUESTIONS)-1
	certificate_requested = dialog_manager.dialog_data.get("quiz_dod_certificate_sent")

	if certificate_requested is None:
		db: DB | None = dialog_manager.middleware_data.get("db")
		event = getattr(dialog_manager, "event", None)
		user = getattr(event, "from_user", None) if event else None

		if db and user:
			try:
				certificate_requested = await db.quiz_dod_users_info.get_certificate_status(user.id)
			except Exception:
				logger.exception(
					"[QUIZ_DOD] Failed to load certificate status for user=%s",
					getattr(user, "id", "unknown"),
				)
				certificate_requested = None

		if certificate_requested is None:
			certificate_requested = False
		else:
			dialog_manager.dialog_data["quiz_dod_certificate_sent"] = certificate_requested

	return {
		"name": name,
		"correct_answers": score,
		"max_questions": len(QUESTIONS),
		"best_score": best_score,
		"has_previous_score": best_score is not None,
		"passed_threshold": passed_threshold,
		"best_updated": dialog_manager.dialog_data.get("quiz_dod_best_updated", False),
		"can_request_certificate": not certificate_requested,
	}
