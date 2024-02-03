import traceback
try:
    import asyncio
    import os
    import random
    import shutil
    import sys
    import time
    from datetime import datetime
    from threading import Thread
    import tkinter as tk
    from ttkthemes import ThemedTk
    from tkinter import ttk, filedialog, messagebox
    
    import requests

    import socks
    from telethon import types
    from telethon.errors import RPCError
    from telethon.tl.functions.channels import LeaveChannelRequest

    from config import (
        timeforsleep,
        reaction,
        limit,
        proxy_type,
        random_reaction,
        max_joins_per_session,
    )
    from log_config import logging
    from opentele.api import API, UseCurrentSession
    from opentele.exception import TFileNotFound
    from opentele.td import TDesktop



    def is_exists_tdatas_and_sessions():
        """Проверяет наличие папки tdatas и sessions и создает их, если они отсутствуют."""
        if not os.path.exists("./tdatas"):
            os.mkdir("./tdatas")
        if not os.path.exists("./sessions"):
            os.mkdir("./sessions")


    is_exists_tdatas_and_sessions()

    def open_chats_file_callback():
        os.system("start notepad chats.txt")

    def open_proxy_file_callback():
        os.system("start notepad proxy.txt")


    chats = open("chats.txt", "r").read().split("\n")

    MAX_JOINS_PER_SESSION = max_joins_per_session
    RANDOM_REACTION = random_reaction
    TIME_FOR_SLEEP = timeforsleep
    REACTION = reaction
    LIMIT = limit
    PROXY_TYPE = proxy_type



    class Proxy:
        """Класс для работы с прокси."""

        def __init__(self):
            self.proxy_type = int(PROXY_TYPE)

        def fetch_proxy_from_link(self, link, index):
            proxies = requests.get(link)

            addr = proxies.text.split("\n")[index+26].split(":")[0]
            port = proxies.text.split("\n")[index+26].split(":")[1]

            return addr, port

        def get_proxy(self, index):
            if self.proxy_type == 0:
                link = open("proxy.txt", "r").read().strip()
                return self.fetch_proxy_from_link(link, index)
            if self.proxy_type == 1:
                proxies = open("proxy.txt", "r").read().split("\n")
                proxy = proxies[index].split(":")
                addr = proxy[0]
                port = proxy[1]
                logging.info(f"{addr} {port}")
                return addr, int(port)

            if self.proxy_type == 2:
                return "", ""


    def current_timestamp():
        """Возвращает текущую дату и время в формате dd/mm/yyyy hh:mm:ss"""
        now = datetime.now()
        formatted_date_time = now.strftime("%d/%m/%Y %H:%M:%S")
        return f"Дата и время: {formatted_date_time} | "


    def start_multiple_telegram_sessions():
        """Запускает несколько сессий Telegram."""
        try:
            os.remove("./tdatas/.gitkeep")
        except FileNotFoundError:
            logging.info("Файл для удаления не найден.")
        except PermissionError:
            logging.error("Недостаточно прав для удаления файла.")
        except Exception as e:
            logging.error(f"Произошла ошибка при попытке удаления файла: {e}")
        session_names = os.listdir("./tdatas")
        random.shuffle(session_names)
        for session_index, session_name in enumerate(session_names):
            clear_session_data(session_name)
            t = Thread(
                target=start_single_session,
                args=(
                    session_index,
                    session_name,
                ),
            )
            t.start()
            time.sleep(1)


    def start_single_session(session_index, session_name):
        """Запускает одну сессию Telegram."""
        asyncio.run(main(session_index, session_name))


    def clear_session_data(session_name):
        """Удаляет данные сессии."""
        try:
            for file in os.listdir(f"./tdatas/{session_name}"):
                if str(file) in ["dumps", "emoji", "user_data"]:
                    shutil.rmtree(f"./tdatas/{session_name}/{file}")
        except FileNotFoundError:
            logging.error("Файл для удаления не найден.")
        except PermissionError:
            logging.error("Недостаточно прав для удаления файла.")
        except Exception as e:
            logging.error(f"Произошла ошибка при попытке удаления файла: {e}")



    async def get_joined_chats(client):
        """Возвращает список ID чатов, в которых состоит аккаунт."""
        joined = []
        try:
            for dialog in await client.get_dialogs():
                joined.append(dialog.entity.id)
        except Exception as e:
            logging.error(f"Error: {e}")
            return False

        return joined


    async def authorize_telegram_session(proxy, tname):
        tdesk = None
        try:
            tdesk = TDesktop(f"tdatas/{tname}")
        except ConnectionError as e:
            logging.error(f"{tname} - Ошибка соединения: {e}")
        except TFileNotFound:
            pass
        except Exception as e:
            logging.error(f"Нерабочий аккаунт! {e}")
            sys.exit(1)

        if not tdesk:
            try:
                tdesk = TDesktop(f"tdatas/{tname}", keyFile='datas')
            except Exception as e:
                logging.error(f"Нерабочий аккаунт! {e}")
                sys.exit(1)

        api = API.TelegramIOS.Generate()
        prox = Proxy()
        addr, port = prox.get_proxy(proxy)
        logging.info(f"{tname} | Прокси: {addr}:{port}")
        logging.info(f"{tname} | Авторизация")
        if addr == "" or port == "":
            try:
                client = await tdesk.ToTelethon(
                    f"sessions/{tname}.session",
                    UseCurrentSession,
                    api,
                )
                await client.connect()
            except BaseException:
                logging.error("Нерабочий аккаунт!")
                return
        else:
            try:
                client = await tdesk.ToTelethon(
                    f"sessions/{tname}.session",
                    UseCurrentSession,
                    api,
                    proxy=(socks.SOCKS5, addr, int(port), True),
                    connection_retries=0,
                    retry_delay=1,
                    auto_reconnect=True,
                    request_retries=0,
                )
                await client.connect()
            except Exception as e:
                if "ConnectionError" in str(e):
                    logging.warning(f"{tname} | Нерабочие прокси: {addr}:{port}")
                    logging.info(f"{tname} | Заменяем прокси")
                    return authorize_telegram_session(proxy + 1, tname)
                else:
                    logging.error(f"Нерабочий аккаунт! {e}")
                    return

        return client


    def print_chat_statistics(
            num_joined_chats,
            num_already_in_chats,
            num_sent_join_requests,
            num_failed_joins):
        logging.info(
            f"Вступил в {num_joined_chats} чатов, уже состоит в {num_already_in_chats} чатах, отправил {num_sent_join_requests} запросов на вступление, не удалось вступить в {num_failed_joins} чатов"
        )


    async def main(proxy_index, session_name):
        """Основная функция."""
        with open("chats.txt", "r") as chats:
            chats_to_keep = chats.read().split("\n")

        logging.info("Запуск сессии")

        try:
            client = await authorize_telegram_session(proxy_index, session_name)
            if not client.is_connected():
                await client.connect()
        except ValueError:
            logging.error(f"{session_name} - Авторизация не удалась!")
            return
        except RPCError as e:
            logging.error(f"Telethon RPC Error: {e}")
        except ConnectionError:
            logging.error("Connection Error")
        except Exception as e:
            logging.error(f"Неизвестная ошибка: {e}")
        
        if not client.is_connected():
            await client.connect()

        joined_chats = await get_joined_chats(client)
        if not joined_chats:
            logging.info(f"{session_name} - Нет чатов или групп")
            return
        dialogs = await client.get_dialogs()
        channels = [d.entity for d in dialogs if isinstance(d.entity, (types.Channel, types.Chat))]
        
        for channel in channels:
            try:
                if isinstance(channel.id, types.Channel) and channel.title not in chats_to_keep:
                    await client(LeaveChannelRequest(channel))
                    logging.info(f"Left channel: {channel.title}")
            except Exception as e:
                logging.info(f"Failed to leave channel {channel.title}: {e}")




        client.disconnect()
        logging.info(f"{session_name} Завершено")


    def load_instructions():
        try:
            with open("instruction.txt", "r", encoding='utf-8-sig') as file:
                return file.read()
        except:  
            return "Не удалось прочитать"

    def restart_script():
        """Перезапускает скрипт."""
        python = sys.executable
        os.execl(python, python, * sys.argv)
    
    def exit_script():
        sys.exit(0)

    def start_thread(target, *args):
        thread = Thread(target=target, args=args)
        thread.start()


    def create_widgets(root):
        # Создаем фреймы для кнопок и инструкций
        button_frame = ttk.Frame(root,borderwidth=0)
        instructions_frame = ttk.Frame(root,borderwidth=0)

        button_frame.pack(side=tk.RIGHT, fill=tk.Y)
        instructions_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Кнопки
        open_chats_file_button = ttk.Button(button_frame, text="Open file with chats", command=open_chats_file_callback)
        open_chats_file_button.pack(pady=10)

        open_proxy_file_button = ttk.Button(button_frame, text="Open file with proxy", command=open_proxy_file_callback)
        open_proxy_file_button.pack(pady=10)


        start_without_archive_button = ttk.Button(button_frame, text="Start", command=start_multiple_telegram_sessions)
        start_without_archive_button.pack(pady=10)
        restart_button = ttk.Button(button_frame, text="Restart", command=restart_script)
        restart_button.pack(pady=10)

        exit_button = ttk.Button(button_frame, text="Exit", command=exit_script)
        exit_button.pack(pady=10)


        instructions_text = tk.Text(instructions_frame, bg='#2E2E2E', fg='#FFFFFF', font=("Arial", 12), padx=10, pady=10)  # Устанавливаем темный фон и светлый текст
        instructions_text.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        instructions_text.insert(tk.END, load_instructions())

    # Создаем основное окно
    root = ThemedTk(theme="equilux")  # выбираем тему equilux из библиотеки ttkthemes для темного режима
    root.title("TGChatCore")
    root.geometry("1000x600")

    create_widgets(root)
    root.mainloop()
except Exception as e:
    logging.error(f"Произошла ошибка: {e}")
    traceback.print_exc()
    input("Нажмите Enter, чтобы выйти...")
    raise