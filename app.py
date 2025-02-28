from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage
import cv2
from keras.models import load_model
from keras.preprocessing.image import load_img
import numpy as np
import os

# line_bot_api = LineBotApi('LINE_CHANNEL_ACCESS_TOKEN')
# handler = WebhookHandler('LINE_CHANNEL_SECRET')

line_bot_api = LineBotApi('7Y10gL12VmYp/4zAWn4PQxGQ0EQR7Jbh4ZOtKFEEUgH0g00kZNO5JUgZ0h/GnLPB0A/43R7G8KujRkicjukFOPfcgthBYm3oz44T0HEyEvFKyROkpXDtDrDAMpTns6xX2rycAwR9U6lxFt9Yaa9vhAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('a1f71912a687e5b25b3ca449ed9e4629')
app = Flask(__name__)

directory = "uploadImages"
if not os.path.exists(directory):
    os.makedirs(directory)

# Webhook route for LINE Messaging API
@app.route('/webhook', methods=['GET','POST'])
def webhook():
    # Get X-Line-Signature header and request body
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # Handle webhook events
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)  

    return 'Connection'  

# Event handler for text messages
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # Extract message text from the event
    message_text = event.message.text

    # Reply to the user with the same message
    reply_message = TextSendMessage(text=message_text)
    line_bot_api.reply_message(event.reply_token, reply_message)

# Event handler for images messages
    
model = load_model("model.h5")

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    # รับข้อมูลรูปภาพ
    message_content = line_bot_api.get_message_content(event.message.id)

    # ตั้งชื่อไฟล์
    filename = f"image_{event.message.id}.jpg"
    filepath = os.path.join(directory, filename)


    # บันทึกไฟล์
    with open(filepath, "wb") as f:
        for chunk in message_content.iter_content():
            f.write(chunk)

    # อ่านรูปภาพ
    img1 = cv2.imread(filepath)

    # แปลงสี
    img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)

    # ปรับขนาด
    img1 = cv2.resize(img1, (224, 224))

    # แปลงเป็น array
    img1 = np.array(img1) / 255.0

    # เปลี่ยนมิติ
    img1 = np.reshape(img1, (1, 224, 224, 3))

    # ทำนาย
    prediction = model.predict(img1)

    # ดึงคลาสและความน่าจะเป็น
    label = ['Anthracnose', 'Healthy']
    result = label[np.argmax(prediction)]
    percen = prediction[0][np.argmax(prediction)]*100

    # แสดงผลลัพธ์
    # print(prediction)
    # print(f"ความน่าจะเป็น:{prediction[0][np.argmax(prediction)]}")
    # print(f"คลาสที่ทำนาย: {result}")

    # ส่งผลลัพธ์กลับไปยังผู้ใช้
    line_bot_api.reply_message(
        event.reply_token,
        [
            TextSendMessage(text=f"เป็นใบ {result}"),
            TextSendMessage(text=f"โอกาศ {round(percen,2)}%"),
            TextSendMessage(text=f"{prediction}")

        ],
    )
if __name__ == '__main__':
    app.run(port=8000,debug=True)
    
