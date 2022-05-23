import os

from vkbottle import CtxStorage
from vkbottle.bot import Bot, Message
from utils.commands import bot_except, commands as commands_
from utils.wrapper import vk_wrapper

TOKEN = os.getenv("VK_TOKEN")
bot = Bot(TOKEN)
ctx = CtxStorage()

wrap = vk_wrapper(bot.api)
cmd = commands_(wrap)


@bot.on.message(text="Привет<!>")
async def hello(message: Message):
    users_info = await bot.api.users.get(message.from_id)
    await message.answer(f"Добрый день, {users_info[0].first_name} !")


@bot.on.message(text="/help<!>")
async def help_(message: Message):
    await cmd.help(message)


@bot.on.message(text="/cat<!>")
async def cat(message: Message):
    await cmd.cat(message)


@bot.on.message(text="/weather<!>")
@bot_except()
async def weather(message: Message):
    await cmd.weather(message)


@bot.on.message(text="/qrcode<!>")
@bot_except()
async def qrcode(message: Message):
    await cmd.qrcode(message)


@bot.on.message(text="/story<!>")
async def story(message: Message):
    await cmd.story(message)


@bot.on.message(text="/manuls<!>")
@bot_except()
async def manuls_init(message: Message):
    state = message.text.split()[1]
    if state == "start":
        ctx.set("status", False)
        state_func = lambda: ctx.get("status")
        await cmd.manuls_init(message, state_func)
    elif state == "stop":
        ctx.set("status", True)


@bot.on.message(text="/calc<!>")
@bot_except(sigflag=True)
async def calc(message: Message):
    await cmd.calc(message)


@bot.on.message(text="/plot<!>")
@bot_except(sigflag=True)
async def plot(message: Message):
    await cmd.plot(message)


if __name__ == "__main__":
    bot.run_forever()
