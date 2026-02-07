import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
import json
import os

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
ASKING_NAME, ASKING_LEVEL, TAKING_TEST, MAIN_MENU = range(4)

# Файл для хранения данных пользователей
USER_DATA_FILE = 'users_data.json'

# Вопросы для теста (5 вопросов на каждый уровень)
TEST_QUESTIONS = {
    'A1': [
        {"question": "Hello! How ___ you?", "options": ["is", "are", "am", "be"], "correct": 1},
        {"question": "My name ___ Anna.", "options": ["is", "are", "am", "be"], "correct": 0},
        {"question": "I ___ from Russia.", "options": ["is", "are", "am", "be"], "correct": 2},
        {"question": "This is ___ apple.", "options": ["a", "an", "the", "-"], "correct": 1},
        {"question": "She ___ a student.", "options": ["is", "are", "am", "be"], "correct": 0},
    ],
    'A2': [
        {"question": "I ___ to school every day.", "options": ["go", "goes", "going", "went"], "correct": 0},
        {"question": "Yesterday I ___ a movie.", "options": ["watch", "watches", "watched", "watching"], "correct": 2},
        {"question": "There ___ many books on the table.", "options": ["is", "are", "was", "be"], "correct": 1},
        {"question": "I have ___ lived in Moscow.", "options": ["ever", "never", "always", "yet"], "correct": 2},
        {"question": "She is ___ than her sister.", "options": ["tall", "taller", "tallest", "more tall"], "correct": 1},
    ],
    'B1': [
        {"question": "If I ___ you, I would study harder.", "options": ["am", "was", "were", "be"], "correct": 2},
        {"question": "The project ___ by next Monday.", "options": ["will finish", "will be finished", "finishes", "is finishing"], "correct": 1},
        {"question": "I've been studying English ___ five years.", "options": ["since", "for", "during", "while"], "correct": 1},
        {"question": "She suggested ___ to the cinema.", "options": ["go", "to go", "going", "goes"], "correct": 2},
        {"question": "This is the book ___ I told you about.", "options": ["what", "which", "who", "where"], "correct": 1},
    ],
    'B2': [
        {"question": "Had I known about it, I ___ you.", "options": ["would tell", "would have told", "will tell", "told"], "correct": 1},
        {"question": "The meeting is ___ to start at 3 PM.", "options": ["supposed", "propose", "supposing", "suppose"], "correct": 0},
        {"question": "She's been working here since she ___ university.", "options": ["graduated", "has graduated", "graduates", "graduating"], "correct": 0},
        {"question": "___ the weather, we decided to go hiking.", "options": ["Despite", "Although", "However", "Nevertheless"], "correct": 0},
        {"question": "I wish I ___ more time to travel.", "options": ["have", "had", "would have", "will have"], "correct": 1},
    ],
    'C1': [
        {"question": "Scarcely ___ the door when it started raining.", "options": ["I closed", "had I closed", "did I close", "I had closed"], "correct": 1},
        {"question": "The proposal is ___ consideration by the committee.", "options": ["under", "in", "on", "at"], "correct": 0},
        {"question": "Not only ___ late, but he also forgot the documents.", "options": ["he was", "was he", "he is", "is he"], "correct": 1},
        {"question": "She speaks English with such ___ that she sounds native.", "options": ["fluent", "fluency", "fluently", "fluentness"], "correct": 1},
        {"question": "___ to your proposal, I'd like to suggest some modifications.", "options": ["With regard", "In regard", "Regarding", "Regards"], "correct": 0},
    ],
}

