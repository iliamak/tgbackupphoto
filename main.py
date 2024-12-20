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

# Настройка страницы
st.set_page_config(
   page_title="Telegram Photos Downloader",
   page_icon="📸",
   layout="wide"
)

# Инициализация session state
if 'phone' not in st.session_state:
   st.session_state.phone = ''
if 'auth_step' not in st.session_state:
   st.session_state.auth_step = 'phone'
if 'client' not in st.session_state:
   st.session_state.client = None
if 'phone_code_hash' not in st.session_state:
   st.session_state.phone_code_hash = None

async def send_code(api_id, api_hash, phone):
   """Отправка кода подтверждения"""
   try:
       # Логируем начало процесса
       logger.info(f"[{datetime.now()}] Начинаем процесс отправки кода")
       st.write("Инициализация клиента...")

       # Создаем клиент
       client = TelegramClient('anon', api_id, api_hash)
       logger.info(f"[{datetime.now()}] Клиент создан")
       st.write("Клиент создан...")

       # Подключаемся
       logger.info(f"[{datetime.now()}] Попытка подключения")
       await client.connect()
       st.write("Подключение установлено...")

       # Проверяем подключение
       if not await client.is_user_authorized():
           logger.info(f"[{datetime.now()}] Пользователь не авторизован, отправляем код")
           st.write("Отправляем запрос на код...")
           
           # Отправляем запрос на код
           sent = await client.send_code_request(phone=phone)
           
           if sent:
               logger.info(f"[{datetime.now()}] Код успешно отправлен")
               st.success("Код отправлен! Проверьте Telegram.")
               st.session_state.client = client
               st.session_state.phone_code_hash = sent.phone_code_hash
               return True
           else:
               logger.error(f"[{datetime.now()}] Ошибка при отправке кода")
               st.error("Не удалось отправить код")
               return False
               
   except Exception as e:
       logger.error(f"[{datetime.now()}] Ошибка: {str(e)}")
       st.error(f"Произошла ошибка: {str(e)}")
       if "Too many requests" in str(e):
           st.warning("Слишком много запросов. Подождите несколько минут и попробуйте снова.")
       return False

