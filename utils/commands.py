import logging
import signal
import argparse
import shlex
from io import BytesIO
from vkbottle.http import AiohttpClient
import utils.wrapper as wrapper
from deep_translator import GoogleTranslator as translator

from sympy import preview

from utils.sympy_wrapper import vmw_eval, vmw_plot  # local module

TIMEOUT = 15
signal.signal(
    signal.SIGALRM,
    lambda sig, st: (_ for _ in ()).throw(Exception("Превышен лимит по времени!")),
)

logging.basicConfig(format="[%(levelname)s]:<%(asctime)s>: %(message)s")
http_client = AiohttpClient()
transl = translator(source="auto", target="ru")


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


COMMAND_FUNC = [
    {"name": "help"},
    {"name": "cat"},
    {"name": "fox"},
    {"name": "neko"},
    {"name": "translate"},
    {"name": "numbers"},
    {"name": "qrcode"},
    {"name": "weather"},
    {"name": "story"},
    {"name": "calc", "sigflag": True},
    {"name": "plot", "sigflag": True, "regexp": True},
]


class commands:
    def __init__(self, bot: wrapper):
        self.__bot = bot

    async def help(self, message):
        help_str = """Инструкция к боту:
/help -- вызов инструкции (кто б знал...)
/manuls <start | stop> <A> <B> -- вызов/остановка подсчёта манулов в диапазоне [A;B]
/calc [команда_Sympy] -- вызов интерпретатора СКА Sympy
/plot[...] -- вызов sympy-функций для вывода графиков
/cat /fox /neko -- получение фото
/translate [-L <lang>] <text> - перевод text на lang
/weather <city> -- погода
/qrcode <text> -- генерация QR кода
/story -- история от GPT2
"""
        await self.__bot.answer(message, help_str)

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

    async def fox(self, message):
        resp = await http_client.request_json("https://randomfox.ca/floof/")
        buff = await http_client.request_content(resp["image"])
        await self.__bot.answer_photo(message, buff)

    async def neko(self, message):
        resp = await http_client.request_json("https://api.waifu.pics/sfw/neko")
        buff = await http_client.request_content(resp["url"])
        await self.__bot.answer_photo(message, buff)

    async def translate(self, message):
        parser = argparse.ArgumentParser()
        parser.add_argument("-L", "-lang", default="ru")

        input_str = message.text.split(" ", 1)[1]
        args, text = parser.parse_known_intermixed_args(shlex.split(input_str))
        text = translator(source="auto", target=args.L).translate(text=" ".join(text))
        await self.__bot.reply(message, text)

    async def numbers(self, message):
        input_str = tmp[1] if len(tmp := message.text.split()) > 1 else "random"
        text = await http_client.request_text(f"http://numbersapi.com/{input_str}")
        await self.__bot.answer(message, transl.translate(text=text))

    async def weather(self, message):
        city = tmp[1] if len(tmp := message.text.split()) > 1 else "Novosibirsk"
        text = await http_client.request_text(f"https://wttr.in/{city}?m&format=4")
        await self.__bot.answer(message, text)

    async def qrcode(self, message):
        buff = await http_client.request_content(
            f"https://image-charts.com/chart?chs=150x150&cht=qr&chl={message.text.split(' ', 1)[1]}&choe=UTF-8"
        )
        await self.__bot.reply_photo(message, buff)

    async def story(self, message):
        input_str = message.text.split(" ", 1)[1]
        response = await http_client.request_json(
            "https://pelevin.gpt.dobro.ai/generate/",
            method="POST",
            json={"prompt": input_str, "length": 100},
        )
        await self.__bot.answer(message, input_str + response["replies"][0])
