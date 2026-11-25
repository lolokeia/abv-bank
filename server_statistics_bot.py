import asyncio
import html
import json, time
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.client.session.aiohttp import AiohttpSession

dp = Dispatcher()

SPARK_CHARS = "▁▂▃▅▆▇"

API_URL = "http://172.25.0.1:8099/api"

HEADERS = {"X-API-Key": "abv_secret_token"}

ADMIN_PATH = "admins.json"

FORBIDDEN = f"Доступ запрещен"

BOT_TOKEN = "" #"nothing"

PROXY_URL = "socks5://tg-ws-proxy:1080"

TEXT_SERVER_STATUS = "Статистика сервера"

LVLS = {
    0: "0. Может всё",
    1: "1. Может читать полный журнал",
    2: "2. Может читать журнал без docker-контейнеров",
    3: "3. Может получать уведомления о работах, может смотреть аптайм",
}

LAST_STATUS_MSG: dict[int, int] = {}

ALERT_STATE = {
    "api_down": False,
    "high_temp": False,
    "high_cpu": False,
    "high_ram": False,
    "high_ssd": False,
    "seen_ssh": set(),
    "ssh_initialized": False,
}



main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=TEXT_SERVER_STATUS)]
    ],
    resize_keyboard=True
)

def get_admins() -> dict[str, int]:
    try:
        with open(ADMIN_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Config Error] Ошибка чтения {ADMIN_PATH}: {e}")
        return {}
    
def lvl_to_text(lvl):
    if lvl in LVLS:
        return LVLS[lvl]
    else:
        return "Неизвестный уровень доступа"
    
def check_admin(msg, req_lvl=3) -> bool:
    uid = str(msg.from_user.id)
    ADMINS = get_admins()
    if uid in ADMINS:
        if ADMINS.get(uid) <= req_lvl: return True
        else: return False
    else: return False

def check_admin_lvl(msg) -> int:
    ADMINS = get_admins()
    uid = str(msg.from_user.id)
    if uid in ADMINS:
        return ADMINS.get(uid)
    else: return None

async def broadcast(bot: Bot, text: str, max_lvl: int = 0) -> int:
    """Рассылает сообщение всем админам с уровнем <= max_lvl."""
    sent_count = 0
    for uid, lvl in get_admins().items():
        if lvl <= max_lvl:
            try:
                await bot.send_message(int(uid), text, parse_mode="HTML")
                sent_count += 1
            except Exception as e:
                print(f"[Notify Error] Ошибка отправки {uid}: {e}")
    return sent_count


