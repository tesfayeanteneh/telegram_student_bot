from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, Filters
import pandas as pd
import os
import configparser

# Read configuration
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), '../config/config.ini'))
TOKEN = config['TELEGRAM']['TOKEN']
GROUP_CHAT_ID = '@RoboticsScience'  # Group username

# Define the path for the CSV file
data_dir = os.path.join(os.path.dirname(__file__), '../data')
csv_file_path = os.path.join(data_dir, 'status_selections.csv')

# Ensure the data directory exists
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# Initialize or load the DataFrame to store the selections
if os.path.exists(csv_file_path):
    try:
        selections_data = pd.read_csv(csv_file_path)
    except pd.errors.EmptyDataError:
        selections_data = pd.DataFrame(columns=["Name", "Selection"])
else:
    selections_data = pd.DataFrame(columns=["Name", "Selection"])

# Command handler for /start command in private chat
def start(update: Update, context: CallbackContext) -> None:
    if update.message.chat.type == "private":
        keyboard = [
            [InlineKeyboardButton("Working", callback_data='working')],
            [InlineKeyboardButton("Not Working", callback_data='not working')],
            [InlineKeyboardButton("Others", callback_data='others')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(chat_id=GROUP_CHAT_ID, text="Please select your status:", reply_markup=reply_markup)
        update.message.reply_text("Buttons have been sent to the group.")
    else:
        update.message.reply_text("This command is only available in private chat.")

# Callback query handler for button press
def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    # Save the selection in the context user data
    context.user_data['selection'] = query.data
    query.edit_message_text(text="Please enter your full name:")

def record_name(update: Update, context: CallbackContext) -> None:
    name = update.message.text
    selection = context.user_data.get('selection')

    # Save selection to DataFrame
    new_entry = pd.DataFrame([[name, selection]], columns=["Name", "Selection"])
    global selections_data
    selections_data = pd.concat([selections_data, new_entry], ignore_index=True)
    selections_data.to_csv(csv_file_path, index=False)  # Save to CSV file

# Command handler to send the CSV file in private chat
def get_file(update: Update, context: CallbackContext) -> None:
    if update.message.chat.type == "private":
        if os.path.exists(csv_file_path):
            update.message.reply_text("Sending the status selections file...")
            context.bot.send_document(chat_id=update.effective_chat.id, document=open(csv_file_path, 'rb'))
        else:
            update.message.reply_text("No selections file found.")
    else:
        update.message.reply_text("This command is only available in private chat.")

# Main function to start the bot
def main() -> None:
    # Create the Updater and pass it your bot's token
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("getfile", get_file))
    dispatcher.add_handler(CallbackQueryHandler(button, pattern='^(working|not working|others)$'))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, record_name))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
