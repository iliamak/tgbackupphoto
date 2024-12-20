import streamlit as st
from telethon import TelegramClient
from telethon.tl.types import InputMessagesFilterPhotos
import os
import asyncio
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def download_photos(api_id, api_hash, chat_username):
    logger.info(f"[{datetime.now()}] Начинаем процесс скачивания")
    logger.info(f"[{datetime.now()}] Создаем клиент Telegram")
    
    try:
        # Создаем клиент
        client = TelegramClient('anon', api_id, api_hash)
        logger.info(f"[{datetime.now()}] Клиент создан, пытаемся подключиться")
        st.write("Создан клиент Telegram...")

        # Подключаемся
        await client.connect()
        logger.info(f"[{datetime.now()}] Подключение установлено")
        st.write("Подключение установлено...")

        # Проверяем авторизацию
        if not await client.is_user_authorized():
            logger.info(f"[{datetime.now()}] Требуется авторизация")
            st.warning("Требуется авторизация...")
            await client.start()
            
        logger.info(f"[{datetime.now()}] Успешная авторизация")
        st.write("Успешная авторизация...")

        try:
            # Получаем информацию о чате
            logger.info(f"[{datetime.now()}] Пытаемся получить информацию о чате: {chat_username}")
            chat = await client.get_entity(chat_username)
            logger.info(f"[{datetime.now()}] Информация о чате получена")
            st.write("Получен доступ к чату...")
            
            # Получаем сообщения
            logger.info(f"[{datetime.now()}] Запрашиваем список фотографий")
            messages = await client.get_messages(
                chat,
                filter=InputMessagesFilterPhotos,
                limit=None
            )
            
            if not messages:
                logger.warning(f"[{datetime.now()}] Фотографии не найдены")
                st.warning("В этом чате нет фотографий")
                return
                
            logger.info(f"[{datetime.now()}] Найдено {len(messages)} фотографий")
            st.success(f"Найдено фотографий: {len(messages)}")
            
            # Создаем директорию
            chat_name = chat.title if hasattr(chat, 'title') else chat.username
            os.makedirs(f'photos_from_{chat_name}', exist_ok=True)
            
            # Скачиваем фотографии
            progress_bar = st.progress(0)
            for i, message in enumerate(messages):
                logger.info(f"[{datetime.now()}] Скачивание фото {i+1}/{len(messages)}")
                progress = (i + 1) / len(messages)
                progress_bar.progress(progress)
                
                path = await message.download_media(f'./photos_from_{chat_name}/')
                if path:
                    logger.info(f"[{datetime.now()}] Сохранено: {path}")
                    st.write(f"Скачано: {os.path.basename(path)}")
            
            logger.info(f"[{datetime.now()}] Процесс завершен успешно")
            st.success("Все фотографии скачаны!")
            
        except Exception as e:
            logger.error(f"[{datetime.now()}] Ошибка при работе с чатом: {str(e)}")
            st.error(f"Ошибка при работе с чатом: {str(e)}")
            
    except Exception as e:
        logger.error(f"[{datetime.now()}] Ошибка при подключении: {str(e)}")
        st.error(f"Ошибка при подключении к Telegram: {str(e)}")
        
    finally:
        logger.info(f"[{datetime.now()}] Закрываем соединение")
        await client.disconnect()
        logger.info(f"[{datetime.now()}] Соединение закрыто")

# Интерфейс приложения
st.title("📸 Telegram Photos Downloader")
st.write("Скачивайте фотографии из чатов Telegram")

api_id = st.text_input("API ID", type="password")
api_hash = st.text_input("API Hash", type="password")
chat_username = st.text_input("Username чата или номер телефона")

if st.button("Скачать фотографии"):
    logger.info(f"[{datetime.now()}] Нажата кнопка скачивания")
    
    if not api_id or not api_hash or not chat_username:
        logger.warning(f"[{datetime.now()}] Не все поля заполнены")
        st.error("Пожалуйста, заполните все поля")
    else:
        logger.info(f"[{datetime.now()}] Начинаем процесс скачивания")
        st.info("Подключаемся к Telegram...")
        try:
            asyncio.run(download_photos(api_id, api_hash, chat_username))
        except Exception as e:
            logger.error(f"[{datetime.now()}] Критическая ошибка: {str(e)}")
            st.error(f"Критическая ошибка: {str(e)}")

st.markdown("---")
st.markdown(
    "<div style='text-align: center'>Сделано с ❤️ для удобного скачивания фото из Telegram</div>",
    unsafe_allow_html=True
)