async def fetch_api(endpoint: str, params: dict = None) -> dict | list | None:
    timeout = aiohttp.ClientTimeout(total=5)
    try:
        async with aiohttp.ClientSession(headers=HEADERS, timeout=timeout) as session:
            async with session.get(f"{API_URL}/{endpoint}", params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
    except Exception:
        return None

def make_sparkline(values: list[float]) -> str:
    if not values:
        return "нет данных"
    return "".join(
        SPARK_CHARS[min(len(SPARK_CHARS) - 1, int(v / 100 * (len(SPARK_CHARS) - 1)))]
        for v in values
    )

@dp.message(Command('status'))
@dp.message(F.text == TEXT_SERVER_STATUS)
async def cmd_status(message: Message):
    if check_admin(message):
        lvl = check_admin_lvl(message)
        if lvl is None:
            await message.answer("🔴 <b>Ваш уровень помечен как None</b>", parse_mode="HTML")
            return

        sys_info, up, dk, hist = await asyncio.gather(
            fetch_api("system"),
            fetch_api("uptime"),
            fetch_api("docker"),
            fetch_api("history", {"hours": 24})
        )

        if not sys_info or not up:
            await message.answer("🔴 <b>Сервер мониторинга недоступен</b>", parse_mode="HTML")
            return

        step = max(1, len(hist) // 25) if hist else 1
        cpu_line = make_sparkline([p["cpu"] for p in hist[::step] if p["cpu"] is not None]) if hist else ""
        ram_line = make_sparkline([p["ram"] for p in hist[::step] if p["ram"] is not None]) if hist else ""
        r = up.get("ratios", {})

        lines = [
            "🖥 <b>Статус сервера</b>\n",
            f"⏱ <b>Аптайм:</b> {up['uptime_hours']} ч. ({up['uptime_days']} дн.)",
            f"⏱ 24ч: {r.get('24h')}% | 7д: {r.get('7d')}% | 30д: {r.get('30d')}% | Всё: {r.get('all_time')}%",
        ]

        if lvl <= 2:
            lines_sys = [
                f"⚙️ <b>CPU:</b> {sys_info['cpu']['percent']}% (LA: {sys_info['cpu']['load_avg'][0]:.2f})",
                f"🧠 <b>RAM:</b> {sys_info['ram']['used_gb']} / {sys_info['ram']['total_gb']} ГБ ({sys_info['ram']['percent']}%)",
                f"💾 <b>Диск:</b> {sys_info['disk_root']['used_gb']} / {sys_info['disk_root']['total_gb']} ГБ ({sys_info['disk_root']['percent']}%)",
            ]
            lines.extend(lines_sys)

            if sys_info.get("temp_max_c"):
                lines.append(f"<b>Температура (MAX):</b> {sys_info['temp_max_c']} °C")

            if cpu_line:
                lines.append(f"\n<b>CPU (24ч):</b> <code>{cpu_line}</code>")
                lines.append(f"<b>RAM (24ч):</b> <code>{ram_line}</code>")

        if lvl <= 1:
            if dk:
                if dk.get("available"):
                    lines.append(f"\n🐳 <b>Docker ({dk['count']}):</b>")
                    for c in dk["containers"]:
                        icon = "🟢" if c["status"] == "running" else "🔴"
                        lines.append(f"{icon} <code>{c['name']} ({c['image']})</code> — {c['status']}")
                else:
                    lines.append("\n🐳 <b>Docker недоступен</b>")

        uid = message.from_user.id
        print(f"stats ask from {uid} with lvl {lvl}")
        # 1. Удаляем предыдущее сообщение со статусом от бота
        if uid in LAST_STATUS_MSG:
            try:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=LAST_STATUS_MSG[uid])
            except Exception:
                pass

        # 2. Удаляем сообщение пользователя ("Статистика сервера" или "/status")
        try:
            await message.delete()
        except Exception:
            pass

        # 3. Отправляем свежий статус и запоминаем его ID
        sent_msg = await message.answer("\n".join(lines), parse_mode="HTML")
        LAST_STATUS_MSG[uid] = sent_msg.message_id
    else:
        await message.answer(FORBIDDEN, parse_mode="HTML")

@dp.message(CommandStart(deep_link=True))
async def cmd_start_deeplink(message: Message, command: CommandObject):
    if command.args == "getid":
        await message.answer(
            f"🆔 Ваш Telegram ID: <code>{message.from_user.id}</code>\n"
            f"<i>Нажмите на цифры, чтобы скопировать, и отправьте администратору.</i>",
            parse_mode="HTML"
        )
        print("Recved /start with getid")
        return
    await cmd_start(message)


@dp.message(CommandStart())
async def cmd_start(message: Message):
    lvl = check_admin_lvl(message)
    lvl_text = lvl_to_text(lvl)
    if check_admin(message) and lvl is not None:
        await message.answer(f"Привет! Ваш уровень: {lvl_text}", parse_mode="HTML", reply_markup=main_kb)
        print("Recved /start")
    else:
        await message.answer("Вас нет в списке администраторов!", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())



@dp.message(Command("bcast"))
async def cmd_broadcast(message: Message, command: CommandObject):

    a = 1 / 0
    if not check_admin(message, req_lvl=0):
        await message.answer(FORBIDDEN, parse_mode="HTML")
        return

    if not command.args:
        await message.answer(
            "ℹ️ <b>Использование:</b>\n"
            "<code>/bcast all Текст</code> — всем уровням (0–3)\n"
            "<code>/bcast 2 Текст</code> — уровням 2, 1, 0\n"
            "<code>/bcast 1 Текст</code> — уровням 1, 0\n"
            "<code>/bcast 0 Текст</code> — только уровню 0",
            parse_mode="HTML"
        )
        return

    parts = command.args.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("⚠️ Укажите текст объявления после уровня.", parse_mode="HTML")
        return

    target_raw = parts[0].lower()
    broadcast_text = parts[1]

    if target_raw == "all":
        max_lvl = max(LVLS.keys())
    elif target_raw.isdigit() and int(target_raw) in LVLS:
        max_lvl = int(target_raw)
    else:
        await message.answer("⚠️ Неверный уровень. Укажите <code>0..3</code> или <code>all</code>.", parse_mode="HTML")
        return

    sender = html.escape(message.from_user.full_name)
    formatted_msg = (
        f"📢 <b>Оповещение</b>\n"
        f"{html.escape(broadcast_text)}"
    )

    sent_count = await broadcast(message.bot, formatted_msg, max_lvl=max_lvl)
    print(f"Broadcasted to {sent_count}")
    await message.answer(f"✅ Доставлено получателям: <b>{sent_count}</b>", parse_mode="HTML")



STRIKES = {"cpu": 0, "ram": 0, "disk": 0, "temp": 0}

def check_threshold(key: str, is_bad: bool, required: int = 3) -> str | None:
    """
    Возвращает:
    - 'ALERT', если порог превышен `required` раз подряд;
    - 'OK', если проблема была активна, но теперь прошла;
    - None, если ничего не изменилось.
    """
    if is_bad:
        STRIKES[key] += 1
        # Шлём алерт ровно в тот момент, когда счётчик достиг нужного числа
        if STRIKES[key] == required:
            return "ALERT"
    else:
        # Если до этого уже был отправлен ALERT, сообщаем о восстановлении
        was_alerted = STRIKES[key] >= required
        STRIKES[key] = 0
        if was_alerted:
            return "OK"
    return None

async def monitor_loop(bot: Bot):
    while True:
        try:
            sys_info, ssh_data = await asyncio.gather(
                fetch_api("system"),
                fetch_api("ssh")
            )

            # 0. Доступность самого агента
            if not sys_info:
                if not ALERT_STATE["api_down"]:
                    ALERT_STATE["api_down"] = True
                    await broadcast(bot, "🚨 <b>АЛЕРТ:</b> API мониторинга не отвечает!", max_lvl=0)
                await asyncio.sleep(30)
                continue
            elif ALERT_STATE["api_down"]:
                ALERT_STATE["api_down"] = False
                await broadcast(bot, "✅ <b>ВОССТАНОВЛЕНО:</b> API мониторинга снова в сети.", max_lvl=0)

            # 1–4. Пороговые триггеры: Темп > 60°C, CPU > 90%, RAM > 90%, SSD > 80%
            checks = [
                ("high_cpu", sys_info["cpu"]["percent"] > 90.0, f"🔥 Загрузка CPU: <b>{sys_info['cpu']['percent']}%</b>", "✅ Загрузка CPU в норме."),
                ("high_ram", sys_info["ram"]["percent"] > 90.0, f"🧠 Заполнение RAM: <b>{sys_info['ram']['percent']}%</b>", "✅ Использование RAM в норме."),
                ("high_ssd", sys_info["disk_root"]["percent"] > 80.0, f"💾 Заполнение SSD: <b>{sys_info['disk_root']['percent']}%</b>", "✅ Место на SSD освобождено."),
            ]
            if sys_info.get("temp_max_c") is not None:
                checks.append(
                    ("high_temp", sys_info["temp_max_c"] > 60.0, f"🌡 Температура CPU: <b>{sys_info['temp_max_c']} °C</b>", "✅ Температура CPU в норме.")
                )

            for key, is_bad, bad_msg, ok_msg in checks:
                if (is_bad) and (not ALERT_STATE[key]):
                    ALERT_STATE[key] = True
                    await broadcast(bot, f"⚠️ <b>АЛЕРТ:</b> {bad_msg}", max_lvl=1)
                elif (not is_bad) and (ALERT_STATE[key]):
                    ALERT_STATE[key] = False
                    await broadcast(bot, ok_msg, max_lvl=1)

            # 5. Успешные входы по SSH (всё, что содержит "Accepted ")
                        # 5. Успешные входы по SSH
            if ssh_data:
                if "logins" in ssh_data:
                    items = [(x["id"], x["message"]) for x in ssh_data["logins"]]
                elif ssh_data.get("available"):
                    items = [(line, line) for line in ssh_data.get("logs", []) if "Accepted " in line]
                else:
                    items = []

                if not ALERT_STATE["ssh_initialized"]:
                    for item_id, _ in items:
                        ALERT_STATE["seen_ssh"].add(item_id)
                    ALERT_STATE["ssh_initialized"] = True
                else:
                    for item_id, msg in items:
                        if item_id not in ALERT_STATE["seen_ssh"]:
                            ALERT_STATE["seen_ssh"].add(item_id)
                            await broadcast(
                                bot,
                                f"🔐 <b>Вход по SSH:</b>\n<code>{html.escape(msg)}</code>",
                                max_lvl=0
                            )


        except Exception as e:
            print(f"[Monitor Error] {e}")

        await asyncio.sleep(5)


running = True

async def on_shutdown(bot: Bot):
    global running
    print("closing")
    await broadcast(bot, "🦺Бот отключен", max_lvl=1)
    running = False

async def main():
    starting = True
    print("Starting")
    global bot
    while starting:
        try:
            session = AiohttpSession(proxy=PROXY_URL)
            bot = Bot(token=BOT_TOKEN, session=session)
            starting = False
        except Exception as e:
            print(f"ERROR: {e}")
            time.sleep(1)

    print("Bot started")
    asyncio.create_task(monitor_loop(bot))
    print("Done")
    dp.shutdown.register(on_shutdown)
    while running:
        try:
            await broadcast(bot, f"✅Бот запущен", max_lvl=1)
            await dp.start_polling(bot)
        except Exception as e:
            print(f"Bot error: {e}")
            await broadcast(bot, f"⚠️Ошибка бота", max_lvl=1)
            time.sleep(1)
            print(f"Trying to restart")
            continue
    


if __name__ == "__main__":
    asyncio.run(main())