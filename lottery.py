import logging
import asyncio
import os
import json
from flask import Flask, render_template
import threading
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '8724280923:AAF-RmLnpfee08R3XgjYn7aRWO8uh3XbgZQ'
ADMIN_ID = 5997569372

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

total_numbers = 20
DATA_FILE = "slots_data.json"

def load_slots():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
        except Exception:
            pass
    return {i: None for i in range(1, total_numbers + 1)}

def save_slots():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(slots, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Error saving slots: {e}")

slots = load_slots()

def generate_slots_text():
    text = "📌 **የዕጣ ቁጥሮች ዝርዝር**\n\n"
    for num in range(1, total_numbers + 1):
        user = slots.get(num)
        if user:
            text += f"{num} 👉 {user}\n"
        else:
            text += f"{num} 👉 \n"
    return text

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    welcome_text = (
        "ሰላም! እንኳን ወደ ዕጣ ማውጫ ቦት በደህና መጡ።\n\n"
        "አሁን ያሉትን ቁጥሮች ለማየት /slots የሚለውን ይጫኑ።\n"
        "ቁጥር ለመያዝ በቀጥታ የሚፈልጉትን **ቁጥር ብቻ** ይላኩ (ምሳሌ፦ 5)"
    )
    await message.reply(welcome_text)

@dp.message(Command("slots"))
async def show_slots(message: types.Message):
    text = generate_slots_text()
    await message.reply(text)

@dp.message(Command("approve"))
async def approve_payment(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("ይህንን ትዕዛዝ መጠቀም የሚችሉት አድሚኖች ብቻ ናቸው ❌")
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.reply("አጠቃቀም: /approve [ቁጥር] [የተጠቃሚ_ስም]\nምሳሌ: /approve 5 yaq")
        return

    num_str, user_name = parts[1], parts[2]

    if num_str.isdigit():
        num = int(num_str)
        if num in slots:
            slots[num] = f"{user_name} ✅"
            save_slots()
            updated_text = generate_slots_text()
            await message.reply(f"ክፍያው ተረጋግጧል! ቁጥር {num} በይፋ ተዘግቷል። 🟢\n\n{updated_text}")
        else:
            await message.reply("የተሳሳተ ቁጥር ነው።")
    else:
        await message.reply("እባክዎ ትክክለኛ ቁጥር ያስገቡ።")

@dp.message(Command("draw"))
async def draw_lottery(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("ይህንን ትዕዛዝ መጠቀም የሚችሉት አድሚኖች ብቻ ናቸው ❌")
        return

    approved_nums = [str(num) for num, user in slots.items() if user is not None and "✅" in str(user)]

    if not approved_nums:
        await message.reply("እስካሁን የጸደቀ (✅) የተያዘ ቁጥር የለም። እጣ ማውጣት አይቻልም! ❌")
        return

    nums_string = ",".join(approved_nums)
    wheel_url = f"https://lottery-bot-10.onrender.com/?numbers={nums_string}"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎡 ዊሉን በብሮውዘር ክፈትና አሽከርክር", url=wheel_url)]
        ]
    )

    await message.answer(f"🎯 **እጣ ማውጫ ዊል ዝግጁ ነው!**\n\nየጸደቁት ቁጥሮች፦ **{nums_string}**\n\nከታች ያለውን አዝራር በመጫን አሽከርክረው፦", reply_markup=keyboard)

@dp.message()
async def book_slot_direct(message: types.Message):
    text = message.text.strip() if message.text else ""

    if text.isdigit():
        num = int(text)

        if num in slots:
            if slots[num] is None:
                user_name = message.from_user.first_name
                slots[num] = f"{user_name} (ክፍያ በመጠበቅ ላይ ⏳)"
                save_slots()

                payment_info = (
                    f"ቁጥር {num} ተይዟል! 📌\n\n"
                    "እባክዎ ክፍያውን በሚከተለው አካውንት ይፈጽሙ፡\n"
                    "• ንግድ ባንክ (CBE): 1000XXXXXXXXXX\n"
                    "• ቴሌብር (Telebirr): 0925270516\n\n"
                    "ክፍያውን ከፈጸሙ በኋላ የክፍያውን ማረጋገጫ ለአድሚኑ ይላኩ።"
                )
                await message.reply(payment_info)
            else:
                await message.reply(f"ይቅርታ! ቁጥር {num} አስቀድሞ ተይዟል ❌")
        else:
            await message.reply(f"እባክዎ ከ 1 እስከ {total_numbers} ያሉትን ቁጥሮች ብቻ ይምረጡ።")

# --- Flask ዌብ ሰርቨር እና ዊል (HTML) ማገናኛ ---
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('wheel.html')

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    asyncio.run(main())
