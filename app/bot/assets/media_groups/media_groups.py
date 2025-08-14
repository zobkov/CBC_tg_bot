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
    base_dir = Path(__file__).parent
    # Use absolute paths to local images in the same folder as this file
    start_media_paths = [
        base_dir / "1.jpeg",
        base_dir / "2.jpeg",
        base_dir / "3.jpeg",
    ]

    media_group = compose_media_group([str(p) for p in start_media_paths], caption=caption)
    return media_group.build()



