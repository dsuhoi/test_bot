import base64
import logging
import os
import re
import signal
from io import BytesIO
from typing import Union

from cairosvg import svg2png
from deep_translator import GoogleTranslator as translator

from app.utils.async_requests import aio_requests
from app.utils.sympy_wrapper import sympy_eval
from app.utils.wrapper import cmd, meta_cmd, tg_wrapper, vk_wrapper

TIMEOUT = 15
signal.signal(
    signal.SIGALRM,
    lambda sig, st: (_ for _ in ()).throw(Exception("Превышен лимит по времени!")),
)
openai_token = os.getenv("OPENAI_TOKEN")

logging.basicConfig(format="[%(levelname)s]:<%(asctime)s>: %(message)s")


def get_attr(input_str: str, key, default=None):
    templ = rf"\s?-?{key}\s*=?\s*(\w+)\s?"
    res = re.search(templ, input_str)
    if res:
        return input_str.replace(res[0], " "), res[1]
    else:
        return input_str, default


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


class bot_commands(metaclass=meta_cmd):
    def __init__(self, bot: Union[vk_wrapper, tg_wrapper], http_client=aio_requests()):
        self.__bot = bot
        self.__http = http_client
        self.__transl = translator(source="auto", target="ru")

        self.__help = "Инструкция к боту:\n"
        self.__help_ext = {}
        for func in bot_commands.COMMANDS:
            if h := func.get("help_"):
                self.__help += h + "\n"
            if h_ext := func.get("help_ext"):
                self.__help_ext[func.get("name")] = h_ext

    @cmd(help_="/help <command> -- вызов инструкции")
    async def help(self, message):
        input_str = message.text.split(maxsplit=1)
        if len(input_str) > 1 and (h := self.__help_ext.get(input_str[1])):
            help_str = h
        else:
            help_str = self.__help

        await self.__bot.answer(message, help_str)

    @cmd(help_="/cat /fox /neko -- получение фото")
    async def cat(self, message):
        buff = await self.__http.request_content("https://thiscatdoesnotexist.com/")
        await self.__bot.answer_photo(message, buff)

    @cmd()
    async def fox(self, message):
        resp = await self.__http.request_json("https://randomfox.ca/floof/")
        buff = await self.__http.request_content(resp["image"])
        await self.__bot.answer_photo(message, buff)

    @cmd()
    async def neko(self, message):
        resp = await self.__http.request_json("https://api.waifu.pics/sfw/neko")
        buff = await self.__http.request_content(resp["url"])
        await self.__bot.answer_photo(message, buff)

    @cmd(
        help_="/translate [-L <lang>] <text> - перевод text на lang",
        help_ext="""Примеры:
/translate Hello world!
/translate -L ja Привет мир!
""",
    )
    async def translate(self, message):
        input_str = message.text.split(maxsplit=1)[1]
        text, lang = get_attr(input_str, "L", default="ru")
        text = translator(source="auto", target=lang.lower()).translate(text=text)
        await self.__bot.reply(message, text)

    @cmd(help_ext="/number <number> -- получение информации о числе")
    async def numbers(self, message):
        input_str = tmp[1] if len(tmp := message.text.split()) > 1 else "random"
        text = await self.__http.request_text(f"http://numbersapi.com/{input_str}")
        await self.__bot.answer(message, self.__transl.translate(text=text))

    @cmd(help_="/weather <city> -- погода")
    async def weather(self, message):
        city = tmp[1] if len(tmp := message.text.split()) > 1 else "Novosibirsk"
        text = await self.__http.request_text(f"https://wttr.in/{city}?m&format=4")
        await self.__bot.answer(message, text)

    @cmd(help_="/qrcode <text> -- генерация QR кода")
    async def qrcode(self, message):
        text = message.text.split(maxsplit=1)[1]
        buff = await self.__http.request_content(
            f"https://image-charts.com/chart?chs=150x150&cht=qr&chl={text}&choe=UTF-8"
        )
        await self.__bot.reply_photo(message, buff)

    @cmd(help_="/image <text> -- генерация изображения по описанию")
    async def image(self, message):
        text = message.text.split(maxsplit=1)[1]
        URL = "https://backend.craiyon.com/generate"
        res = (
            await self.__http.request_json(
                URL,
                method="POST",
                json={
                    "prompt": text,
                },
            )
        ).get("images")
        images = [BytesIO(base64.decodebytes(i.encode("utf-8"))) for i in res]
        await self.__bot.reply_photo(message, images)
        map(lambda x: x.close(), images)

    @cmd(help_="/story <text> -- история от GPT2")
    async def story(self, message):
        input_str = message.text.split(maxsplit=1)[1]
        response = await self.__http.request_json(
            "https://pelevin.gpt.dobro.ai/generate/",
            method="POST",
            json={"prompt": input_str, "length": 100},
        )
        await self.__bot.answer(message, input_str + response["replies"][0])

    @cmd(help_="/gpt <text> -- запрос для chatgpt")
    async def gpt(self, message):
        prompt = message.text.split(" ", 1)[1]
        response = await self.__http.request_json(
            "https://api.openai.com/v1/chat/completions",
            method="POST",
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
            },
            headers={"Authorization": f"Bearer {openai_token}"},
        )
        await self.__bot.reply(message, response["choices"][0]["message"]["content"])

    async def calc__(self, input_str: str):
        signal.alarm(TIMEOUT)
        res = sympy_eval(input_str)
        signal.alarm(0)
        res_str = f"Input:$${res['input']}$$\nOutput:$${res['output']}$$"
        try:
            resp_svg = await self.__http.request_content(
                "https://math.vercel.app/",
                params={
                    "from": r"\begin{aligned} & \text{Input:} \\"
                    + rf"& {res['input']} \\"
                    + r"& \text{Output:} \\"
                    + f"& {res['output']}"
                    + r"\end{aligned}"
                },
            )
            buff = BytesIO()
            svg2png(bytestring=resp_svg, write_to=buff, dpi=200)
            buff.seek(0)
        except Exception:
            return res_str
        else:
            return buff

    @cmd(
        sigflag=True,
        help_="/calc [Sympy_command] -- вызов интерпретатора СКА Sympy",
        help_ext="""Примеры:
/calc integrate(cos(x)) -- интегрирование
/calc diff(cos(x)) -- дифференцирование
/calc solve(x^3 + 2x^2 - 4x + 1) -- поиск корней
""",
    )
    async def calc(self, message):
        buff = await self.calc__(message.text.split(" ", 1)[1])
        if isinstance(buff, str):
            await self.__bot.answer(message, buff)
        else:
            await self.__bot.answer_photo(message, buff)
            buff.close()

    def plot__(self, input_str: str):
        signal.alarm(TIMEOUT)
        fig = sympy_eval(input_str.rsplit(")", 1)[0] + ",show=False)", plot=True)
        buff = BytesIO()
        signal.alarm(TIMEOUT)
        fig.save(buff)
        signal.alarm(0)
        del fig
        buff.seek(0)
        return buff

    @cmd(
        sigflag=True,
        regexp=True,
        help_="/plot[...] -- вызов sympy-функций для вывода графиков",
        help_ext="""Примеры:
/plot(x, x^2, x^3) -- вывод нескольких графиков
/ploti(x^2 - y^2 - 1) -- вывод графика, заданного уравнением
Синонимы:
ploti -- plot_implicit
plot3ds -- plot3d_parametric_surface
plot3dL -- plot3d_parametric_line
""",
    )
    async def plot(self, message):
        buff = self.plot__(message.text[1:])
        await self.__bot.answer_photo(message, buff)
        buff.close()
