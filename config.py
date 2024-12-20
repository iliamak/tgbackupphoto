from typing import Optional
import streamlit as st

# Константы для приложения
APP_NAME = "Telegram Photos Downloader"
APP_ICON = "📸"
VERSION = "1.0.0"

# Настройки для сохранения файлов
DEFAULT_DOWNLOAD_DIR = "downloaded_photos"
MAX_PHOTOS_DISPLAY = 5  # Максимальное количество отображаемых фото в интерфейсе

# Тексты для интерфейса
INSTRUCTIONS = """
1. Перейдите на https://my.telegram.org
2. Войдите в свой аккаунт
3. Перейдите в 'API development tools'
4. Создайте новое приложение
5. Скопируйте API ID и API Hash
"""

ERROR_MESSAGES = {
    "missing_credentials": "Пожалуйста, заполните все поля",
    "invalid_username": "Неверное имя пользователя или чат не найден",
    "connection_error": "Ошибка подключения к Telegram",
    "download_error": "Ошибка при скачивании фотографий"
}

SUCCESS_MESSAGES = {
    "download_complete": "Все фотографии успешно скачаны!",
    "connection_success": "Успешное подключение к Telegram"
}
