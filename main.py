import streamlit as st
from telethon import TelegramClient
from telethon.tl.types import InputMessagesFilterPhotos
import os
import asyncio
import logging
from datetime import datetime
import re
import uuid

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
if 'session_id' not in st.session_state:
   st.session_state.session_id = str(uuid.uuid4())  # Уникальный ID сессии

def sanitize_filename(filename):
    """Очищает имя файла от недопустимых символов"""
    # Заменяем недопустимые символы на подчеркивание
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

async def send_code(api_id, api_hash, phone):
   """Отправка кода подтверждения"""
   client = None
   try:
       # Логируем начало процесса
       logger.info(f"[{datetime.now()}] Начинаем процесс отправки кода")
       status_msg = st.empty()
       status_msg.info("Инициализация клиента...")

       # Проверка API ID и Hash
       if not api_id.isdigit():
           st.error("API ID должен содержать только цифры")
           logger.error(f"[{datetime.now()}] Некорректный API ID: {api_id}")
           return False
       
       if len(api_hash) < 10:
           st.error("API Hash слишком короткий, проверьте введенные данные")
           logger.error(f"[{datetime.now()}] Некорректный API Hash (слишком короткий)")
           return False

       # Создаем клиент с уникальным ID сессии
       try:
           client = TelegramClient(f'session_{st.session_state.session_id}', int(api_id), api_hash)
           logger.info(f"[{datetime.now()}] Клиент создан")
           status_msg.info("Клиент создан, подключаемся к Telegram...")
       except Exception as e:
           logger.error(f"[{datetime.now()}] Ошибка при создании клиента: {str(e)}")
           st.error(f"Ошибка при создании клиента: {str(e)}")
           return False

       # Подключаемся с таймаутом и обработкой ошибок
       try:
           await asyncio.wait_for(client.connect(), timeout=30)
           logger.info(f"[{datetime.now()}] Подключение установлено")
           status_msg.info("Подключение к Telegram установлено!")
       except asyncio.TimeoutError:
           logger.error(f"[{datetime.now()}] Таймаут при подключении к Telegram")
           st.error("Превышено время ожидания при подключении к Telegram. Проверьте интернет-соединение.")
           if client and client.is_connected():
               await client.disconnect()
           return False
       except Exception as e:
           logger.error(f"[{datetime.now()}] Ошибка при подключении: {str(e)}")
           st.error(f"Ошибка при подключении к Telegram: {str(e)}")
           if client and client.is_connected():
               await client.disconnect()
           return False

       # Проверка подключения и отправка кода
       try:
           if not await client.is_user_authorized():
               logger.info(f"[{datetime.now()}] Пользователь не авторизован, отправляем код")
               status_msg.info("Отправляем запрос на код авторизации...")
               
               # Отправляем запрос на код с таймаутом и отображением прогресса
               try:
                   # Для улучшения UX - показываем пользователю что происходит
                   progress_bar = st.progress(0)
                   for i in range(10):
                       progress_bar.progress((i + 1) * 10)
                       if i == 3:
                           status_msg.info("Связываемся с серверами Telegram...")
                       elif i == 6:
                           status_msg.info("Формируем запрос на код авторизации...")
                       elif i == 9:
                           status_msg.info("Ожидаем ответ от Telegram...")
                       await asyncio.sleep(0.2)  # Небольшая задержка для анимации
                   
                   # Фактическая отправка кода
                   sent = await asyncio.wait_for(
                       client.send_code_request(phone=phone),
                       timeout=30  # 30 секунд таймаут
                   )
                   
                   if sent:
                       logger.info(f"[{datetime.now()}] Код успешно отправлен. Phone code hash: {sent.phone_code_hash}")
                       st.success("Код успешно отправлен! Проверьте приложение Telegram на вашем телефоне.")
                       st.session_state.client = client
                       st.session_state.phone_code_hash = sent.phone_code_hash
                       return True
                   else:
                       logger.error(f"[{datetime.now()}] Ошибка при отправке кода - пустой ответ")
                       st.error("Не удалось отправить код. Получен пустой ответ от Telegram API.")
                       await client.disconnect()
                       return False
               except asyncio.TimeoutError:
                   logger.error(f"[{datetime.now()}] Таймаут при отправке кода")
                   st.error("Превышено время ожидания при отправке кода. Возможно, серверы Telegram перегружены.")
                   await client.disconnect()
                   return False
               except Exception as e:
                   logger.error(f"[{datetime.now()}] Ошибка при отправке кода: {str(e)}")
                   error_message = str(e)
                   if "Too many requests" in error_message:
                       st.error("Слишком много запросов к API Telegram. Подождите несколько минут и попробуйте снова.")
                   elif "The phone number is invalid" in error_message:
                       st.error("Указан некорректный номер телефона. Проверьте формат и попробуйте снова.")
                   elif "API ID invalid" in error_message or "APP_ID_INVALID" in error_message:
                       st.error("Указан некорректный API ID. Проверьте данные на my.telegram.org")
                   elif "API Hash invalid" in error_message or "API_HASH_INVALID" in error_message:
                       st.error("Указан некорректный API Hash. Проверьте данные на my.telegram.org")
                   else:
                       st.error(f"Ошибка при отправке кода: {error_message}")
                   await client.disconnect()
                   return False
           else:
               logger.info(f"[{datetime.now()}] Пользователь уже авторизован")
               st.success("Вы уже авторизованы!")
               st.session_state.client = client
               st.session_state.auth_step = 'completed'
               return True
       except Exception as e:
           logger.error(f"[{datetime.now()}] Ошибка при проверке авторизации: {str(e)}")
           st.error(f"Ошибка при проверке авторизации: {str(e)}")
           if client and client.is_connected():
               await client.disconnect()
           return False
               
   except Exception as e:
       logger.error(f"[{datetime.now()}] Общая ошибка в процессе отправки кода: {str(e)}")
       st.error(f"Произошла ошибка: {str(e)}")
       if client and client.is_connected():
           await client.disconnect()
       return False