async def download_photos(api_id, api_hash, chat_username):
   """Основная функция для скачивания фотографий"""
   try:
       # Процесс авторизации
       if st.session_state.auth_step == 'phone':
           st.info("Для начала нужно авторизоваться в Telegram")
           
           # Используем форму для ввода телефона
           with st.form(key='phone_form'):
               phone = st.text_input(
                   "Введите номер телефона (в международном формате, например: +79123456789)",
                   value=st.session_state.phone
               )
               submit_button = st.form_submit_button("Отправить код")
               
               if submit_button:
                   logger.info(f"[{datetime.now()}] Попытка отправки кода на номер {phone}")
                   
                   # Проверяем формат номера
                   if not phone.startswith('+'):
                       phone = '+' + phone
                   
                   phone = phone.replace(' ', '').replace('-', '')
                   logger.info(f"[{datetime.now()}] Обработанный номер: {phone}")
                   
                   if await send_code(api_id, api_hash, phone):
                       st.session_state.phone = phone
                       st.session_state.auth_step = 'code'
                       st.rerun()
           return

       elif st.session_state.auth_step == 'code':
           st.info(f"Код отправлен на номер {st.session_state.phone}")
           
           # Используем форму для ввода кода
           with st.form(key='code_form'):
               code = st.text_input("Введите код из Telegram", key="code_input")
               submit_code = st.form_submit_button("Подтвердить код")
               
               if submit_code:
                   try:
                       logger.info(f"[{datetime.now()}] Попытка входа с кодом")
                       await st.session_state.client.sign_in(
                           phone=st.session_state.phone,
                           code=code,
                           phone_code_hash=st.session_state.phone_code_hash
                       )
                       logger.info(f"[{datetime.now()}] Успешный вход")
                       st.session_state.auth_step = 'completed'
                       st.success("Авторизация успешна!")
                       st.rerun()
                   except Exception as e:
                       logger.error(f"[{datetime.now()}] Ошибка при вводе кода: {str(e)}")
                       st.error(f"Ошибка при вводе кода: {str(e)}")
           
           # Кнопка для повторной отправки кода
           if st.button("Отправить код повторно", key="resend_code_btn"):
               if await send_code(api_id, api_hash, st.session_state.phone):
                   st.success("Код отправлен повторно")
           return

       # Скачивание фотографий
       try:
           if not st.session_state.client:
               client = TelegramClient('anon', api_id, api_hash)
               await client.connect()
           else:
               client = st.session_state.client

           logger.info(f"[{datetime.now()}] Получаем информацию о чате")
           chat = await client.get_entity(chat_username)
           
           logger.info(f"[{datetime.now()}] Получаем список фотографий")
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
           download_dir = f'photos_from_{chat_name}'
           os.makedirs(download_dir, exist_ok=True)
           
           progress_bar = st.progress(0)
           status_text = st.empty()
           
           for i, message in enumerate(messages):
               progress = (i + 1) / len(messages)
               progress_bar.progress(progress)
               status_text.text(f"Скачивание фото {i+1} из {len(messages)}")
               
               path = await message.download_media(f'./{download_dir}/')
               if path:
                   logger.info(f"[{datetime.now()}] Скачан файл: {path}")

           st.success(f"Все фотографии успешно скачаны в папку {download_dir}!")
           
       except Exception as e:
           logger.error(f"[{datetime.now()}] Ошибка при скачивании: {str(e)}")
           st.error(f"Ошибка при скачивании: {str(e)}")
           
   except Exception as e:
       logger.error(f"[{datetime.now()}] Общая ошибка: {str(e)}")
       st.error(f"Произошла ошибка: {str(e)}")
   
   finally:
       if st.session_state.client:
           await client.disconnect()

# Основной интерфейс
st.title("📸 Telegram Photos Downloader")
st.write("Скачивайте фотографии из чатов Telegram")

# Основная форма
with st.form(key='main_form'):
   api_id = st.text_input("API ID", type="password")
   api_hash = st.text_input("API Hash", type="password")
   chat_username = st.text_input(
       "Username чата или номер телефона",
       value="me" if st.session_state.auth_step != 'phone' else "",
       help="Используйте 'me' для сохранения фото из избранного"
   )
   submit_main = st.form_submit_button("Скачать фотографии")

   if submit_main:
       if not api_id or not api_hash or not chat_username:
           st.error("Пожалуйста, заполните все поля")
       else:
           asyncio.run(download_photos(api_id, api_hash, chat_username))

# Отладочная информация в сайдбаре
with st.sidebar:
   st.write("Отладочная информация:")
   st.write(f"Текущий шаг: {st.session_state.auth_step}")
   st.write(f"Сохраненный телефон: {st.session_state.phone}")
   st.write(f"Phone code hash: {st.session_state.phone_code_hash}")
   if st.button("Сбросить состояние"):
       for key in st.session_state.keys():
           del st.session_state[key]
       st.rerun()

# Инструкция
with st.expander("Инструкция"):
   st.write("""
   1. Получите API ID и API Hash:
      - Зайдите на https://my.telegram.org
      - Авторизуйтесь
      - Перейдите в 'API development tools'
      - Создайте новое приложение
      
   2. Введите данные в форму:
      - Вставьте полученные API ID и API Hash
      - Для скачивания из избранного введите 'me'
      
   3. При первом использовании:
      - Введите номер телефона в международном формате
      - Введите код, который придет в Telegram
      
   4. Нажмите кнопку "Скачать фотографии"
   """)

# Футер
st.markdown("---")
st.markdown(
   "<div style='text-align: center'>Сделано с ❤️ для удобного скачивания фото из Telegram</div>",
   unsafe_allow_html=True
)
