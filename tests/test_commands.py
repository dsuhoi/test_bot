import pytest
from app.commands import bot_commands


class mock_message:
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return f"mock_mess: {self.text}"


class mock_http_client:
    def __init__(self, data=dict()):
        self.__data = data

    async def request_text(self, url, *args, **kwargs):
        return self.__data.get(url)

    async def request_content(self, url, *args, **kwargs):
        return self.__data.get(url)

    async def request_json(self, url, *args, **kwargs):
        return self.__data.get(url)

    def __repr__(self):
        return f"http_client: {self.__data}"


def mock_bot(result):
    class _mock_bot:
        async def answer(self, message, data):
            assert data == result

        async def reply(self, message, data):
            assert data == result

        def __repr__(self):
            return f"mock_bot: {result}"

    return _mock_bot()


@pytest.mark.parametrize(
    "method, input_data, result",
    [
        (
            bot_commands.help,
            "/help translate",
            "Примеры:\n/translate Hello world!\n/translate -L ja Привет мир!\n",
        ),
        (bot_commands.translate, "/translate Hello world!", "Привет, мир!"),
    ],
)
@pytest.mark.asyncio
async def test_inner_handler(method, input_data, result):
    bot = mock_bot(result)
    message = mock_message(input_data)
    commands = bot_commands(bot)
    await method(commands, message)


@pytest.mark.parametrize(
    "method, url_data, input_data, result",
    [
        (
            bot_commands.weather,
            {"https://wttr.in/Moscow?m&format=4": "Moscow: -5°C ←19km/h"},
            "/weather Moscow",
            "Moscow: -5°C ←19km/h",
        )
    ],
)
@pytest.mark.asyncio
async def test_urls_hanler(method, url_data, input_data, result):
    http_client = mock_http_client(url_data)
    bot = mock_bot(result)
    message = mock_message(input_data)
    commands = bot_commands(bot, http_client)
    await method(commands, message)
