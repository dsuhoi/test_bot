import os

from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message
from vkbottle import CtxStorage

import commands as cmd

TOKEN = os.getenv("TG_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: Message):
    await message.reply(cmd.help_())


ctx = CtxStorage()


@dp.message_handler(commands="manuls")
@cmd.bot_except()
async def manuls_init(message: Message):
    state = message.text.split()[1]
    if state == "start":
        ctx.set("status", False)
        state_func = lambda: ctx.get("status")
        await cmd.manuls_init(message, state_func)
    elif state == "stop":
        ctx.set("status", True)


@dp.message_handler(commands="calc")
@cmd.bot_except(sigflag=True)
async def calc(message: Message):
    buff = cmd.calc_(message.text.split(" ", 1)[1])
    if isinstance(buff, str):
        await message.answer(buff)
    else:
        await message.answer_photo(buff)
        buff.close()


@dp.message_handler(regexp_commands="plot")
@cmd.bot_except(sigflag=True)
async def plot(message: Message):
    buff = cmd.plot_(message.text[1:])
    await message.answer_photo(buff)
    buff.close()


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