async def download_photos(api_id, api_hash, chat_username):
   """Основная функция для скачивания фотографий"""
   client = None
   try:
       # Процесс авторизации
       if st.session_state.auth_step == 'phone':
           st.info("Для начала нужно авторизоваться в Telegram")
           
           # Форма для ввода телефона
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
           
           # Форма для ввода кода
           with st.form(key='code_form'):
               code = st.text_input("Введите код из Telegram", key="code_input")
               submit_code = st.form_submit_button("Подтвердить код")
               
               if submit_code:
                   try:
                       logger.info(f"[{datetime.now()}] Попытка входа с кодом")
                       # Проверяем, что клиент существует и подключен
                       if st.session_state.client and not st.session_state.client.is_connected():
                           await st.session_state.client.connect()
                           
                       await asyncio.wait_for(
                           st.session_state.client.sign_in(
                               phone=st.session_state.phone,
                               code=code,
                               phone_code_hash=st.session_state.phone_code_hash
                           ),
                           timeout=30  # 30 секунд таймаут
                       )
                       logger.info(f"[{datetime.now()}] Успешный вход")
                       st.session_state.auth_step = 'completed'
                       st.success("Авторизация успешна!")
                       st.rerun()
                   except asyncio.TimeoutError:
                       logger.error(f"[{datetime.now()}] Таймаут при вводе кода")
                       st.error("Превышено время ожидания. Попробуйте снова.")
                   except Exception as e:
                       logger.error(f"[{datetime.now()}] Ошибка при вводе кода: {str(e)}")
                       st.error(f"Ошибка при вводе кода: {str(e)}")
           
           # Кнопка повторной отправки кода вне формы
           if st.button("Отправить код повторно", key="resend_code_btn"):
               if await send_code(api_id, api_hash, st.session_state.phone):
                   st.success("Код отправлен повторно")
           return

       # Скачивание фотографий
       try:
           # Проверяем, существует ли клиент, подключен ли он
           if not st.session_state.client or not st.session_state.client.is_connected():
               # Если клиент существует, но не подключен - пробуем переподключить
               if st.session_state.client:
                   try:
                       await st.session_state.client.connect()
                       client = st.session_state.client
                   except Exception:
                       # Если переподключение не удалось - создаем новый клиент
                       client = TelegramClient(f'session_{st.session_state.session_id}', api_id, api_hash)
                       await client.connect()
               else:
                   # Если клиента нет - создаем новый
                   client = TelegramClient(f'session_{st.session_state.session_id}', api_id, api_hash)
                   await client.connect()
           else:
               client = st.session_state.client

           # Проверяем авторизацию
           if not await client.is_user_authorized():
               st.warning("Необходима авторизация. Пожалуйста, войдите в аккаунт.")
               st.session_state.auth_step = 'phone'
               st.rerun()
               return

           logger.info(f"[{datetime.now()}] Получаем информацию о чате")
           try:
               chat = await asyncio.wait_for(
                   client.get_entity(chat_username),
                   timeout=30  # 30 секунд таймаут
               )
           except asyncio.TimeoutError:
               st.error("Превышено время ожидания при получении информации о чате. Проверьте подключение.")
               return
           except Exception as e:
               st.error(f"Не удалось найти чат: {str(e)}")
               return
           
           logger.info(f"[{datetime.now()}] Получаем список фотографий")
           try:
               messages = await asyncio.wait_for(
                   client.get_messages(
                       chat,
                       filter=InputMessagesFilterPhotos,
                       limit=None
                   ),
                   timeout=60  # 60 секунд таймаут для больших чатов
               )
           except asyncio.TimeoutError:
               st.error("Превышено время ожидания при получении списка фотографий. Возможно, в чате слишком много сообщений.")
               return
           except Exception as e:
               st.error(f"Ошибка при получении списка фотографий: {str(e)}")
               return
           
           if not messages:
               st.warning("В этом чате нет фотографий")
               return
           
           st.success(f"Найдено фотографий: {len(messages)}")
           
           # Безопасное получение имени чата
           if hasattr(chat, 'title') and chat.title:
               chat_name = chat.title
           elif hasattr(chat, 'username') and chat.username:
               chat_name = chat.username
           else:
               chat_name = "unknown_chat"
           
           # Очистка имени чата от недопустимых символов
           safe_chat_name = sanitize_filename(chat_name)
           download_dir = f'photos_from_{safe_chat_name}'
           os.makedirs(download_dir, exist_ok=True)
           
           progress_bar = st.progress(0)
           status_text = st.empty()
           failed_photos = []
           
           for i, message in enumerate(messages):
               progress = (i + 1) / len(messages)
               progress_bar.progress(progress)
               status_text.text(f"Скачивание фото {i+1} из {len(messages)}")
               
               try:
                   # Скачивание с таймаутом
                   path = await asyncio.wait_for(
                       message.download_media(f'./{download_dir}/'),
                       timeout=120  # 2 минуты на скачивание одного файла
                   )
                   if path:
                       logger.info(f"[{datetime.now()}] Скачан файл: {path}")
               except asyncio.TimeoutError:
                   logger.error(f"[{datetime.now()}] Таймаут при скачивании файла из сообщения {message.id}")
                   failed_photos.append(message.id)
               except Exception as e:
                   logger.error(f"[{datetime.now()}] Ошибка при скачивании файла из сообщения {message.id}: {str(e)}")
                   failed_photos.append(message.id)

           # Отчет о результатах
           if failed_photos:
               st.warning(f"Скачивание завершено с ошибками. Не удалось скачать {len(failed_photos)} из {len(messages)} фотографий.")
           else:
               st.success(f"Все фотографии успешно скачаны в папку {download_dir}!")
           
       except Exception as e:
           logger.error(f"[{datetime.now()}] Ошибка при скачивании: {str(e)}")
           st.error(f"Ошибка при скачивании: {str(e)}")
           
   except Exception as e:
       logger.error(f"[{datetime.now()}] Общая ошибка: {str(e)}")
       st.error(f"Произошла ошибка: {str(e)}")
   
   finally:
       # Безопасное закрытие соединения
       if client and client.is_connected():
           await client.disconnect()

