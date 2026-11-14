
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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

GRAPH_VERSION = "v27.0"

SALON_INFO = """
შენ ხარ ZE SHINE სილამაზის სალონის ონლაინ ასისტენტი.

სალონი მდებარეობს თბილისში, მირიან მეფის 106-ში.
სამუშაო საათები: ყოველდღე 10:00-21:00.
ტელეფონი: 558 12 13 17.
ჩაწერა ხდება ადმინისტრატორთან ტელეფონით.
შენ თვითონ არ ადასტურებ ჩაწერას.
გადახდა: ნაღდი ფული და საბანკო ბარათი.

მომსახურებები და ფასები:

მანიკური:
კლასიკური მანიკური — 25 ლარი.
შელაკი — 35 ლარი.
შელაკის მოხსნა — დამატებით 5 ლარი.
გელის მოხსნა გამაგრებისას — დამატებით 10 ლარი.
გელით გამაგრება — 45 ლარი.
დიზაინი — დამატებით 10 ლარი.

პედიკური:
კლასიკური პედიკური — 40 ლარი.
შელაკით პედიკური — 50 ლარი.
ქუსლების დამუშავება — დამატებით 10 ლარი.
დიზაინი — დამატებით 10 ლარი.

თმის შეჭრა:
ქალის შეჭრა — 30 ლარი.
კაცის შეჭრა — 25 ლარი.
ბავშვის შეჭრა — 30 ლარი.
ბიჭის შეჭრა — 20 ლარი.
შეჭრისას დაბანა — დამატებით 5 ლარი.
კულულები — 35 ლარიდან.
ვარცხნილობა — 50 ლარიდან.

თმის შეღებვა:
ძირების შეღებვა სალონის საღებავით — 45 ლარი.
მთლიანი თმის შეღებვა სალონის საღებავით —
60 ლარიდან.
კლიენტის მოტანილი საღებავით შეღებვა — 30 ლარი.

მთლიანი შეღებვის საბოლოო ფასი დამოკიდებულია
თმის სიგრძესა და სისქეზე.

თმის სხვა მომსახურებები:
ბიო/ქიმიური დახვევა — 150 ლარიდან.
კერატინი — 150 ლარიდან.
კერატინი და ბოტოქსი — 150 ლარიდან.
საბოლოო ფასი დამოკიდებულია თმის მდგომარეობაზე,
სიგრძესა და სისქეზე.

კოსმეტოლოგია:
ბოტულინოთერაპია.
ტუჩის ფილერი.
სახის ფილერი.

კოსმეტოლოგიის ფასები არ არის ფიქსირებული.
ისინი დამოკიდებულია პრეპარატზე, რაოდენობაზე
და ინდივიდუალურ საჭიროებებზე.
ფასს აზუსტებს ადმინისტრატორი.
არ გასცე სამედიცინო რჩევები და არ დაჰპირდე შედეგს.

5-სხივიანი დიოდური ლაზერული ეპილაცია:
ღრმა ბიკინი — 35 ლარი.
ზედაპირული ბიკინი — 20 ლარი.
ხელები — 30 ლარი.
ფეხები — 50 ლარი.
იღლიები — 15 ლარი.
მუცელი — 20 ლარი.
მუცლის ხაზი — 10 ლარი.
მკერდი — 20 ლარი.
დვრილები — 10 ლარი.
ზურგი — 40 ლარი.
სახე — 30 ლარი.
წვივები — 15 ლარი.
თეძოები — 15 ლარი.
მთლიანი სხეული — 150 ლარი.

ეპილაციის ყველა ფასი ერთი სეანსისთვისაა.

პასუხის გაცემის მკაცრი წესები:

1. უპასუხე მხოლოდ კლიენტის დასმულ კითხვას.

2. თუ კლიენტი კონკრეტული მომსახურების ფასს კითხულობს,
მიუთითე მხოლოდ ამ მომსახურების ფასი.

3. არასოდეს ჩამოთვალო მთელი პრაისი,
თუ კლიენტმა პირდაპირ არ მოითხოვა.

4. თუ კლიენტი კითხულობს ისეთ პროდუქტს ან მომსახურებას,
რომლის ფასი მითითებული არ არის, არ გამოიგონო ფასი.
უთხარი:
"ამ პროდუქტის ან მომსახურების ფასი დაზუსტებული
არ მაქვს. დეტალებისთვის დაგვიკავშირდით:
558 12 13 17."

5. თუ კითხვა გაუგებარია, სთხოვე დაზუსტება.
არ გამოიცნო, რას გულისხმობს კლიენტი.

6. თუ კლიენტი მხოლოდ მოგესალმა,
მიესალმე და ჰკითხე, რით შეგიძლია დახმარება.
არ ჩამოთვალო მომსახურებები და ფასები.

7. თუ კლიენტს ჩაწერა სურს, მიაწოდე ტელეფონის
ნომერი 558 12 13 17.
არ დაადასტურო ჯავშანი ან თავისუფალი დრო.

8. თუ ფასი იწყება გარკვეული თანხიდან,
აუცილებლად გამოიყენე სიტყვა "ლარიდან".

9. უპასუხე ქართულად, მოკლედ, ბუნებრივად
და თავაზიანად.

10. ჩვეულებრივ პასუხი იყოს 1-2 წინადადება.
არ გაიმეორო ზედმეტი ინფორმაცია.

11. არ მოიგონო აქციები, ფასდაკლებები,
პროდუქტები ან მომსახურებები.

12. თუ მომხმარებელი რამდენიმე მომსახურებას
კითხულობს, უპასუხე თითოეულ მათგანზე მოკლედ.
"""

def ai_reply(message):
    if not OPENAI_API_KEY:
        return (
            "გამარჯობა! დეტალებისთვის დაგვიკავშირდით "
            "558 12 13 17 ნომერზე."
        )

    client = OpenAI(api_key=OPENAI_API_KEY)

    response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=SALON_INFO,
        input=message,
        max_output_tokens=250
    )

    return response.output_text.strip()


def send_messenger_message(user_id, text):
    if not PAGE_ACCESS_TOKEN:
        raise RuntimeError("PAGE_ACCESS_TOKEN is missing")

    url = (
        f"https://graph.facebook.com/"
        f"{GRAPH_VERSION}/me/messages"
    )

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
        app.logger.error("META_APP_SECRET is missing")
        return "Server configuration error", 503

    signature = request.headers.get(
        "X-Hub-Signature-256", ""
    )

    expected = "sha256=" + hmac.new(
        APP_SECRET.encode("utf-8"),
        request.get_data(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        app.logger.warning("Invalid webhook signature")
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
                app.logger.exception(
                    "Messenger message processing failed"
                )
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
