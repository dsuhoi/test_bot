import os

from vkbottle import CtxStorage
from vkbottle import PhotoMessageUploader as photo_uploader
from vkbottle.bot import Bot, Message
from vkbottle.http import AiohttpClient
import commands as cmd

TOKEN = os.getenv("VK_TOKEN")
bot = Bot(TOKEN)
ctx = CtxStorage()
http_client = AiohttpClient()


@bot.on.message(text="Привет<!>")
async def hello(message: Message):
    users_info = await bot.api.users.get(message.from_id)
    await message.answer(f"Добрый день, {users_info[0].first_name} !")


@bot.on.message(text="/help<!>")
async def help_(message: Message):
    await message.answer(cmd.help_())


@bot.on.message(text="/manuls<!>")
@cmd.bot_except()
async def manuls_init(message: Message):
    state = message.text.split()[1]
    if state == "start":
        ctx.set("status", False)
        state_func = lambda: ctx.get("status")
        await cmd.manuls_init(message, state_func)
    elif state == "stop":
        ctx.set("status", True)


@bot.on.message(text="/calc<!>")
@cmd.bot_except(sigflag=True)
async def calc(message: Message):
    buff = cmd.calc_(message.text.split(" ", 1)[1])
    if isinstance(buff, str):
        await message.answer(buff)
    else:
        doc = await photo_uploader(bot.api).upload(buff, peer_id=message.peer_id)
        buff.close()
        await message.answer(attachment=doc)


@bot.on.message(text="/plot<!>")
@cmd.bot_except(sigflag=True)
async def plot(message: Message):
    buff = cmd.plot_(message.text[1:])
    doc = await photo_uploader(bot.api).upload(buff, peer_id=message.peer_id)
    buff.close()
    await message.answer(attachment=doc)


@bot.on.message(text="/cat<!>")
async def cat(message: Message):
    buff = await http_client.request_content("https://thiscatdoesnotexist.com/")
    doc = await photo_uploader(bot.api).upload(buff, peer_id=message.peer_id)
    await message.answer("", attachment=doc)


if __name__ == "__main__":
    bot.run_forever()
