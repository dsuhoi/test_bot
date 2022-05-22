import os

from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message
from vkbottle import CtxStorage
from commands import bot_except, commands as commands_
from wrapper import tg_wrapper

TOKEN = os.getenv("TG_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

wrap = tg_wrapper()
cmd = commands_(wrap)

ctx = CtxStorage()


@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: Message):
    await cmd.help(message)


@dp.message_handler(commands="manuls")
@bot_except()
async def manuls_init(message: Message):
    state = message.text.split()[1]
    if state == "start":
        ctx.set("status", False)
        state_func = lambda: ctx.get("status")
        await cmd.manuls_init(message, state_func)
    elif state == "stop":
        ctx.set("status", True)


@dp.message_handler(commands="cat")
@bot_except()
async def cat(message: Message):
    await cmd.cat(message)


@dp.message_handler(commands="calc")
@bot_except(sigflag=True)
async def calc(message: Message):
    await cmd.calc(message)


@dp.message_handler(regexp_commands="plot")
@bot_except(sigflag=True)
async def plot(message: Message):
    await cmd.plot(message)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
