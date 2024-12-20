import streamlit as st
from telethon import TelegramClient
from telethon.tl.types import InputMessagesFilterPhotos
import os
import asyncio
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def download_photos(api_id, api_hash, chat_username):
    logger.info(f"[{datetime.now()}] Начинаем процесс скачивания")
    
    try:
        client = TelegramClient('anon', api_id, api_hash)
        logger.info(f"[{datetime.now()}] Клиент создан, пытаемся подключиться")
        st.write("Создан клиент Telegram...")

        await client.connect()
        logger.info(f"[{datetime.now()}] Подключение установлено")
        st.write("Подключение установлено...")

        if not await client.is_user_authorized():
            # Добавляем форму для ввода телефона
            phone = st.text_input("Введите номер телефона (в международном формате, например: +79123456789)")
            if phone:
                try:
                    # Отправляем код подтверждения
                    await client.send_code_request(phone)
                    # Показываем поле для ввода кода
                    code = st.text_input("Введите код подтверждения, отправленный в Telegram")
                    if code:
                        try:
                            # Пытаемся войти с полученным кодом
                            await client.sign_in(phone, code)
                            st.success("Успешная авторизация!")
                        except Exception as e:
                            st.error(f"Ошибка при вводе кода: {str(e)}")
                            return
                except Exception as e:
                    st.error(f"Ошибка при отправке кода: {str(e)}")
                    return
            return  # Прерываем выполнение до завершения авторизации

        logger.info(f"[{datetime.now()}] Успешная авторизация")
        st.write("Успешная авторизация...")

        # Остальной код для скачивания фотографий...
        try:
            chat = await client.get_entity(chat_username)
            messages = await client.get_messages(
                chat,
                filter=InputMessagesFilterPhotos,
                limit=None
            )
            
            if not messages:
                st.warning("В этом чате нет фотографий")
                return
                
            st.success(f"Найдено фотографий: {len(messages)}")
            
            chat_name = chat.title if hasattr(chat, 'title') else chat.username
            os.makedirs(f'photos_from_{chat_name}', exist_ok=True)
            
            progress_bar = st.progress(0)
            for i, message in enumerate(messages):
                progress = (i + 1) / len(messages)
                progress_bar.progress(progress)
                
                path = await message.download_media(f'./photos_from_{chat_name}/')
                if path:
                    st.write(f"Скачано: {os.path.basename(path)}")
            
            st.success("Все фотографии скачаны!")
            
        except Exception as e:
            st.error(f"Ошибка при работе с чатом: {str(e)}")
            
    except Exception as e:
        st.error(f"Ошибка при подключении к Telegram: {str(e)}")
        
    finally:
        await client.disconnect()

# Интерфейс приложения
st.title("📸 Telegram Photos Downloader")
st.write("Скачивайте фотографии из чатов Telegram")

with st.expander("Инструкция"):
    st.write("""
    1. Введите API ID и API Hash (получите их на my.telegram.org)
    2. Введите username чата (для избранного используйте 'me')
    3. Нажмите "Скачать фотографии"
    4. При первом использовании потребуется авторизация:
        - Введите номер телефона в международном формате
        - Введите код, который придет в Telegram
    """)

api_id = st.text_input("API ID", type="password")
api_hash = st.text_input("API Hash", type="password")
chat_username = st.text_input("Username чата или номер телефона")

if st.button("Скачать фотографии"):
    if not api_id or not api_hash or not chat_username:
        st.error("Пожалуйста, заполните все поля")
    else:
        asyncio.run(download_photos(api_id, api_hash, chat_username))

st.markdown("---")
st.markdown(
    "<div style='text-align: center'>Сделано с ❤️ для удобного скачивания фото из Telegram</div>",
    unsafe_allow_html=True
)
