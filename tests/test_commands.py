import pytest
from utils.commands import bot_commands


class mock_message:
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return f"mock_mess: {self.text}"


def mock_http_client(result):
    class _mock_http_client:
        async def requests_content(self, url):
            return result

        async def requests_json(self, url):
            return result

        def __repr__(self):
            return f"http_client: {result}"

    return _mock_http_client()


def mock_bot(result):
    class _mock_bot:
        async def answer(self, message, data):
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
            (bot_commands.weather, "/weather Moscow", "Moscow: ☁️   🌡️-6°C 🌬️←19km/h"),
        ),
        # ("/calc "),
    ],
)
@pytest.mark.asyncio
async def test_inner_handler(method, input_data, result):
    bot = mock_bot(result)
    message = mock_message(input_data)
    commands = bot_commands(bot)
    await method(commands, message)


# @pytest.mark.asyncio
# async def test_urls_hanler(input_data, result):
#     bot = mock_bot(result)
#     message = mock_message(input_data)
#     commands = bot_commands(bot)
#     await commands.
