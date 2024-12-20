import streamlit as st
from telethon import TelegramClient
from telethon.tl.types import InputMessagesFilterPhotos
import os
import asyncio
from config import *
from utils import create_download_directory, initialize_client, format_file_size

# Настройка страницы
st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    layout="centered"
)

# Стилизация заголовка
st.title(f"{APP_ICON} {APP_NAME}")
st.write("Скачивайте фотографии из чатов Telegram")

# Основная форма
api_id = st.text_input("API ID", type="password", help="Введите API ID от Telegram")
api_hash = st.text_input("API Hash", type="password", help="Введите API Hash от Telegram")
chat_username = st.text_input(
    "Username чата или номер телефона",
    help="Введите username чата без @ или номер телефона"
)

if st.button("Скачать фотографии"):
    if not api_id or not api_hash or not chat_username:
        st.error("Пожалуйста, заполните все поля")
    else:
        async def download_photos():
            try:
                # Создаем клиента
                client = TelegramClient('anon', api_id, api_hash)
                await client.start()
                
                # Получаем информацию о чате
                chat = await client.get_entity(chat_username)
                
                # Получаем сообщения с фотографиями
                messages = await client.get_messages(
                    chat,
                    filter=InputMessagesFilterPhotos,
                    limit=None
                )
                
                if not messages:
                    st.warning("В этом чате нет фотографий")
                    return
                
                st.success(f"Найдено фотографий: {len(messages)}")
                
                # Создаем директорию для сохранения
                chat_name = chat.title if hasattr(chat, 'title') else chat.username
                download_dir = create_download_directory(chat_name)
                
                # Создаем прогресс бар
                progress_bar = st.progress(0)
                
                # Скачиваем фотографии
                for i, message in enumerate(messages):
                    # Обновляем прогресс
                    progress = (i + 1) / len(messages)
                    progress_bar.progress(progress)
                    
                    # Скачиваем фото
                    path = await message.download_media(f'./{download_dir}/')
                    if path:
                        st.write(f"Скачано: {os.path.basename(path)}")
                
                st.success("Все фотографии успешно скачаны!")
                
            except Exception as e:
                st.error(f"Ошибка: {str(e)}")
            finally:
                await client.disconnect()

        # Запускаем асинхронную функцию
        st.info("Подключаемся к Telegram...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(download_photos())

# Добавляем футер
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        Сделано с ❤️ для удобного скачивания фото из Telegram
    </div>
    """,
    unsafe_allow_html=True
)
