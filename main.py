import streamlit as st
from telethon import TelegramClient
from telethon.tl.types import InputMessagesFilterPhotos
import os
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

# Создаем боковую панель с инструкциями
with st.sidebar:
    st.header("Инструкция")
    st.write(INSTRUCTIONS)
    st.divider()
    st.caption(f"Версия: {VERSION}")

# Создаем основной интерфейс с вкладками
tab1, tab2 = st.tabs(["Скачивание", "Настройки"])

with tab1:
    # Основная форма
    with st.form("download_form"):
        api_id = st.text_input("API ID", type="password", help="Введите API ID от Telegram")
        api_hash = st.text_input("API Hash", type="password", help="Введите API Hash от Telegram")
        chat_username = st.text_input(
            "Username чата или номер телефона",
            help="Введите username чата без @ или номер телефона"
        )
        
        submit_button = st.form_submit_button("Скачать фотографии")

    # Обработка нажатия кнопки
    if submit_button:
        if not api_id or not api_hash or not chat_username:
            st.error(ERROR_MESSAGES["missing_credentials"])
        else:
            try:
                async def download_photos():
                    # Инициализация клиента
                    client = await initialize_client(api_id, api_hash)
                    if not client:
                        return

                    try:
                        # Получаем информацию о чате
                        chat = await client.get_entity(chat_username)
                        chat_name = chat.title if hasattr(chat, 'title') else chat.username
                        
                        # Создаем контейнер для статуса
                        status_container = st.empty()
                        
                        # Получаем сообщения с фотографиями
                        status_container.info("Получаем список фотографий...")
                        messages = await client.get_messages(
                            chat,
                            filter=InputMessagesFilterPhotos,
                            limit=None
                        )
                        
                        if not messages:
                            st.warning("В этом чате нет фотографий")
                            return
                        
                        # Показываем информацию о найденных фото
                        st.success(f"Найдено фотографий: {len(messages)}")
                        
                        # Создаем директорию для сохранения
                        download_dir = create_download_directory(chat_name)
                        
                        # Создаем прогресс бар
                        progress_bar = st.progress(0)
                        info_text = st.empty()
                        
                        # Скачиваем фотографии
                        for i, message in enumerate(messages):
                            # Обновляем прогресс
                            progress = (i + 1) / len(messages)
                            progress_bar.progress(progress)
                            
                            # Скачиваем фото
                            path = await message.download_media(f'./{download_dir}/')
                            
                            # Показываем информацию о текущем файле
                            if os.path.exists(path):
                                size = format_file_size(os.path.getsize(path))
                                info_text.text(f"Скачано {i+1} из {len(messages)}: {os.path.basename(path)} ({size})")
                        
                        # Завершение
                        progress_bar.progress(1.0)
                        st.success(SUCCESS_MESSAGES["download_complete"])
                        
                        # Показываем информацию о расположении файлов
                        st.info(f"Все файлы сохранены в папке: {download_dir}")
                        
                    except Exception as e:
                        st.error(f"Ошибка: {str(e)}")
                    finally:
                        await client.disconnect()

                # Запускаем процесс скачивания
                st.info("Подключаемся к Telegram...")
                import asyncio
                asyncio.run(download_photos())
                
            except Exception as e:
                st.error(f"Ошибка при подключении: {str(e)}")

with tab2:
    st.write("Настройки будут добавлены в следующих версиях")

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
