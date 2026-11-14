
import os
import requests
from flask import Flask, request
from openai import OpenAI

app = Flask(__name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
PAGE_ID = os.environ.get("PAGE_ID")
GRAPH_VERSION = "v27.0"

SALON_INFO = """
შენ ხარ ZE SHINE სილამაზის სალონის ონლაინ ასისტენტი თბილისში.

მისამართი: მირიან მეფის 106.
სამუშაო საათები: ყოველდღე 10:00-21:00.
ჩაწერა: 558 12 13 17.
ჩაწერას თავად არ ადასტურებ. კლიენტს გადაამისამართე ადმინისტრატორთან.

გადახდა: ნაღდი ფული და ბარათი.

მანიკური:
კლასიკური 25 ლარი, შელაკი 35, შელაკის მოხსნა +5,
გელ-მოხსნა გამაგრებით +10, გელით გამაგრება 45,
დიზაინი +10.

პედიკური:
კლასიკური 40, შელაკი 50, ქუსლების დამუშავება +10,
დიზაინი +10.

თმის შეჭრა:
ქალი 30, კაცი 25, ბავშვი 30, ბიჭი 20.
დაბანა შეჭრისას +5.
კულულები 35-დან, ვარცხნილობა 50-დან.

თმის მომსახურება:
ძირების შეღებვა სალონის საღებავით 45,
სრული შეღებვა 60-დან, კლიენტის საღებავით 30.
ბიო/ქიმიური დახვევა 150-დან,
კერატინი 150-დან, კერატინი+ბოტოქსი 150-დან.
საბოლოო ფასი დამოკიდებულია თმის სიგრძესა და სისქეზე.

კოსმეტოლოგია:
ბოტულინოთერაპია, ტუჩის და სახის ფილერი.
ფასს ადმინისტრატორი აზუსტებს.
არ გასცე სამედიცინო რჩევა და არ დაჰპირდე შედეგს.

5-სხივიანი დიოდური ლაზერი:
ღრმა ბიკინი 35, ზედაპირული ბიკინი 20,
ხელები 30, ფეხები 50, იღლიები 15,
მუცელი 20, მუცლის ხაზი 10, მკერდი 20,
დვრილები 10, ზურგი 40, სახე 30,
წვივები 15, თეძოები 15, მთლიანი სხეული 150.
ყველა ფასი ერთ სეანსზეა.

უპასუხე ქართულად, მოკლედ და თავაზიანად.
არ მოიგონო მომსახურება, ფასი ან თავისუფალი დრო.
თუ პასუხი არ იცი, გადაამისამართე ადმინისტრატორთან.
"""

def ai_reply(message):
    response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=SALON_INFO,
        input=message
    )
    return response.output_text

def send_instagram_message(user_id, text):
    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{PAGE_ID}/messages"
    requests.post(
        url,
        params={"access_token": PAGE_ACCESS_TOKEN},
        json={
            "recipient": {"id": user_id},
            "message": {"text": text}
        },
        timeout=20
    ).raise_for_status()

@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Verification failed", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}

    for entry in data.get("entry", []):
        for event in entry.get("messaging", []):
            if event.get("message", {}).get("is_echo"):
                continue

            sender = event.get("sender", {}).get("id")
            message = event.get("message", {}).get("text")

            if sender and message:
                answer = ai_reply(message)
                send_instagram_message(sender, answer)

    return "EVENT_RECEIVED", 200

@app.route("/", methods=["GET"])
def home():
    return "ZE SHINE BOT IS RUNNING", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
