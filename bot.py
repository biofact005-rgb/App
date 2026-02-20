import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import threading
import os

# --- FLASK SERVER (RENDER KE LIYE ZARURI) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_server():
    # Render khud ek PORT environment variable deta hai
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# Flask ko alag thread mein chalana taaki bot ruk na jaye
server_thread = threading.Thread(target=run_server)
server_thread.start()

# --- BOT CONFIGURATION ---
# Render ke environment variables (Environment) se token nikalna
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YAHAN_APNA_BOT_TOKEN_DALEIN")
bot = telebot.TeleBot(BOT_TOKEN)

# Links store karne ke liye global list
user_links = []

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not user_links:
        bot.reply_to(message, "Pehle mujhe links wali .txt file bhejo!\n\n(Purane links hatane ke liye /delete bhejein)")
        return
    show_link(message.chat.id, 0)

@bot.message_handler(commands=['delete'])
def delete_links(message):
    global user_links
    if not user_links:
        bot.reply_to(message, "Pehele se hi koi links save nahi hain.")
        return
        
    user_links.clear()
    bot.reply_to(message, "🗑️ ✅ Saare purane links delete ho gaye hain! Ab aap nayi .txt file bhej sakte hain.")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    global user_links
    if message.document.file_name.endswith(".txt"):
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            text_content = downloaded_file.decode('utf-8')
            user_links.clear() 
            user_links = [line.strip() for line in text_content.split('\n') if line.strip()]
            
            bot.reply_to(message, f"✅ {len(user_links)} links load ho gaye hain! Ab /start dabayein.")
        except Exception as e:
            bot.reply_to(message, "❌ File read karne mein error aayi.")
    else:
        bot.reply_to(message, "Sirf .txt file bhejein.")

def show_link(chat_id, index, message_id=None):
    if not user_links:
        return
        
    link = user_links[index]
    text = f"{link}\n{link}\n{link}"
    
    markup = InlineKeyboardMarkup()
    buttons = []
    
    if index > 0:
        buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"prev_{index}"))
    if index < len(user_links) - 1:
        buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"next_{index}"))
        
    if buttons:
        markup.add(*buttons)
        
    if message_id:
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=markup, disable_web_page_preview=True)
    else:
        bot.send_message(chat_id=chat_id, text=text, reply_markup=markup, disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if not user_links:
        bot.answer_callback_query(call.id, "Data delete ho chuka hai! Nayi file bhejein.", show_alert=True)
        return
        
    data = call.data
    current_index = int(data.split("_")[1])
    
    if data.startswith("next_"):
        show_link(call.message.chat.id, current_index + 1, call.message.message_id)
    elif data.startswith("prev_"):
        show_link(call.message.chat.id, current_index - 1, call.message.message_id)
        
    bot.answer_callback_query(call.id)

print("Bot chal raha hai...")
bot.infinity_polling()
