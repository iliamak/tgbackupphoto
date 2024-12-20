import streamlit as st
from telethon import TelegramClient
from telethon.tl.types import InputMessagesFilterPhotos
import os
import asyncio
from contextlib import asynccontextmanager

# Функция для безопасного создания и закрытия клиента
@asynccontextmanager
async def create_client(api_id, api_hash):
    client = TelegramClient('anon', api_id, api_hash)
    try:
        await client.start()
        yield client
    finally:
        await client.disconnect()

# Основная функция скачивания
async def download_photos(api_id, api_hash, chat_username):
    async with create_client(api_id, api_hash) as client:
        try:
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
            os.makedirs(f'photos_from_{chat_name}', exist_ok=True)
            
            # Создаем прогресс бар
            progress_bar = st.progress(0)
            
            # Скачиваем фотографии
            for i, message in enumerate(messages):
                try:
                    progress = (i + 1) / len(messages)
                    progress_bar.progress(progress)
                    
                    path = await message.download_media(f'./photos_from_{chat_name}/')
                    if path:
                        st.write(f"Скачано: {os.path.basename(path)}")
                except Exception as e:
                    st.warning(f"Не удалось скачать фото {i+1}: {str(e)}")
                    continue
            
            st.success("Процесс завершен!")
            
        except Exception as e:
            st.error(f"Ошибка: {str(e)}")

# Интерфейс приложения
st.title("📸 Telegram Photos Downloader")
st.write("Скачивайте фотографии из чатов Telegram")

api_id = st.text_input("API ID", type="password")
api_hash = st.text_input("API Hash", type="password")
chat_username = st.text_input("Username чата или номер телефона")

if st.button("Скачать фотографии"):
    if not api_id or not api_hash or not chat_username:
        st.error("Пожалуйста, заполните все поля")
    else:
        try:
            st.info("Подключаемся к Telegram...")
            asyncio.run(download_photos(api_id, api_hash, chat_username))
        except Exception as e:
            st.error(f"Критическая ошибка: {str(e)}")

st.markdown("---")
st.markdown(
    "<div style='text-align: center'>Сделано с ❤️ для удобного скачивания фото из Telegram</div>",
    unsafe_allow_html=True
)
