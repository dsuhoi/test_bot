import os

from vkbottle.bot import Bot, Message

from utils.commands import bot_commands, bot_except
from utils.wrapper import vk_wrapper

TOKEN = os.getenv("VK_TOKEN")
bot = Bot(TOKEN)

wrap = vk_wrapper(bot.api)
commands = bot_commands(wrap)


def generate_func(func):
    @bot.on.message(text=f"/{func['name']}<!>")
    @bot_except(sigflag=func.get("sigflag"))
    async def wrapper(message: Message):
        await getattr(commands, func["name"])(message)

    wrapper.__name__ = func["name"]
    return wrapper


DEL_COMMANDS = []

COMMAND_FUNC = filter(lambda a: a["name"] not in DEL_COMMANDS, commands.COMMANDS)

for func in COMMAND_FUNC:
    generate_func(func)

if __name__ == "__main__":
    bot.run_forever()
