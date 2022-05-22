from vkbottle.bot import Message as mess_vk
from vkbottle import PhotoMessageUploader as photo_uploader
from aiogram.types import Message as mess_tg


class wrapper:
    async def answer(self, message, text: str, **kwargs):
        pass

    async def answer_photo(self, message, buff, caption: str, **kwargs):
        pass

    async def reply(self, message, text, **kwargs):
        pass


class vk_wrapper(wrapper):
    def __init__(self, api):
        self.__api = api

    async def answer(self, message: mess_vk, text: str = "", **kwargs):
        await message.answer(text, **kwargs)

    async def answer_photo(self, message: mess_vk, buff, caption: str = "", **kwargs):
        doc = await photo_uploader(self.__api).upload(buff, peer_id=message.peer_id)
        await message.answer(caption, attachment=doc)


class tg_wrapper(wrapper):
    async def answer(self, message: mess_tg, text: str = "", **kwargs):
        await message.answer(text)

    async def answer_photo(self, message: mess_tg, buff, caption: str = "", **kwargs):
        await message.answer_photo(buff, caption=caption)
