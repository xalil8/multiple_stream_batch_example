import telegram

test_bot = telegram.Bot(token="6670171232:AAFMTfDvzrpJ47Djq3rBtCpK59L2gMdGLy4") # sadece yelek ile ilgili resimleri göndermek icin var
test_bot.send_photo(chat_id="-1001875614534",photo=open("./logs/yelek_detections/1_1_image.jpg", "rb"),caption=f"deneme")
