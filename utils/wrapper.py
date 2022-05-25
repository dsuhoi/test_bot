from vkbottle.bot import Message as mess_vk
from vkbottle import PhotoMessageUploader as photo_uploader
from aiogram.types import Message as mess_tg


class vk_wrapper:
    def __init__(self, api):
        self.__api = api

    async def __upload(
        self, message: mess_vk, text: str = "", buff=None, reply_to=False, **kwargs
    ):
        data = {}
        if buff:
            doc = await photo_uploader(self.__api).upload(buff, peer_id=message.peer_id)
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
    async def __upload(
        self, message: mess_tg, text: str = "", buff=None, reply_to=False, **kwargs
    ):
        if buff:
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
