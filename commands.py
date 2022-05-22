import asyncio as ac
import logging
import signal
from io import BytesIO
from vkbottle.http import AiohttpClient
import wrapper

from sympy import preview

from sympy_wrapper import vmw_eval, vmw_plot  # local module

TIMEOUT = 15
signal.signal(
    signal.SIGALRM,
    lambda sig, st: (_ for _ in ()).throw(Exception("Превышен лимит по времени!")),
)

logging.basicConfig(format="[%(levelname)s]:<%(asctime)s>: %(message)s")
http_client = AiohttpClient()


def bot_except(**params):
    def decor(func):
        async def wrapper(message):
            try:
                await func(message)
            except Exception as e:
                if params:
                    if params["sigflag"]:
                        signal.alarm(0)
                logging.warning(e)
                await message.answer(f"Ошибка {e}")

        return wrapper

    return decor


class commands:
    def __init__(self, bot: wrapper):
        self.__bot = bot

    async def help(self, message):
        help_str = """Инструкция к боту:
/help -- вызов инструкции (кто б знал...)
/manuls <start | stop> <A> <B> -- вызов/остановка подсчёта манулов в диапазоне [A;B]
/calc [команда_Sympy] -- вызов интерпретатора СКА Sympy
/plot[...] -- вызов sympy-функций для вывода графиков
/cat -- получение фото кота
/weather <city> -- погода
"""
        await self.__bot.answer(message, help_str)

    async def manuls_init(self, message, _state):
        *_, start, end = message.text.split()
        start, end = int(start), int(end)
        if 0 < start <= end:
            await self.__bot.answer(message, f"Подсчёт от {start} и до {end}:")
            n_ends = [2, 0, 1, 1, 1, 2]
            str_ends = ["", "а", "ов"]
            for i in range(start, end + 1):
                res_s = f"{i} манул{str_ends[2 if 4 < (i % 100) < 20 else n_ends[min(i % 10, 5)]]}"
                await self.__bot.answer(message, res_s)
                await ac.sleep(0.15)
                if _state():
                    await self.__bot.answer(message, "Остановка подсчёта")
                    break

    def calc__(self, input_str: str):
        signal.alarm(TIMEOUT)
        res = vmw_eval(input_str)
        signal.alarm(0)
        res_str = f"Input: $${res['input']}$$\nOutput: $${res['output']}$$"
        try:
            buff = BytesIO()
            preview(res_str, viewer="BytesIO", outputbuffer=buff, euler=False)
            buff.seek(0)
        except Exception:
            return res_str
        else:
            return buff

    async def calc(self, message):
        buff = self.calc__(message.text.split(" ", 1)[1])
        if isinstance(buff, str):
            await self.__bot.answer(message, buff)
        else:
            await self.__bot.answer_photo(message, buff)
            buff.close()

    def plot__(self, input_str: str):
        signal.alarm(TIMEOUT)
        fig = vmw_plot(input_str.rsplit(")", 1)[0] + ",show=False)")
        buff = BytesIO()
        signal.alarm(TIMEOUT)
        fig.save(buff)
        signal.alarm(0)
        del fig
        buff.seek(0)
        return buff

    async def plot(self, message):
        buff = self.plot__(message.text[1:])
        await self.__bot.answer_photo(message, buff)
        buff.close()

    async def cat(self, message):
        buff = await http_client.request_content("https://thiscatdoesnotexist.com/")
        await self.__bot.answer_photo(message, buff)

    async def weather(self, message):
        city = tmp[1] if len(tmp := message.text.split()) > 1 else "Novosibirsk"
        text = await http_client.request_text(f"https://wttr.in/{city}?format=4")
        await self.__bot.answer(message, text)
