from pathlib import Path

from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.types.input_file import FSInputFile


def compose_media_group(paths: list[str], caption: str | None = None) -> MediaGroupBuilder:
        """Build a MediaGroup from local file paths.

        - caption is optional; if None or empty, no caption will be sent.
        - Telegram requires InputFile objects for local uploads; passing plain strings
            may be treated as URLs/file_ids and lead to WEBPAGE_MEDIA_EMPTY.
        """
        media_group = MediaGroupBuilder(caption=caption) if caption else MediaGroupBuilder()
        for p in paths:
                media_group.add_photo(FSInputFile(p))
        return media_group


def build_start_media_group(caption: str | None = None):
    # Используем папку с новыми изображениями
    images_dir = Path(__file__).parent.parent / "images" / "start"
    
    # Используем все PNG файлы из папки start (1.png - 9.png)
    start_media_paths = [
        images_dir / "1.png",
        images_dir / "2.png",
        images_dir / "3.png",
        images_dir / "4.png",
        images_dir / "5.png",
        images_dir / "6.png",
        images_dir / "7.png",
        images_dir / "8.png",
        images_dir / "9.png",
    ]

    media_group = compose_media_group([str(p) for p in start_media_paths], caption=caption)
    return media_group.build()



