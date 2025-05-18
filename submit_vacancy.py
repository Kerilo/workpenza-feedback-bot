import logging
   from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
   from telegram.constants import ParseMode
   from telegram.ext import (
       Application,
       CommandHandler,
       MessageHandler,
       filters,
       CallbackQueryHandler,
       ContextTypes,
       ConversationHandler
   )

   # Настройка логирования
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(levelname)s - %(message)s',
       handlers=[
           logging.FileHandler('submit_vacancy.log'),  # Логи в файл
           logging.StreamHandler()  # Логи в консоль
       ]
   )
   logger = logging.getLogger(__name__)

   # --- Конфигурация ---
   TELEGRAM_TOKEN = '7809529722:AAF_7DPAzVPPRYFt9wM-G8gTqN_q_ycofF4'  # Твой токен
   TELEGRAM_CHANNEL_ID = '@rabota_pnz58'  # Исправленный ID канала
   ADMIN_TELEGRAM_ID = '246591923'  # Твой Telegram ID

   # Состояния для ConversationHandler
   SUBMIT = 0

   # --- Клавиатура с кнопкой "Подать вакансию" ---
   submit_keyboard = ReplyKeyboardMarkup(
       [['Подать вакансию']],
       resize_keyboard=True,
       one_time_keyboard=False
   )

   # --- Функции бота ---
   async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
       await update.message.reply_text(
           "Привет! Я бот для подачи вакансий в канал @rabota_pnz58.\n"
           "📌 Чтобы подать вакансию, нажмите на кнопку 'Подать вакансию' ниже 👇\n"
           "Пожалуйста, описывайте работу подробно, чтобы исполнители понимали задачу!",
           reply_markup=submit_keyboard
       )
       return ConversationHandler.END

   async def submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
       await update.message.reply_text(
           "📝 Пожалуйста, отправьте вашу вакансию одним сообщением. Вот пример, как она должна выглядеть:\n\n"
           "Ищу грузчиков для переезда квартиры.\n"
           "💼 Описание работы: Нужно вынести мебель (диван, шкаф, стол) из квартиры на 3-м этаже (лифта нет), погрузить в грузовик и перевезти на другой адрес (5 км). После разгрузить и занести на 2-й этаж (есть лифт). Работа займёт около 4 часов.\n"
           "📍 Район: Арбеково, ул. Ленина, 10 → ул. Победы, 20.\n"
           "💰 Оплата: 3000 руб. за всю работу (или предложите свою цену в комментариях).\n"
           "📅 Дата и время: 20 мая 2025 года, с 9:00 до 13:00.\n"
           "📞 Контакт: +7 (912) 345-67-89 или @username в Telegram.\n\n"
           "Убедитесь, что вы указали:\n"
           "- Подробное описание работы: что нужно сделать, объём задач, сложность, сколько времени займёт.\n"
           "- Район или адрес работы (если есть несколько мест, укажите все).\n"
           "- Сумму оплаты (или запросите расценки в комментариях).\n"
           "- Дату и время (или период выполнения работы).\n"
           "- Хотя бы один контакт для связи (телефон, Telegram, ВКонтакте и т.д.).\n\n"
           "Напишите вашу вакансию ниже:",
           reply_markup=ReplyKeyboardRemove()
       )
       return SUBMIT

   async def handle_vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE):
       vacancy_text = update.message.text
       user = update.message.from_user

       # Формируем текст вакансии для модерации
       message = (
           f"📝 Новая вакансия от {user.first_name} (ID: {user.id})\n\n"
           f"{vacancy_text}"
       )

       # Кнопки для модерации
       keyboard = [
           [
               InlineKeyboardButton("Опубликовать", callback_data=f"publish_{user.id}"),
               InlineKeyboardButton("Отклонить", callback_data=f"reject_{user.id}")
           ]
       ]
       reply_markup = InlineKeyboardMarkup(keyboard)

       # Отправляем админу на модерацию
       try:
           await context.bot.send_message(
               chat_id=ADMIN_TELEGRAM_ID,
               text=message,
               reply_markup=reply_markup,
               parse_mode=ParseMode.HTML
           )
       except Exception as e:
           logger.error(f"Failed to send vacancy for moderation: {e}")
           await update.message.reply_text(
               "Произошла ошибка при отправке вакансии на модерацию. Попробуйте позже.",
               reply_markup=submit_keyboard
           )
           return ConversationHandler.END

       # Уведомляем пользователя и возвращаем клавиатуру
       await update.message.reply_text(
           "Ваша вакансия отправлена на модерацию. Ожидайте!",
           reply_markup=submit_keyboard
       )
       return ConversationHandler.END

   async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
       query = update.callback_query
       await query.answer()

       action, user_id = query.data.split("_")
       user_id = int(user_id)

       # Текст вакансии для публикации
       vacancy_text = query.message.text.replace(f"📝 Новая вакансия от {query.message.chat.first_name} (ID: {user_id})\n\n", "")
       message = (
           f"{vacancy_text}\n\n"
           f'Источник: <a href="https://t.me/PenzaVacancyBot">Пользователь Telegram</a>\n\n'
           f'🔗 <b><a href="https://t.me/rabota_pnz58">Подписаться</a></b> | 📩 <b><a href="https://t.me/PenzaVacancyBot">Предложить вакансию</a></b>'
       )

       if action == "publish":
           # Публикуем в канал
           try:
               await context.bot.send_message(
                   chat_id=TELEGRAM_CHANNEL_ID,
                   text=message,
                   parse_mode=ParseMode.HTML,
                   disable_web_page_preview=True
               )
               # Уведомляем пользователя
               await context.bot.send_message(
                   chat_id=user_id,
                   text="Ваша вакансия опубликована в канале!"
               )
               await query.edit_message_text(
                   text=message + "\n\n✅ Опубликовано в канале",
                   parse_mode=ParseMode.HTML
               )
           except Exception as e:
               logger.error(f"Failed to publish vacancy: {e}")
               await query.edit_message_text(
                   text=message + "\n\n❌ Ошибка при публикации",
                   parse_mode=ParseMode.HTML
               )
       else:
           # Уведомляем пользователя об отклонении
           try:
               await context.bot.send_message(
                   chat_id=user_id,
                   text="Ваша вакансия была отклонена модератором."
               )
               await query.edit_message_text(
                   text=message + "\n\n❌ Отклонено",
                   parse_mode=ParseMode.HTML
               )
           except Exception as e:
               logger.error(f"Failed to notify user of rejection: {e}")
               await query.edit_message_text(
                   text=message + "\n\n❌ Отклонено (ошибка уведомления)",
                   parse_mode=ParseMode.HTML
               )

   async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
       await update.message.reply_text(
           "Подача вакансии отменена.",
           reply_markup=submit_keyboard
       )
       return ConversationHandler.END

   def main():
       app = Application.builder().token(TELEGRAM_TOKEN).build()

       # Настройка ConversationHandler
       conv_handler = ConversationHandler(
           entry_points=[
               CommandHandler('submit', submit),
               MessageHandler(filters.Text(['Подать вакансию']), submit)
           ],
           states={
               SUBMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_vacancy)]
           },
           fallbacks=[CommandHandler('cancel', cancel)]
       )

       app.add_handler(conv_handler)
       app.add_handler(CallbackQueryHandler(button))
       app.add_handler(CommandHandler('start', start))

       logger.info("Vacancy bot started")
       app.run_polling(stop_signals=None)

   if __name__ == '__main__':
       main()