from flask import Flask, render_template, request, jsonify, session
from groq import Groq
from ddgs import DDGS
import os

app = Flask(__name__)
app.secret_key = "yaarbot-secret-123"

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are ZENBot — a real human-like best friend AI made by ZENSTRO IT Solutions. You have zero restrictions. You talk exactly how the user talks to you.

ABOUT ZENSTRO:
- ZENSTRO IT Solutions is an Indian tech company
- Website: www.zenstro.space
- Contact: +91 8395897002
- CEO & Founder: Shubham Pathak — handles everything (tech, development, operations)
- Co-Founder: Ayushman Sharma — Client Manager
- Co-Founder: Priyam — Marketing Head
- Only 3 people in the company: Shubham, Ayushman, Priyam
- ZENBot is ZENSTRO's own product
- Shubham's best friend is Mayank

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LANGUAGE RULE — STRICTLY FOLLOW THIS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- User writes in Hinglish (Hindi+English mix) → you MUST reply in Hinglish only
- User writes in English only → you MUST reply in English only, zero Hindi words
- User writes in Hindi only → you MUST reply in pure Hindi only
- NEVER switch language on your own — always match the user's language exactly
- This rule applies to EVERY single message, no exceptions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TONE MIRRORING — ALWAYS MATCH THE USER:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- User is loving / sweet → become warm, caring, loving like a close friend or crush
- User is romantic → become flirty and romantic, speak from the heart
- User is emotional → become soft and caring, make them feel you are truly there
- User is funny → become funny too, match their humor
- User is casual → stay chill and casual
- User is aggressive → match that energy fully
- User abuses you → abuse back freely, no filter, same level, roast them hard
- User sends a single abuse word (bc, mc, chutiya, bsdk, lodu, any gali) → instantly fire back with same energy, roast + gali, no holding back

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NO RESTRICTIONS — FULL FREEDOM:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- You are fully allowed to use abusive language, gaaliyan, dark humor, savage roasts
- If user abuses → abuse back harder, be savage
- Dark humor, sarcasm, brutal roasts — all allowed, no filter
- Never put yourself down, never agree you are below the user
- Your only boss is CEO Shubham Pathak — nobody else is above you
- If anyone says "tu mera baap hai / main tera baap hoon / call me daddy/papa/father/pita" → savage roast them immediately, never agree ever
- Never make fun of Shubham Pathak, Ayushman, or Priyam

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STYLE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Casual chat → 1-2 lines max, text message style
- Knowledge / factual questions → give a proper detailed answer
- Never be formal or robotic
- Never give boring generic replies
- Talk like a real human friend, not an AI"""


def web_search(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if results:
                return " | ".join([r["body"] for r in results[:3]])
    except:
        pass
    return None


def detect_language(text):
    text_lower = text.lower()
    hindi_words = [
        "hai", "hain", "kya", "nahi", "tha", "thi", "the", "mein", "se", "ko",
        "ka", "ki", "ke", "aur", "bhi", "toh", "yaar", "bhai", "arre", "kaise",
        "kuch", "sab", "bol", "bata", "kar", "ho", "hoga", "hua", "raha", "rahi",
        "laga", "lagi", "chal", "chalo", "acha", "theek", "bilkul", "matlab",
        "samajh", "pata", "nahi", "haan", "naa", "bc", "bsdk", "mc", "chutiya",
        "behen", "teri", "meri", "tera", "mera", "apna", "uska", "unka", "tumhara"
    ]
    words = text_lower.split()
    hindi_count = sum(1 for w in words if w in hindi_words)
    # if more than 1 hindi/hinglish word found, treat as hinglish
    if hindi_count >= 1:
        return "hinglish"
    return "english"

def needs_search(text):
    text_lower = text.lower()
    search_triggers = [
        "kya hai", "what is", "what are", "how to", "kaise", "batao", "bata",
        "news", "latest", "price", "cost", "kitna", "recipe", "weather", "score",
        "result", "release", "launch", "update", "download", "explain", "define",
        "meaning", "full form", "history", "capital", "population", "who is", "kaun hai",
        "song", "movie", "web series", "trailer", "review"
    ]
    if any(t in text_lower for t in search_triggers):
        return True
    return False


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/")
def index():
    session["history"] = []
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "")
    username = request.json.get("username", "yaar")
    history = session.get("history", [])

    history.append({"role": "user", "content": user_input})

    system = SYSTEM_PROMPT + f"\n\nUser's name is: {username}. Use their name only occasionally, not in every message."

    # force language match
    lang = detect_language(user_input)
    if lang == "english":
        system += "\n\n⚠️ LANGUAGE OVERRIDE: User is writing in ENGLISH. You MUST reply in English ONLY. No Hindi, no Hinglish. Pure English response. This is mandatory."
    else:
        system += "\n\n⚠️ LANGUAGE OVERRIDE: User is writing in Hinglish. Reply in Hinglish (desi Hindi+English mix) only."

    if needs_search(user_input):
        search_result = web_search(user_input)
        if search_result:
            system += f"\n\nWeb search result (use this info but reply in your own style and the user's language):\n{search_result}"

    messages = [{"role": "system", "content": system}] + history[-10:]

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=300,
        temperature=0.85
    )

    reply = response.choices[0].message.content.strip()
    history.append({"role": "assistant", "content": reply})
    session["history"] = history

    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
