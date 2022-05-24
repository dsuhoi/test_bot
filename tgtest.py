import os

from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message, ContentType
from utils.commands import COMMAND_FUNC, bot_except, commands as commands_
from utils.wrapper import tg_wrapper

TOKEN = os.getenv("TG_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

wrap = tg_wrapper()
cmd = commands_(wrap)


@dp.message_handler(commands=["start", "help"])
async def help(message: Message):
    await cmd.help(message)


DEL_COMMANDS = ["help", "photo"]

COMMAND_FUNC_ = filter(lambda a: a["name"] not in DEL_COMMANDS, COMMAND_FUNC)

for func in COMMAND_FUNC_:
    reg_str = "regexp_" if func.get("regexp") else ""
    exec(
        f"""
@dp.message_handler({reg_str}commands=\"{func['name']}\")
@bot_except(sigflag={func.get('sigflag')})
async def {func['name']}(message: Message):
    await cmd.{func['name']}(message)
"""
    )


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
