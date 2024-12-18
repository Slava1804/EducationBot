# Count Words Bot

### Description
Count Words Bot — это Telegram-бот для подсчета частоты слов в сообщениях.  
Функционал бота включает два уровня доступа:

1. **Обычные пользователи**:
   - Доступ к команде `/word_count` для подсчета слов в сообщении.
   - Ограничение: **5 бесплатных сообщений**. После этого необходимо оформить **подписку**.

2. **Администраторы**:
   - Доступ к статистике выполненных задач пользователей через команду `/admin_stats`.
   - Возможность назначать других пользователей администраторами с помощью `/add_admin`.

### Features
- Подсчет частоты слов в сообщении.
- Ограничение на количество бесплатных запросов.
- Поддержка подписок для расширения доступа.
- Роли пользователей: **администратор** и **пользователь**.

### Requirements
- **Python 3.8+**
- Установленные зависимости из `requirements.txt`
- **Telegram Bot API token** (обязателен)

### Run

1. **Создайте виртуальное окружение и активируйте его**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Для Windows: venv\Scripts\activate

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.