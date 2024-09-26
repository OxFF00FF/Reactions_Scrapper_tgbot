import os
from datetime import datetime, timedelta
import json
from Bot.colors import *

filename = 'channel_messages.json'
file_path = os.path.join(os.path.abspath('data'), filename)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        if isinstance(o, bytes):
            return list(o)

        return json.JSONEncoder.default(self, o)


def get_user_data() -> dict:
    print(f"\n{YELLOW}👋  Привет. Я бот для получения сообщений из тегерам каналов{WHITE}\n")

    result = {}
    print(f"🤖  Откуда получить сообщения?")
    input_channel = input(f'{CYAN}▶️  URL телеграм канала: {WHITE}')

    if input_channel.startswith('https://t.me/') or input_channel.startswith('t.me/'):
        result['channel'] = input_channel

        print(f"\n🤖  Как нужно получить сообщения?\n"
              f"{LIGHT_YELLOW}1 │  {RESET}📅  {YELLOW}Диапазон дат (от начальной до конечной даты) {WHITE}\n"
              f"{LIGHT_YELLOW}2 │  {RESET}🔢  {YELLOW}Количество (от последнего от указанного количества) {WHITE}")
        choice = input(f"{CYAN}▶️  Выберите действие (1/2): {WHITE}")

        if choice == '1':
            print(f"\n{LIGHT_YELLOW}ℹ️  Укажите диапазон дат в формате: {BOLD}{LIGHT_BLUE}ДД.ММ.ГГГГ{RESET}{WHITE}")
            print(f"{LIGHT_YELLOW}ℹ️  Например: {BOLD}01.01.2024, 30.01.2024{RESET}{WHITE}\n")

            start_date = input(f"{CYAN}▶️  Начальная дата: ")
            end_date = input(f"{CYAN}▶️  Конечная дата:  ")
            try:
                start_date = datetime.strptime(start_date, '%d.%m.%Y')
                end_date = datetime.strptime(end_date, '%d.%m.%Y')
                end_date = end_date + timedelta(hours=23, minutes=59, seconds=59)
            except Exception as e:
                print(f"\n{LIGHT_RED}🚫 Неверно указан формат даты: {e}")
                exit(1)

            if start_date >= end_date:
                print(f"{RED}🚫  Дата начала должна быть меньше даты окончания{WHITE}")

            print(f"{YELLOW}ℹ️  Получаем сообщения за период: {start_date} - {end_date}\n{WHITE}")
            result['date_range'] = {'start': start_date, 'end': end_date}

        elif choice == '2':
            print(f"\n🤖  Сколько сообщений нужно получить?")
            total_count_limit = input(f"{CYAN}▶️  Укажите количество: {WHITE}")

            if total_count_limit.isdigit():
                print(f"{YELLOW}ℹ️  Получаем сообщений: {total_count_limit}{WHITE}\n")
                result['messages_count'] = int(total_count_limit)
            else:
                print(f"\n{LIGHT_RED}🚫  Количество должно быть числом{WHITE}")

        else:
            print(f"\n{LIGHT_RED}🚫  Такой опции нет: {choice}{WHITE}")
            exit(1)

    else:
        print(f"\n{LIGHT_RED}🚫  Указанный url не является телеграм каналом{WHITE}")
        exit(1)

    return result


def save_file(messages):
    if not os.path.exists('data'):
        os.makedirs('data')

    with open(file_path, 'w') as f:
        json.dump(messages, f, cls=DateTimeEncoder, ensure_ascii=True, indent=4)


def read_file():
    with open(file_path, 'r') as file:
        data = json.loads(file.read())
        return data


def line_before(blank_line=True, width=50):
    text = "\n┌" + "─" * width + "┐"
    if blank_line:
        print(text)
    else:
        print(text.strip())


def line_after(blank_line=True, width=50):
    text = "└" + "─" * width + "┘\n"
    if blank_line:
        print(text)
    else:
        print(text.strip())
