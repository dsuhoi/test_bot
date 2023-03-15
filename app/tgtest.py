import os

from aiogram import Bot, Dispatcher, executor
from aiogram.types import BotCommand, Message

from app.commands import bot_commands, bot_except
from app.utils.wrapper import tg_wrapper

TOKEN = os.getenv("TG_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
wrap = tg_wrapper()
commands = bot_commands(wrap)


@dp.message_handler(commands=["start", "help"])
async def help(message: Message):
    await commands.help(message)


def generate_func(func):
    handler_kwargs = {}
    if func.get("regexp"):
        handler_kwargs["regexp_commands"] = func["name"]
    else:
        handler_kwargs["commands"] = func["name"]

    @dp.message_handler(**handler_kwargs)
    @bot_except(sigflag=func.get("sigflag"))
    async def wrapper(message: Message):
        message.text = s[1] if len(s := message.text.split(maxsplit=1)) > 1 else ""
        await getattr(commands, func["name"])(message)

    wrapper.__name__ = func["name"]
    return wrapper


DEL_COMMANDS = ["help"]
COMMAND_FUNC = filter(lambda a: a["name"] not in DEL_COMMANDS, commands.COMMANDS)
commands_info = []

for func in COMMAND_FUNC:
    generate_func(func)
    if h := func.get("help_"):
        commands_info.append(BotCommand(func.get("name"), h))


async def init_info(dp):
    await dp.bot.set_my_commands(commands_info)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=init_info)
