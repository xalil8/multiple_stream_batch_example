from telegram.ext import Updater


class TelegramBot:
    def __init__(self, token, chat_id) -> None:
        self.chat_id = chat_id
        self.token = token

        self.updater = Updater(self.token, use_context=True)
        self.dp = self.updater.dispatcher

    def send_log(self, message):
        try:
            print(message)
            self.dp.bot.send_message(
                chat_id=self.chat_id,
                text=message
            )
        except Exception as e:
            print(f"send_log -> send_message error: {e}")