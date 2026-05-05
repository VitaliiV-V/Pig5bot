import json
import os
from telegram import  ReplyKeyboardRemove, ReplyKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram.ext import ContextTypes, ChatMemberHandler
from dotenv import load_dotenv
import uuid

load_dotenv()

TOKEN = os.getenv("TOKEN")

owner_id = int(os.getenv("owner_id"))
main_channel_id = int(os.getenv("main_channel_id"))
personal_channel_id = int(os.getenv("personal_channel_id"))
logs_channel_id = int(os.getenv("logs_channel_id"))
full_channel_id = int(os.getenv("full_channel_id"))
enable_Text_Notifications = bool(os.getenv("enable_Text_Notifications"))

owner_name = os.getenv("owner_name")

def load_chat_config(name):
    file_path = f"configs/{name}.json"
    default_data = {        
        "ban_messages": 0,
        "banned": [],
        "banned_users": [],
        "owner_names": [],
        "white_lists_mode" : "off",
        "white_list": [],
        "anon_enable": 0
    }

    if not os.path.exists(file_path):
        os.makedirs("configs", exist_ok=True)
        config = default_data.copy()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        return config
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config

def check(text, id):

    with open("dict.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    text = text.lower()
    text2 = ''
    for i in text:
        val = data.get(i)
        if val is not None:
            if len(text2) == 0 or text2[-1] != val:
                text2 += val

    name = "configs/" + str(id) + ".json"
    with open(name, "r", encoding="utf-8") as f:
        data2 = json.load(f)

    for i in data2["banned"]:
        if i in text2 or i in text:
            return True

    return False

async def reply_in_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = update.channel_post or update.edited_channel_post
    if not msg:
        return
    chat_id = msg.chat_id
    message_id = msg.message_id
    message_text = msg.text or ""

    if chat_id != main_channel_id:
        return

    if chat_id == main_channel_id:
        await context.bot.forward_message(
            chat_id=full_channel_id,
            from_chat_id=chat_id,
            message_id=msg.message_id
        )
        await context.bot.forward_message(
            chat_id = logs_channel_id,
            from_chat_id = chat_id,
            message_id = msg.message_id
        )
        await context.bot.send_message(
            chat_id = logs_channel_id,
            text = f"<pre>{msg.author_signature}</pre>",
            parse_mode = "HTML"
        )

    config = load_chat_config(str(main_channel_id))

    with open("uuid.json", "r", encoding="utf-8") as f:
        data2 = json.load(f)

    if msg.author_signature in config["banned_users"]:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        return

    if "/ban" in message_text and update.channel_post and msg.reply_to_message and data2["uuid"] in msg.author_signature:
        name = str(main_channel_id)
        file_path = f"configs/{name}.json"
        data = load_chat_config(str(main_channel_id))

        s = msg.text.split(maxsplit=1)[1] if len(msg.text.split(maxsplit=1)) > 1 else ""
        if msg.reply_to_message.author_signature not in data["banned_users"]:
            data["banned_users"].append(msg.reply_to_message.author_signature)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    if msg.author_signature:
        txt = msg.author_signature
        ok = 0
        if config["owner_names"]:
            for i in config["owner_names"]:
                if i in txt:
                    ok = 1

        if ok:
            if data2["uuid"] not in msg.author_signature:
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                return
            else:
                new_uuid = str(uuid.uuid4())

                await context.bot.set_chat_title(personal_channel_id, owner_name + "ㅤㅤㅤㅤㅤㅤ ㅤ ㅤ ㅤ ㅤ ㅤ ㅤ ㅤ " + new_uuid)

                with open("uuid.json", "r", encoding="utf-8") as f:
                    data3 = json.load(f)

                data3["uuid"] = new_uuid

                with open("uuid.json", "w", encoding="utf-8") as f:
                    json.dump(data3, f, ensure_ascii=False, indent=4)
                return

    if config["white_lists_mode"] != "off":
        ok = False
        if config["white_lists_mode"] == "admins" or config["white_lists_mode"] == "admins_only":
            admins = await context.bot.get_chat_administrators(chat_id)
            for u in admins:
                admin = ''
                if u.user.first_name:
                    admin += u.user.first_name
                if u.user.first_name and u.user.last_name:
                    admin += " "
                if u.user.last_name:
                    admin += u.user.last_name
                print(admin)
                if admin == msg.author_signature:
                    ok = True
        if config["white_lists_mode"] == "admins" or config["white_lists_mode"] == "manual":
            for u in config["white_list"]:
                print(u)
                print(msg.author_signature)
                if u == msg.author_signature:
                    ok = True

        if not ok:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            return

    if config["ban_messages"] == 1:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        return
    elif config["ban_messages"] == 2:
        if check(message_text, chat_id):
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            return

async def ban_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    if not result:
        return

    if result.chat.id == personal_channel_id and result.new_chat_member.status == "member":
        user_id = result.new_chat_member.user.id
        await context.bot.ban_chat_member(
            chat_id=result.chat.id,
            user_id=user_id
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_name = (await context.bot.get_me()).first_name
    msg = update.message
    if not msg:
        return

    await msg.reply_text(
        f"Вас приветствует система защиты «{bot_name}».\n"
    )

async def blockall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.from_user or not msg.text:
        return

    user_id = msg.from_user.id

    bot_name = (await context.bot.get_me()).first_name
    msg = update.message
    if not msg:
        return

    if user_id == owner_id:
        name = str(main_channel_id)
        file_path = f"configs/{name}.json"
        data = load_chat_config(str(main_channel_id))

        data["ban_messages"] = 1

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        await context.bot.send_message(chat_id=name,
                                       text=f"⚠️ Уведомление от системы защиты «{bot_name}»:\n"
                                            "Активирован режим тотальной зачистки.\n"
                                            "Любая активность будет немедленно удалена.\n"
                                            "Канал под полным контролем.")
        await msg.reply_text(
            f"Система защиты «{bot_name}» активирована"
        )

    else:

        await msg.reply_text(
            f"Внимание! Системой защиты «{bot_name}» отражена попытка несанкционированного доступа к телеграм каналу"
        )

async def smart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.from_user or not msg.text:
        return

    user_id = msg.from_user.id

    bot_name = (await context.bot.get_me()).first_name

    if user_id == owner_id:
        name = str(main_channel_id)
        file_path = f"configs/{name}.json"
        data = load_chat_config(str(main_channel_id))

        data["ban_messages"] = 2

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        await context.bot.send_message(chat_id=name,
                                       text=f"⚠️ Уведомление от системы защиты «{bot_name}»:\n"
                                            "Включён интеллектуальный режим модерации.\n"
                                            "Анализирую поведение, фильтрую спам и поддерживаю порядок.\n"
                                            "Работаю аккуратно.")

        await msg.reply_text(
            f"Система защиты «{bot_name}» активирована"
        )
    else:
        await msg.reply_text(
            f"Внимание! Системой защиты «{bot_name}» отражена попытка несанкционированного доступа к телеграм каналу 🍌хаммаааааааам🍌"
        )

async def disable(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.from_user or not msg.text:
        return

    user_id = msg.from_user.id

    bot_name = (await context.bot.get_me()).first_name


    if user_id == owner_id:
        name = str(main_channel_id)
        file_path = f"configs/{name}.json"
        data = load_chat_config(str(main_channel_id))

        data["ban_messages"] = 0

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        await context.bot.send_message(chat_id=name,
                                       text=f"⚠️ Уведомление от системы защиты «{bot_name}»:\n"
                                            "Система деактивирована.\n"
                                            "Контроль временно снят.")

        await msg.reply_text(
            f"Система защиты «{bot_name}» деактивирована"
        )

    else:
        await msg.reply_text(
            f"Внимание! Системой защиты «{bot_name}» отражена попытка несанкционированного доступа к телеграм каналу"
        )

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.from_user or not msg.text:
        return

    user_id = msg.from_user.id

    bot_name = (await context.bot.get_me()).first_name

    if user_id == owner_id:
        name = str(main_channel_id)
        file_path = f"configs/{name}.json"
        data = load_chat_config(str(main_channel_id))

        s = msg.text.split(maxsplit=1)[1] if len(msg.text.split(maxsplit=1)) > 1 else ""

        try:
            if s not in data["banned_users"]:
                data["banned_users"].append(s)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            await msg.reply_text(
                f"{s} зaблокирован"
            )
        except Exception as e:
            await msg.reply_text(
                f"Не удалось зблокировать {s}"
            )

    else:
        await msg.reply_text(
            f"Внимание! Системой защиты «{bot_name}»  отражена попытка несанкционированного доступа к телеграм каналу"
        )

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.from_user or not msg.text:
        return

    user_id = msg.from_user.id

    bot_name = (await context.bot.get_me()).first_name

    if user_id == owner_id:
        name = str(main_channel_id)
        file_path = f"configs/{name}.json"
        data = load_chat_config(str(main_channel_id))

        s = msg.text.split(maxsplit=1)[1] if len(msg.text.split(maxsplit=1)) > 1 else ""

        try:
            data["banned_users"].remove(s)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            await msg.reply_text(
                f"{s} разблокирован"
            )
        except Exception as e:
            await msg.reply_text(
                f"Не удалось разблокировать {s}"
            )

    else:
        await msg.reply_text(
            f"Внимание! Системой защиты «{bot_name}»  отражена попытка несанкционированного доступа к телеграм каналу"
        )

async def setwhitelistsmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.from_user or not msg.text:
        return

    user_id = msg.from_user.id

    bot_name = (await context.bot.get_me()).first_name

    if user_id == owner_id:
        name = str(main_channel_id)
        file_path = f"configs/{name}.json"
        data = load_chat_config(str(main_channel_id))

        s = msg.text.split(maxsplit=1)[1] if len(msg.text.split(maxsplit=1)) > 1 else ""
        if s == "admins" or s == "admins_only" or s == "manual" or s == "off":
            try:
                data["white_lists_mode"] = s

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)

                await msg.reply_text(
                    f"Успешно"
                )
            except Exception as e:
                await msg.reply_text(
                    f"Failed"
                )
        else:
            await msg.reply_text(
                f"Failed"
            )

    else:
        await msg.reply_text(
            f"Внимание! Системой защиты «{bot_name}»  отражена попытка несанкционированного доступа к телеграм каналу"
        )

async def addtolists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.from_user or not msg.text:
        return

    user_id = msg.from_user.id

    bot_name = (await context.bot.get_me()).first_name

    if user_id == owner_id:
        name = str(main_channel_id)
        file_path = f"configs/{name}.json"
        data = load_chat_config(str(main_channel_id))

        s = msg.text.split(maxsplit=1)[1] if len(msg.text.split(maxsplit=1)) > 1 else ""

        try:
            if s not in data["white_list"]:
                data["white_list"].append(s)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            await msg.reply_text(
                f"{s} в белом списке",reply_markup=ReplyKeyboardRemove()
            )
        except Exception as e:
            await msg.reply_text(
                f"Не удалось добавить {s} в белый список",reply_markup=ReplyKeyboardRemove()
            )

    else:
        await msg.reply_text(
            f"Внимание! Системой защиты «{bot_name}»  отражена попытка несанкционированного доступа к телеграм каналу", reply_markup=ReplyKeyboardRemove()
        )

async def delfromlists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.from_user or not msg.text:
        return

    user_id = msg.from_user.id

    bot_name = (await context.bot.get_me()).first_name

    if user_id == owner_id:
        name = str(main_channel_id)
        file_path = f"configs/{name}.json"
        data = load_chat_config(str(main_channel_id))

        s = msg.text.split(maxsplit=1)[1] if len(msg.text.split(maxsplit=1)) > 1 else ""

        try:
            data["white_list"].remove(s)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            await msg.reply_text(
                f"{s} больше не в белом списке"
            )
        except Exception as e:
            await msg.reply_text(
                f"Не удалось убрать {s} из белого списка"
            )

    else:
        await msg.reply_text(
            f"Внимание! Системой защиты «{bot_name}»  отражена попытка несанкционированного доступа к телеграм каналу"
        )


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.from_user or not msg.text:
        return

    user_id = msg.from_user.id

    s = msg.text.split(maxsplit=1)[1] if len(msg.text.split(maxsplit=1)) > 1 else ""
    text = (f"Новый запрос на регистрацию канала:\n"
            f"Владелец: {msg.from_user.first_name} {msg.from_user.username}\n"
            f"Имя канала: {s}")
    keyboard = ReplyKeyboardMarkup(
        [[f"/add {s}", "/reject"]],
        resize_keyboard=True
    )
    await context.bot.send_message(
        chat_id=owner_id,
        text = text,
        reply_markup=keyboard
    )
    await msg.reply_text(
        f"Запрос на регистрацию отправлен", reply_markup=ReplyKeyboardRemove()
    )

async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.from_user or not msg.text:
        return

    user_id = msg.from_user.id

    bot_name = (await context.bot.get_me()).first_name

    if user_id == owner_id:
        await msg.reply_text(
            f"Отклонено",reply_markup=ReplyKeyboardRemove()
        )

    else:
        await msg.reply_text(
            f"Внимание! Системой защиты «{bot_name}»  отражена попытка несанкционированного доступа к телеграм каналу"
        )

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("blockall", blockall))
app.add_handler(CommandHandler("smart", smart))
app.add_handler(CommandHandler("disable", disable))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("unban", unban))
app.add_handler(CommandHandler("setwhitelistsmode", setwhitelistsmode))
app.add_handler(CommandHandler("add", addtolists))
app.add_handler(CommandHandler("del", delfromlists))
app.add_handler(CommandHandler("reg", register))
app.add_handler(CommandHandler("reject", reject))
app.add_handler(MessageHandler(filters.ALL, reply_in_channel))
app.add_handler(MessageHandler(filters.UpdateType.EDITED_CHANNEL_POST, reply_in_channel))
app.add_handler(ChatMemberHandler(ban_new_members, ChatMemberHandler.CHAT_MEMBER))

app.run_polling(allowed_updates=["message", "channel_post", "chat_member"])
