from dataclasses import dataclass


@dataclass(frozen=True)
class Question:
    text: str
    options: list[str]
    correct: int  # индекс правильного варианта


QUESTIONS: list[Question] = [
    Question(
        "Столица Финляндии?",
        ["Осло", "Стокгольм", "Хельсинки", "Копенгаген"],
        2,
    ),
    Question(
        "HTTP-метод для получения ресурса:",
        ["PUT", "POST", "GET", "DELETE"],
        2,
    ),
    Question(
        "Сложность бинарного поиска:",
        ["O(n)", "O(log n)", "O(n log n)", "O(1)"],
        1,
    ),
]
