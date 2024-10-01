# Установка и запуск linux

### 1. Скопировать код из гитхаба:
- `git clone https://github.com/OxFF00FF/Reactions_Scrapper_tgbot.git`

### 2. Перейти в папку проекта:
- `cd Reactions_Scrapper_tgbot`

### 3. Создать виртуальное окружение в текущей папке:
- `python -m venv venv` или `python3 -m venv venv`

### 4. Активировать/деактивировать окружение:
- `source venv/bin/activate` · `deactivate`

### 5. Установить зависимости:
- `pip install -r requirements` или `pip3 install -r requirements`

### 6. Настроить переменные окружения:
- `cp .env.example .env` (создание файла .env)
- `nano .env` (открыть.env на редактирвоание)

### 7. Указать переменные:
- API_ID
- API_HASH
- TELEGRAM_BOT_TOKEN
- ADMIN_USER_IDS
- ALLOWED_TELEGRAM_USER_IDS
- BOT_LOGS_GROUP_ID

### 8. Сохранить файл:
- `ctll + x` и подтвердить сохранение `y`

### 9. Запустить бота:
- `python main.py` или `python3 main.py`

### 9. Запустить консоль:
- `python main.py -с` или `python3 main.py -с`


# Установка и запуск Windows

### 1. Установить зависимости:
- Запустить файл `3. INSTALL.bat`

### 2. Установить Windows терминал:
- Запустить файл `WT setup/Windows Terminal Installer.exe`

### 3. Запуск бота:
- Запустить файл `2. START_WT.bat`