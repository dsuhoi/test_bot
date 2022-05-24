import os

from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message
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


def generate_func(func):
    handler_kwargs = {}
    if func.get("regexp"):
        handler_kwargs["regexp_commands"] = func["name"]
    else:
        handler_kwargs["commands"] = func["name"]

    @dp.message_handler(**handler_kwargs)
    @bot_except(sigflag=func.get("sigflag"))
    async def wrapper(message: Message):
        await getattr(cmd, func["name"])(message)

    wrapper.__name__ = func["name"]
    return wrapper


DEL_COMMANDS = ["help"]

COMMAND_FUNC_ = filter(lambda a: a["name"] not in DEL_COMMANDS, COMMAND_FUNC)

for func in COMMAND_FUNC_:
    generate_func(func)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
