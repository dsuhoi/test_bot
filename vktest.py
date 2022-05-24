import os

from vkbottle.bot import Bot, Message
from utils.commands import COMMAND_FUNC, bot_except, commands as commands_
from utils.wrapper import vk_wrapper

TOKEN = os.getenv("VK_TOKEN")
bot = Bot(TOKEN)

wrap = vk_wrapper(bot.api)
cmd = commands_(wrap)


def generate_func(func):
    @bot.on.message(text=f"/{func['name']}<!>")
    @bot_except(sigflag=func.get("sigflag"))
    async def wrapper(message: Message):
        await getattr(cmd, func["name"])(message)

    wrapper.__name__ = func["name"]
    return wrapper


for func in COMMAND_FUNC:
    generate_func(func)

if __name__ == "__main__":
    bot.run_forever()
