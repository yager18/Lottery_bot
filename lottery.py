import sqlite3
import random
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# --- Configuration ---
BOT_TOKEN = '8724280923:AAF-RmLnpfee08R3XgjYn7aRWO8uh3XbgZQ'
ADMIN_ID = 5997569372
DB_PATH = 'lottery.db'

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS participants 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user_id INTEGER, 
                  full_name TEXT, 
                  ticket_num INTEGER, 
                  status TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- User Actions ---
@dp.message(Command("start"))
async def start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎟️ ትኬት ግዛ (የ1 ትኬት ዋጋ 50 ብር ነው)", callback_data="buy_ticket"))
    builder.row(types.InlineKeyboardButton(text="📊 የኔ ትኬቶች", callback_data="my_status"))
    await message.answer("እንኳን ወደ ያገርሰው የእጣ ትኬት መሸጫ ቦት በሰላም መጡ!", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "buy_ticket")
async def buy(callback: types.CallbackQuery):
    await callback.message.answer("💳 የንግድ ባንክ: ያገርሰው አዕምሮ: 1000501218212 \nቴሌብር: ያገርሰው: 0925270516 \n\nደረሰኝ ይላኩ።")

@dp.message(F.photo)
async def forward_receipt(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="✅ አጽድቅ", callback_data=f"ok_{message.from_user.id}"))
    builder.row(types.InlineKeyboardButton(text="❌ ሰርዝ", callback_data=f"no_{message.from_user.id}"))
    await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"አዲስ ደረሰኝ ከ: {message.from_user.full_name}", reply_markup=builder.as_markup())
    await message.reply("ደረሰኝዎ ደርሷል!")

@dp.callback_query(F.data.startswith("ok_"))
async def approve(callback: types.CallbackQuery):
    try:
        u_id = int(callback.data.split("_")[1])
        ticket_num = random.randint(1000, 9999)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO participants (user_id, full_name, ticket_num, status) VALUES (?, ?, ?, ?)", 
                  (u_id, "ተሳታፊ", ticket_num, "Approved"))
        conn.commit()
        conn.close()
        await bot.send_message(u_id, f"🎉 ተረጋግጧል! ቁጥርዎ: {ticket_num}")
        await callback.message.edit_caption(caption=f"✅ ጸድቋል! ቁጥር: {ticket_num}")
    except Exception as e:
        await callback.answer(f"ስህተት: {e}")

@dp.callback_query(F.data == "my_status")
async def check_status(callback: types.CallbackQuery):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT ticket_num FROM participants WHERE user_id=? AND status='Approved'", (callback.from_user.id,))
    results = c.fetchall()
    conn.close()
    if results:
        tickets = ", ".join([str(r[0]) for r in results])
        await callback.message.answer(f"🎫 ትኬቶችዎ፦ {tickets}")
    else:
        await callback.message.answer("ትኬት የለዎትም።")

# --- Dummy Web Server for Render ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render የሚሰጠውን Port መጠቀም ወሳኝ ነው
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    print("ቦቱ እና የዌብ ሰርቨሩ እየነሱ ነው...")
    # ሁለቱንም በአንድ ጊዜ ማስነሳት
    await asyncio.gather(
        dp.start_polling(bot),
        start_web_server()
    )

if __name__ == "__main__":
    asyncio.run(main())
