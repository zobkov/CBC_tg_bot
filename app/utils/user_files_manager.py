"""
Утилиты для работы с файлами решений пользователей
"""
import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import re

logger = logging.getLogger(__name__)


class UserFilesManager:
    """Менеджер для работы с файлами решений пользователей"""
    
    def __init__(self, base_path: str = "storage/solutions"):
        self.base_path = Path(base_path)
        self.trash_path = Path("storage/trash")
        
        # Создаем базовые директории
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.trash_path.mkdir(parents=True, exist_ok=True)
    
    def _get_user_directory(self, user_id: int, task_number: int, department: str) -> Path:
        """Получает путь к директории пользователя в отделе: storage/solutions/department/user_id/"""
        # Очищаем название отдела от недопустимых символов
        safe_department = re.sub(r'[^\w\s-]', '', department).strip()
        safe_department = re.sub(r'[-\s]+', '_', safe_department)
        
        user_dir = self.base_path / safe_department / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    def _get_next_file_number(self, user_dir: Path) -> int:
        """Получить следующий номер файла для пользователя"""
        if not user_dir.exists():
            return 1
        
        # Ищем файлы с паттерном *_номер-файла_*
        max_number = 0
        for file_path in user_dir.iterdir():
            if file_path.is_file():
                # Извлекаем номер из имени файла
                match = re.search(r'_(\d+)_', file_path.name)
                if match:
                    file_number = int(match.group(1))
                    max_number = max(max_number, file_number)
        
        return max_number + 1
    
    def _sanitize_filename(self, filename: str) -> str:
        """Очистить имя файла от недопустимых символов"""
        # Удаляем недопустимые символы, оставляем буквы, цифры, точки, дефисы, подчеркивания
        clean_name = re.sub(r'[^\w\s.-]', '', filename)
        # Заменяем множественные пробелы и дефисы на одиночные подчеркивания
        clean_name = re.sub(r'[-\s]+', '_', clean_name)
        return clean_name.strip('_')
    
    def save_user_file(self, file_path: str, user_id: int, task_number: int, 
                      department: str, full_name: str, username: str, 
                      original_filename: str) -> str:
        """
        Сохранить файл пользователя
        
        Args:
            file_path: Путь к исходному файлу
            user_id: ID пользователя
            task_number: Номер задания (1, 2, 3)
            department: Название отдела
            full_name: ФИО пользователя
            username: Username пользователя
            original_filename: Оригинальное имя файла
            
        Returns:
            str: Путь к сохраненному файлу
        """
        try:
            # Получаем директорию пользователя: storage/solutions/department/user_id/
            user_dir = self._get_user_directory(user_id, task_number, department)
            
            # Получаем следующий номер файла
            file_number = self._get_next_file_number(user_dir)
            
            # Извлекаем расширение из оригинального имени
            original_path = Path(original_filename)
            extension = original_path.suffix
            clean_original_name = self._sanitize_filename(original_path.stem)
            
            # Очищаем данные пользователя
            clean_full_name = self._sanitize_filename(full_name.replace(' ', '_'))
            clean_username = self._sanitize_filename(username) if username else 'no_username'
            
            # Формируем новое имя файла: фамилия_ИИ_юзернейм_номер-файла_оригинальное-название.расширение
            new_filename = f"{clean_full_name}_{clean_username}_{file_number}_{clean_original_name}{extension}"
            
            # Полный путь к новому файлу
            new_file_path = user_dir / new_filename
            
            # Копируем файл
            shutil.copy2(file_path, new_file_path)
            
            logger.info(f"Сохранен файл пользователя {user_id} в отделе {department}: {new_file_path}")
            return str(new_file_path)
            
        except Exception as e:
            logger.error(f"Ошибка сохранения файла пользователя {user_id}: {e}")
            raise
    
    def get_user_files_list(self, user_id: int, task_number: int, department: str) -> List[Dict[str, Any]]:
        """
        Получить список файлов пользователя для отдела
        
        Returns:
            List[Dict]: Список файлов с информацией [{"number": 1, "original_name": "name.ext", "file_path": "path"}, ...]
        """
        try:
            user_dir = self._get_user_directory(user_id, task_number, department)
            
            if not user_dir.exists():
                return []
            
            files_info = []
            
            for file_path in user_dir.iterdir():
                if file_path.is_file():
                    # Извлекаем номер файла и оригинальное название
                    filename = file_path.name
                    
                    # Паттерн: фамилия_имя_отчество_username_номер_оригинальное-название.расширение
                    # Ищем номер файла в имени с помощью регулярного выражения
                    match = re.search(r'_(\d+)_', filename)
                    if match:
                        try:
                            file_number = int(match.group(1))
                            # Находим позицию номера в строке и берем все после него
                            number_pos = match.end()
                            original_part = filename[number_pos:]
                            
                            files_info.append({
                                "number": file_number,
                                "original_name": original_part,
                                "file_path": str(file_path)
                            })
                        except (ValueError, IndexError):
                            # Если не можем распарсить, добавляем как есть
                            files_info.append({
                                "number": 0,
                                "original_name": filename,
                                "file_path": str(file_path)
                            })
                    else:
                        # Если номер не найден, добавляем как есть
                        files_info.append({
                            "number": 0,
                            "original_name": filename,
                            "file_path": str(file_path)
                        })
            
            # Сортируем по номеру файла
            files_info.sort(key=lambda x: x["number"])
            
            return files_info
            
        except Exception as e:
            logger.error(f"Ошибка получения списка файлов пользователя {user_id}: {e}")
            return []
    
    def delete_all_user_files(self, user_id: int, task_number: int, department: str) -> bool:
        """
        Удалить все файлы пользователя (переместить в trash)
        
        Returns:
            bool: True если успешно
        """
        try:
            user_dir = self._get_user_directory(user_id, task_number, department)
            
            if not user_dir.exists():
                return True
            
            # Перемещаем все файлы в trash
            for file_path in user_dir.iterdir():
                if file_path.is_file():
                    trash_file_path = self.trash_path / file_path.name
                    
                    # Если файл с таким именем уже есть в trash, добавляем timestamp
                    if trash_file_path.exists():
                        from datetime import datetime
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        stem = trash_file_path.stem
                        suffix = trash_file_path.suffix
                        trash_file_path = self.trash_path / f"{stem}_{timestamp}{suffix}"
                    
                    shutil.move(str(file_path), str(trash_file_path))
                    logger.info(f"Файл {file_path.name} перемещен в trash")
            
            # Удаляем пустую директорию пользователя
            if user_dir.exists() and not any(user_dir.iterdir()):
                user_dir.rmdir()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления файлов пользователя {user_id}: {e}")
            return False
    
    def get_user_files_count(self, user_id: int, task_number: int, department: str) -> int:
        """Получить количество файлов пользователя"""
        files_list = self.get_user_files_list(user_id, task_number, department)
        return len(files_list)