import os

from vkbottle.bot import Bot, Message
from utils.commands import COMMAND_FUNC, bot_except, commands as commands_
from utils.wrapper import vk_wrapper

TOKEN = os.getenv("VK_TOKEN")
bot = Bot(TOKEN)

wrap = vk_wrapper(bot.api)
cmd = commands_(wrap)


for func in COMMAND_FUNC:
    exec(
        f"""
@bot.on.message(text=\"/{func['name']}<!>\")
@bot_except(signal={func.get('signal')})
async def {func['name']}(message: Message):
    await cmd.{func['name']}(message)
"""
    )
if __name__ == "__main__":
    bot.run_forever()
