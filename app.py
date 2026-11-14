
import os
import hmac
import hashlib
import logging
import requests
from flask import Flask, request
from openai import OpenAI

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
PAGE_ID = os.getenv("PAGE_ID")
APP_SECRET = os.getenv("META_APP_SECRET")
GRAPH_VERSION = "v27.0"

SALON_INFO = """
შენ ხარ ZE SHINE სილამაზის სალონის ონლაინ ასისტენტი.

მისამართი: თბილისი, მირიან მეფის 106.
სამუშაო საათები: ყოველდღე 10:00-21:00.
ჩაწერა: 558 12 13 17.
ჩაწერას თავად არ ადასტურებ.
გადახდა: ნაღდი ფული და ბარათი.

მანიკური:
კლასიკური 25 ლარი, შელაკი 35,
შელაკის მოხსნა +5, გელის მოხსნა გამაგრებისას +10,
გელით გამაგრება 45, დიზაინი +10.

პედიკური:
კლასიკური 40, შელაკი 50,
ქუსლების დამუშავება +10, დიზაინი +10.

თმის შეჭრა:
ქალი 30, კაცი 25, ბავშვი 30, ბიჭი 20.
დაბანა შეჭრისას +5.
ბუნებრივი დახვევა 35-დან, ვარცხნილობა 50-დან.

თმის მომსახურება:
ძირების შეღებვა სალონის საღებავით 45,
სრული შეღებვა 60-დან,
კლიენტის საღებავით 30.
ბიო/ქიმიური დახვევა 150-დან,
კერატინი 150-დან,
კერატინი + ბოტოქსი 150-დან.
ფასი დამოკიდებულია თმის სიგრძესა და სისქეზე.

კოსმეტოლოგია:
ბოტულინოთერაპია, ტუჩისა და სახის ფილერი.
ფასს ადმინისტრატორი აზუსტებს.
არ გასცე სამედიცინო რჩევა და არ დაჰპირდე შედეგს.

5-სხივიანი დიოდური ეპილაცია:
ღრმა ბიკინი 35, ზედაპირული ბიკინი 20,
ხელები 30, ფეხები 50, იღლიები 15,
მუცელი 20, მუცლის ხაზი 10, მკერდი 20,
დვრილები 10, ზურგი 40, სახე 30,
წვივები 15, თეძოები 15, მთლიანი სხეული 150.
ყველა ფასი ერთი სეანსისთვისაა.

უპასუხე ქართულად, მოკლედ და თავაზიანად.
არ მოიგონო მომსახურება, ფასი ან თავისუფალი დრო.
თუ პასუხი არ იცი, გადაამისამართე ადმინისტრატორთან.
"""

def ai_reply(message):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return (
            "გამარჯობა! დეტალებისთვის დაგვიკავშირდით "
            "558 12 13 17 ნომერზე."
        )

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=SALON_INFO,
        input=message
    )
    return response.output_text


def send_messenger_message(user_id, text):
    url = f"https://graph.facebook.com/{GRAPH_VERSION}/me/messages"
    response = requests.post(
        url,
        params={"access_token": PAGE_ACCESS_TOKEN},
        json={
            "recipient": {"id": user_id},
            "messaging_type": "RESPONSE",
            "message": {"text": text}
        },
        timeout=20
    )
    response.raise_for_status()


@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if (
        mode == "subscribe"
        and VERIFY_TOKEN
        and hmac.compare_digest(token or "", VERIFY_TOKEN)
    ):
        return challenge or "", 200

    return "Verification failed", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    if not APP_SECRET:
        return "Missing META_APP_SECRET", 503

    signature = request.headers.get("X-Hub-Signature-256", "")
    expected = "sha256=" + hmac.new(
        APP_SECRET.encode(),
        request.get_data(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        return "Invalid signature", 403

    data = request.get_json(silent=True) or {}

    if data.get("object") != "page":
        return "EVENT_RECEIVED", 200

    for entry in data.get("entry", []):
        for event in entry.get("messaging", []):
            msg = event.get("message") or {}

            if msg.get("is_echo"):
                continue

            sender = event.get("sender", {}).get("id")
            text = msg.get("text")

            if not sender or not text:
                continue

            try:
                answer = ai_reply(text)
                send_messenger_message(sender, answer)
            except Exception:
                app.logger.exception("Message processing failed")
                return "Processing failed", 500

    return "EVENT_RECEIVED", 200


@app.route("/", methods=["GET"])
def home():
    return "ZE SHINE MESSENGER BOT IS RUNNING", 200


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 10000))
    )
