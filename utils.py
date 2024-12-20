import os
from typing import Optional
import streamlit as st
from telethon import TelegramClient
from telethon.tl.types import InputMessagesFilterPhotos

def create_download_directory(chat_name: str) -> str:
    """Создает директорию для скачивания фотографий."""
    directory = f'photos_from_{chat_name}'
    os.makedirs(directory, exist_ok=True)
    return directory

async def initialize_client(api_id: str, api_hash: str) -> Optional[TelegramClient]:
    """Инициализирует клиент Telegram."""
    try:
        client = TelegramClient('anon', api_id, api_hash)
        await client.start()
        return client
    except Exception as e:
        st.error(f"Ошибка при инициализации клиента: {str(e)}")
        return None

def format_file_size(size_in_bytes: int) -> str:
    """Форматирует размер файла в человекочитаемый вид."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.1f} TB"
