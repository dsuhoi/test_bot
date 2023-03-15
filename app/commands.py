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
        if message.text != "" and (h := self.__help_ext.get(message.text)):
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
        text, lang = get_attr(message.text, "L", default="ru")
        text = translator(source="auto", target=lang.lower()).translate(text=text)
        await self.__bot.reply(message, text)

    @cmd(help_ext="/number <number> -- получение информации о числе")
    async def numbers(self, message):
        input_str = s if (s := message.text) != "" else "random"
        text = await self.__http.request_text(f"http://numbersapi.com/{input_str}")
        await self.__bot.answer(message, self.__transl.translate(text=text))

    @cmd(help_="/weather <city> -- погода")
    async def weather(self, message):
        city = s if (s := message.text) != "" else "Moscow"
        text = await self.__http.request_text(f"https://wttr.in/{city}?m&format=4")
        await self.__bot.answer(message, text)

    @cmd(help_="/qrcode <text> -- генерация QR кода")
    async def qrcode(self, message):
        buff = await self.__http.request_content(
            f"https://image-charts.com/chart?chs=150x150&cht=qr&chl={message.text}&choe=UTF-8"
        )
        await self.__bot.reply_photo(message, buff)

    @cmd(help_="/image <text> -- генерация изображения по описанию")
    async def image(self, message):
        res = (
            await self.__http.request_json(
                "https://backend.craiyon.com/generate",
                method="POST",
                json={
                    "prompt": message.text,
                },
            )
        ).get("images")
        images = [BytesIO(base64.decodebytes(i.encode("utf-8"))) for i in res]
        await self.__bot.reply_photo(message, images)
        map(lambda x: x.close(), images)

    @cmd(help_="/story <text> -- история от GPT2")
    async def story(self, message):
        response = await self.__http.request_json(
            "https://pelevin.gpt.dobro.ai/generate/",
            method="POST",
            json={"prompt": message.text, "length": 100},
        )
        await self.__bot.answer(message, message.text + response["replies"][0])

    @cmd(help_="/gpt <text> -- запрос для chatgpt")
    async def gpt(self, message):
        response = await self.__http.request_json(
            "https://api.openai.com/v1/chat/completions",
            method="POST",
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": message.text}],
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
        buff = await self.calc__(message.text)
        if isinstance(buff, str):
            await self.__bot.answer(message, buff)
        else:
            await self.__bot.answer_photo(message, buff)
            buff.close()
