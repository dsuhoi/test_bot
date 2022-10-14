from types import FunctionType

from aiogram.types import InputFile, InputMediaPhoto
from aiogram.types import Message as mess_tg
from vkbottle import PhotoMessageUploader as photo_uploader
from vkbottle.bot import Message as mess_vk


class meta_cmd(type):
    def __new__(mcs, name, bases, attrs):
        cmd_list = attrs.setdefault("COMMANDS", list())
        for key, value in attrs.items():
            if isinstance(value, FunctionType) and value.__name__ == "__cmd":
                cmd_list.append({"name": key, **value.command_params})
        return super().__new__(mcs, name, bases, attrs)


def cmd(**kwargs):
    def decorator(func):
        async def __cmd(*args, **kwargs):
            return await func(*args, **kwargs)

        __cmd.command_params = kwargs
        return __cmd

    return decorator


class vk_wrapper:
    def __init__(self, api):
        self.__api = api

    async def __upload(
        self, message: mess_vk, text: str = "", buff=None, reply_to=False, **kwargs
    ):
        data = {}
        if buff:
            if isinstance(buff, list):
                doc = [
                    await photo_uploader(self.__api).upload(b, peer_id=message.peer_id)
                    for b in buff
                ]
            else:
                doc = await photo_uploader(self.__api).upload(
                    buff, peer_id=message.peer_id
                )
            data["attachment"] = doc

        if reply_to:
            await message.reply(text, **data, **kwargs)
        else:
            await message.answer(text, **data, **kwargs)

    async def answer(self, message: mess_vk, text: str = "", **kwargs):
        await self.__upload(message, text, **kwargs)

    async def reply(self, message: mess_vk, text: str = "", **kwargs):
        await self.__upload(message, text, reply_to=True, **kwargs)

    async def answer_photo(self, message: mess_vk, buff, caption: str = "", **kwargs):
        await self.__upload(message, caption, buff, **kwargs)

    async def reply_photo(self, message: mess_vk, buff, caption: str = "", **kwargs):
        await self.__upload(message, caption, buff, reply_to=True, **kwargs)


class tg_wrapper:
    def media_upload(buff_list, **kwargs):
        return [InputMediaPhoto(InputFile(buff), **kwargs) for buff in buff_list]

    async def __upload(
        self, message: mess_tg, text: str = "", buff=None, reply_to=False, **kwargs
    ):
        if buff:
            if isinstance(buff, list):
                if reply_to:
                    await message.reply_media_group(tg_wrapper.media_upload(buff))
                else:
                    await message.answer_media_group(tg_wrapper.media_upload(buff))

            else:
                if reply_to:
                    await message.reply_photo(buff, caption=text, **kwargs)
                else:
                    await message.answer_photo(buff, caption=text, **kwargs)
        else:
            if reply_to:
                await message.reply(text, **kwargs)
            else:
                await message.answer(text, **kwargs)

    async def answer(self, message: mess_tg, text: str = "", **kwargs):
        await self.__upload(message, text, **kwargs)

    async def reply(self, message: mess_tg, text: str = "", **kwargs):
        await self.__upload(message, text, reply_to=True, **kwargs)

    async def answer_photo(self, message: mess_tg, buff, caption: str = "", **kwargs):
        await self.__upload(message, caption, buff, **kwargs)

    async def reply_photo(self, message: mess_tg, buff, caption: str = "", **kwargs):
        await self.__upload(message, caption, buff, reply_to=True, **kwargs)