# Основной интерфейс
st.title("📸 Telegram Photos Downloader")
st.write("Скачивайте фотографии из чатов Telegram")

# Основные поля ввода (без формы)
api_id = st.text_input(
    "API ID", 
    value=st.session_state.get('saved_api_id', ''),
    type="password",
    help="Цифровой ID из my.telegram.org"
)
api_hash = st.text_input(
    "API Hash", 
    value=st.session_state.get('saved_api_hash', ''),
    type="password",
    help="Строковый хеш из my.telegram.org"
)
chat_username = st.text_input(
   "Username чата или номер телефона",
   value=st.session_state.get('saved_chat_username', "me" if st.session_state.auth_step == 'completed' else ""),
   help="Используйте 'me' для сохранения фото из избранного"
)

if st.button("Скачать фотографии", key="main_button"):
   # Сохраняем введенные данные в session_state, чтобы они не терялись при перезагрузке
   st.session_state.saved_api_id = api_id
   st.session_state.saved_api_hash = api_hash
   st.session_state.saved_chat_username = chat_username
   
   if not api_id or not api_hash or not chat_username:
       st.error("Пожалуйста, заполните все поля")
   else:
       # Выводим информационное сообщение перед запуском асинхронной задачи
       info_placeholder = st.empty()
       info_placeholder.info("Запускаем процесс... Пожалуйста, не закрывайте страницу.")
       
       # Запускаем асинхронную задачу в отдельном цикле событий
       try:
           # Создаем и настраиваем отдельный цикл событий
           loop = asyncio.new_event_loop()
           asyncio.set_event_loop(loop)
           
           # Добавляем прогресс-бар для визуальной обратной связи
           progress_placeholder = st.empty()
           with progress_placeholder.container():
               st.progress(0.25)
               st.caption("Инициализация...")
           
           # Запускаем асинхронную задачу
           loop.run_until_complete(download_photos(api_id, api_hash, chat_username))
           
           # Удаляем прогресс-плейсхолдер после завершения
           progress_placeholder.empty()
       except Exception as e:
           logger.error(f"[{datetime.now()}] Ошибка при запуске асинхронной задачи: {str(e)}")
           st.error(f"Ошибка при выполнении задачи: {str(e)}")
       finally:
           # Обязательно закрываем цикл событий
           loop.close()
           # Очищаем информационное сообщение
           info_placeholder.empty()

# Отладочная информация в сайдбаре
with st.sidebar:
   st.write("Отладочная информация:")
   st.write(f"Текущий шаг: {st.session_state.auth_step}")
   st.write(f"Сохраненный телефон: {st.session_state.phone}")
   st.write(f"Уникальный ID сессии: {st.session_state.session_id}")
   
   if st.button("Сбросить состояние"):
       # Безопасная очистка session_state
       keys_to_delete = list(st.session_state.keys())
       for key in keys_to_delete:
           del st.session_state[key]
       st.session_state.session_id = str(uuid.uuid4())  # Создаем новый уникальный ID сессии
       st.session_state.auth_step = 'phone'
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
