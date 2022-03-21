import asyncio as ac
import logging
import signal
from io import BytesIO

from sympy import preview

from sympy_wrapper import vmw_eval, vmw_plot  # local module

TIMEOUT = 15
signal.signal(
    signal.SIGALRM,
    lambda sig, st: (_ for _ in ()).throw(Exception("Превышен лимит по времени!")),
)

logging.basicConfig(format="[%(levelname)s]:<%(asctime)s>: %(message)s")


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


def help_():
    return """Инструкция к боту:
/help -- вызов инструкции (кто б знал...)
/manuls <start | stop> <A> <B> -- вызов/остановка подсчёта манулов в диапазоне [A;B]
/calc [команда_Sympy] -- вызов интерпретатора СКА Sympy (Доки: https://docs.sympy.org/latest/index.html)
/plot[...] -- вызов sympy-функций для вывода графиков (Доки: https://docs.sympy.org/latest/modules/plotting.html)
"""


async def manuls_init(message, _state):
    *_, start, end = message.text.split()
    start, end = int(start), int(end)
    if 0 < start <= end:
        await message.answer(f"Подсчёт от {start} и до {end}:")
        n_ends = [2, 0, 1, 1, 1, 2]
        str_ends = ["", "а", "ов"]
        for i in range(start, end + 1):
            res_s = f"{i} манул{str_ends[2 if 4 < (i % 100) < 20 else n_ends[min(i % 10, 5)]]}"
            await message.answer(res_s)
            await ac.sleep(0.15)
            if _state():
                await message.answer("Остановка подсчёта")
                break


def calc_(input_str: str):
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


def plot_(input_str: str):
    signal.alarm(TIMEOUT)
    fig = vmw_plot(input_str.rsplit(")", 1)[0] + ",show=False)")
    buff = BytesIO()
    signal.alarm(TIMEOUT)
    fig.save(buff)
    signal.alarm(0)
    del fig
    buff.seek(0)
    return buff