def load_user_data():
    """Загрузка данных пользователей из файла"""
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_user_data(data):
    """Сохранение данных пользователей в файл"""
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало разговора - приветствие"""
    user = update.effective_user
    
    await update.message.reply_text(
        f"Hey there! 👋 Welcome to *MoraTalk*!\n\n"
        f"Я твой персональный language buddy 🚀\n"
        f"Вместе мы прокачаем твой английский до максимума!\n\n"
        f"Для начала, how should I call you? 😊\n"
        f"Напиши своё имя, чтобы мы могли лучше общаться!",
        parse_mode='Markdown'
    )
    
    return ASKING_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение имени пользователя"""
    user_id = str(update.effective_user.id)
    name = update.message.text.strip()
    
    # Сохраняем имя
    context.user_data['name'] = name
    
    # Создаём клавиатуру для выбора уровня
    keyboard = [
        ['Знаю свой уровень 📊', 'Пройти тест 📝']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(
        f"Nice to meet you, {name}! 🎉\n\n"
        f"So, what's your English level? 🤔\n\n"
        f"Если ты уже знаешь свой уровень (A1, A2, B1, B2, C1) - выбери первую кнопку.\n"
        f"А если не уверен - no worries! Пройди короткий тест и я всё определю сам 😉",
        reply_markup=reply_markup
    )
    
    return ASKING_LEVEL

async def choose_level_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Выбор метода определения уровня"""
    choice = update.message.text
    
    if 'Знаю свой уровень' in choice:
        keyboard = [
            ['A1 - Beginner', 'A2 - Elementary'],
            ['B1 - Intermediate', 'B2 - Upper-Intermediate'],
            ['C1 - Advanced']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        await update.message.reply_text(
            "Perfect! 👌 Выбери свой уровень:",
            reply_markup=reply_markup
        )
        context.user_data['choosing_level'] = True
        return ASKING_LEVEL
        
    else:  # Пройти тест
        context.user_data['test_level'] = 'A1'
        context.user_data['test_question_index'] = 0
        context.user_data['test_correct_answers'] = 0
        
        await update.message.reply_text(
            "Отлично! Let's check your skills! 💪\n\n"
            "Тест состоит из 25 вопросов максимум.\n"
            "Начнём с уровня A1. Поехали! 🚀",
            reply_markup=ReplyKeyboardRemove()
        )
        
        await send_test_question(update, context)
        return TAKING_TEST

async def set_level_directly(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Прямая установка уровня"""
    level_text = update.message.text
    level = level_text.split(' ')[0]  # Получаем A1, A2, и т.д.
    
    context.user_data['level'] = level
    
    # Сохраняем данные пользователя
    user_id = str(update.effective_user.id)
    users_data = load_user_data()
    users_data[user_id] = {
        'name': context.user_data['name'],
        'level': level
    }
    save_user_data(users_data)
    
    await update.message.reply_text(
        f"Awesome! ✨\n\n"
        f"Я создал для тебя индивидуальный план обучения на уровне *{level}*!\n\n"
        f"Get ready to level up your English game! 🎯\n"
        f"Используй /menu чтобы начать своё путешествие! 🚀",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    
    await show_menu(update, context)
    return MAIN_MENU

async def send_test_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка вопроса теста"""
    level = context.user_data['test_level']
    q_index = context.user_data['test_question_index']
    
    question_data = TEST_QUESTIONS[level][q_index]
    
    keyboard = [[opt] for opt in question_data['options']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    total_q = context.user_data.get('total_questions', 0) + 1
    context.user_data['total_questions'] = total_q
    
    await update.message.reply_text(
        f"*Question {total_q}* (Level {level}):\n\n"
        f"{question_data['question']}\n\n"
        f"Choose the correct answer:",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def process_test_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ответа на вопрос теста"""
    level = context.user_data['test_level']
    q_index = context.user_data['test_question_index']
    answer = update.message.text
    
    question_data = TEST_QUESTIONS[level][q_index]
    correct_answer = question_data['options'][question_data['correct']]
    
    if answer == correct_answer:
        context.user_data['test_correct_answers'] += 1
    
    context.user_data['test_question_index'] += 1
    
    # Проверяем, закончились ли вопросы для текущего уровня
    if context.user_data['test_question_index'] >= 5:
        correct = context.user_data['test_correct_answers']
        
        # Проверяем, прошёл ли пользователь уровень (4 из 5)
        if correct >= 4:
            # Переходим на следующий уровень
            levels = ['A1', 'A2', 'B1', 'B2', 'C1']
            current_index = levels.index(level)
            
            if current_index < len(levels) - 1:
                next_level = levels[current_index + 1]
                context.user_data['test_level'] = next_level
                context.user_data['test_question_index'] = 0
                context.user_data['test_correct_answers'] = 0
                
                await update.message.reply_text(
                    f"Great job! 🎉 Ты прошёл уровень {level}!\n"
                    f"Let's move to {next_level}! 💪"
                )
                
                await send_test_question(update, context)
                return TAKING_TEST
            else:
                # Пользователь прошёл C1
                final_level = 'C1'
                await finish_test(update, context, final_level)
                return MAIN_MENU
        else:
            # Пользователь не прошёл текущий уровень
            if level == 'A1':
                final_level = 'A1'
            else:
                levels = ['A1', 'A2', 'B1', 'B2', 'C1']
                current_index = levels.index(level)
                final_level = levels[current_index - 1] if current_index > 0 else 'A1'
            
            await finish_test(update, context, final_level)
            return MAIN_MENU
    else:
        # Продолжаем тест на текущем уровне
        await send_test_question(update, context)
        return TAKING_TEST

async def finish_test(update: Update, context: ContextTypes.DEFAULT_TYPE, level: str):
    """Завершение теста"""
    context.user_data['level'] = level
    
    # Сохраняем данные пользователя
    user_id = str(update.effective_user.id)
    users_data = load_user_data()
    users_data[user_id] = {
        'name': context.user_data['name'],
        'level': level
    }
    save_user_data(users_data)
    
    await update.message.reply_text(
        f"Test completed! 🎊\n\n"
        f"Твой уровень: *{level}*\n\n"
        f"Amazing work! 💫\n"
        f"Я создал для тебя индивидуальный learning plan!\n\n"
        f"Ready to start? Жми /menu! 🚀",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    
    await show_menu(update, context)

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показ главного меню"""
    keyboard = [
        [InlineKeyboardButton("📚 Start a lesson", callback_data='start_lesson')],
        [InlineKeyboardButton("📖 Vocabulary training", callback_data='vocabulary')],
        [InlineKeyboardButton("✨ Premium functions", callback_data='premium')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    name = context.user_data.get('name', 'Friend')
    level = context.user_data.get('level', 'Unknown')
    
    menu_text = (
        f"Hey {name}! 👋\n\n"
        f"Your current level: *{level}*\n\n"
        f"What do you want to do today? 🤔"
    )
    
    if update.message:
        await update.message.reply_text(
            menu_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    else:
        await update.callback_query.message.reply_text(
            menu_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    return MAIN_MENU

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Команда /menu"""
    user_id = str(update.effective_user.id)
    users_data = load_user_data()
    
    if user_id in users_data:
        context.user_data['name'] = users_data[user_id]['name']
        context.user_data['level'] = users_data[user_id]['level']
        await show_menu(update, context)
        return MAIN_MENU
    else:
        await update.message.reply_text(
            "Oops! 😅 Кажется, мы ещё не знакомы.\n"
            "Давай начнём с начала! Используй /start"
        )
        return ConversationHandler.END

async def handle_menu_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка нажатий кнопок меню"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'start_lesson':
        await query.message.reply_text(
            "🎓 *Start a lesson*\n\n"
            "Great choice! Let's begin your lesson! 💪\n\n"
            "Эта функция в разработке... Stay tuned! 🚀",
            parse_mode='Markdown'
        )
    
    elif query.data == 'vocabulary':
        await query.message.reply_text(
            "📖 *Vocabulary training*\n\n"
            "Time to expand your word bank! 📚\n\n"
            "Эта функция скоро появится... Coming soon! ✨",
            parse_mode='Markdown'
        )
    
    elif query.data == 'premium':
        await query.message.reply_text(
            "✨ *Premium functions*\n\n"
            "Unlock exclusive features! 🌟\n\n"
            "Premium возможности:\n"
            "• Неограниченные уроки\n"
            "• Персональный AI-tutor\n"
            "• Speaking practice sessions\n"
            "• Сертификаты и многое другое!\n\n"
            "Contact us для подробностей! 💎",
            parse_mode='Markdown'
        )
    
    await show_menu(update, context)
    return MAIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена разговора"""
    await update.message.reply_text(
        "See you later! 👋\n"
        "Возвращайся скорее! Use /start to begin again.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main():
    """Запуск бота"""
    # Получаем токен из переменной окружения или используем значение по умолчанию
    TOKEN = os.getenv('BOT_TOKEN', '8557327096:AAEcXHHok3-3yzEiWn2ol0zeghhUZwjAhb4')
    
    application = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('menu', menu_command)
        ],
        states={
            ASKING_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)
            ],
            ASKING_LEVEL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: 
                    set_level_directly(u, c) if c.user_data.get('choosing_level') 
                    else choose_level_method(u, c))
            ],
            TAKING_TEST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_test_answer)
            ],
            MAIN_MENU: [
                CallbackQueryHandler(handle_menu_button),
                CommandHandler('menu', menu_command)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)
    
    logger.info("MoraTalk bot is starting... 🚀")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
