import streamlit as st
from telethon import TelegramClient
from telethon.tl.types import InputMessagesFilterPhotos
import os
import asyncio
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация session state
if 'phone' not in st.session_state:
    st.session_state.phone = ''
if 'auth_step' not in st.session_state:
    st.session_state.auth_step = 'phone'
if 'client' not in st.session_state:
    st.session_state.client = None

async def send_code(api_id, api_hash, phone):
    """Отдельная функция для отправки кода"""
    try:
        logger.info(f"[{datetime.now()}] Создаем клиент для отправки кода")
        client = TelegramClient('anon', api_id, api_hash)
        
        logger.info(f"[{datetime.now()}] Подключаемся к Telegram")
        await client.connect()
        
        logger.info(f"[{datetime.now()}] Отправляем запрос на код для номера {phone}")
        code_sent = await client.send_code_request(phone)
        
        logger.info(f"[{datetime.now()}] Код успешно отправлен")
        st.session_state.client = client
        return True
        
    except Exception as e:
        logger.error(f"[{datetime.now()}] Ошибка при отправке кода: {str(e)}")
        st.error(f"Ошибка при отправке кода: {str(e)}")
        return False

async def download_photos(api_id, api_hash, chat_username):
    try:
        if st.session_state.auth_step == 'phone':
            st.info("Для начала нужно авторизоваться в Telegram")
            phone = st.text_input(
                "Введите номер телефона (в международном формате, например: +79123456789)",
                value=st.session_state.phone
            )
            
            if st.button("Отправить код"):
                logger.info(f"[{datetime.now()}] Попытка отправки кода на номер {phone}")
                if await send_code(api_id, api_hash, phone):
                    st.session_state.phone = phone
                    st.session_state.auth_step = 'code'
                    st.rerun()
            return

        elif st.session_state.auth_step == 'code':
            st.info(f"Код отправлен на номер {st.session_state.phone}")
            code = st.text_input("Введите код из Telegram", key="code_input")
            
            if st.button("Подтвердить код"):
                try:
                    logger.info(f"[{datetime.now()}] Попытка входа с кодом")
                    await st.session_state.client.sign_in(st.session_state.phone, code)
                    logger.info(f"[{datetime.now()}] Успешный вход")
                    st.session_state.auth_step = 'completed'
                    st.success("Авторизация успешна!")
                    st.rerun()
                except Exception as e:
                    logger.error(f"[{datetime.now()}] Ошибка при вводе кода: {str(e)}")
                    st.error(f"Ошибка при вводе кода: {str(e)}")
            return

        # Основной код скачивания...
        [остальной код остается без изменений]

    except Exception as e:
        logger.error(f"[{datetime.now()}] Ошибка в основном процессе: {str(e)}")
        st.error(f"Произошла ошибка: {str(e)}")

# Интерфейс приложения
st.title("📸 Telegram Photos Downloader")

# Добавляем отладочную информацию
st.sidebar.write("Отладочная информация:")
st.sidebar.write(f"Текущий шаг: {st.session_state.auth_step}")
st.sidebar.write(f"Сохраненный телефон: {st.session_state.phone}")

api_id = st.text_input("API ID", type="password")
api_hash = st.text_input("API Hash", type="password")
chat_username = st.text_input("Username чата или номер телефона")

if st.button("Скачать фотографии"):
    if not api_id or not api_hash or not chat_username:
        st.error("Пожалуйста, заполните все поля")
    else:
        asyncio.run(download_photos(api_id, api_hash, chat_username))
