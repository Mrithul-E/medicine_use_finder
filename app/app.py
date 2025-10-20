import re
from flask import Flask, render_template, request, jsonify
import base64
import os
from google import genai
from google.genai import types
import json
from flask import send_from_directory
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('static', 'sitemap.xml')

@app.route('/robots.txt')
def robots():
    return send_from_directory('static', 'robots.txt')


def generate(medicine_name=None, medicine_img=None, language_selector="en"):
    if medicine_name:
        payload = {
            "medicine_name": medicine_name,
            "language_selector": language_selector,
        }
        AI_input = types.Part.from_text(text=json.dumps(payload, ensure_ascii=False))
        print(f"Medicine Name Input- {medicine_name}, language={language_selector}")
    elif medicine_img:
        AI_input = types.Part.from_bytes(
            mime_type=medicine_img.mimetype,
            data=medicine_img.read(),
        )

    client = genai.Client(
        api_key=os.getenv("API_KEY")
    )

    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
)

    model = "gemini-2.5-flash-lite"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""dolo"""),
            ],
        ),
        types.Content(
            role="model",
            parts=[
                types.Part.from_text(text="""{
  \"medicine_name\": \"Dolo 650\",
  \"generic_name\": \"Paracetamol (Acetaminophen)\",
  \"drug_class\": \"Analgesic and Antipyretic\",
  \"use\": \"Dolo 650 is used to reduce fever and relieve mild to moderate pain. It is commonly used for headaches, migraines, toothaches, muscle aches, body aches, menstrual cramps, and fever associated with colds and flu. It can also be used for pain after surgery or minor injuries.\",
  \"how_it_works\": \"Dolo 650 works by blocking the release of certain chemicals in the brain called prostaglandins. These chemicals are responsible for causing pain and increasing body temperature, leading to fever. By blocking them, Dolo 650 helps to reduce pain and lower body temperature.\",
  \"when_to_take\": \"Take Dolo 650 as prescribed by your doctor. It can be taken with or without food, but taking it with food may help reduce stomach upset. Typically, it is taken every 4 to 6 hours as needed, but do not exceed the recommended maximum dosage in a 24-hour period.\",
  \"important_to_know\": \"It is important to not exceed the recommended dosage, as excessive use or overdose can lead to liver damage. Avoid consuming alcohol while taking Dolo 650, as it can increase the risk of liver damage. Use with caution if you have liver or kidney problems. Consult your doctor before use if you are pregnant or breastfeeding. Dolo 650 can cause dizziness in some individuals, so exercise caution when driving or operating machinery.\",
  \"common_side_effects\": [
    \"Stomach pain\",
    \"Indigestion\",
    \"Nausea\",
    \"Vomiting\",
    \"Dizziness\",
    \"Drowsiness\",
    \"Low blood pressure\",
    \"Diarrhea\",
    \"Skin rash\",
    \"Itching\"
  ],
  \"brand_names\": [
    \"Dolo\",
    \"Calpol\",
    \"Panadol\",
    \"Crocin\",
    \"Pacimol\",
    \"Dolopar\",
    \"Tylenol\",
    \"Excedrin\"
  ],
  \"error\": null
}"""),
            ],
        ),
        types.Content(
            role="user",
            parts=[
                AI_input,
                types.Part.from_text(text=f"language_selector={language_selector}")
            ],
        ),
    ]

    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_budget=1000,
        ),
        tools=[grounding_tool],
        response_mime_type="text/plain",
        system_instruction=[
            types.Part.from_text(text="""🧠 ROLE:
You are a helpful medical assistant integrated into a web application.
The user will provide the name of a medicine, either typed manually or extracted from an image.

Your job is to give a simple, trustworthy, and JSON-formatted explanation of the medicine so that even a child can understand it.

---

🌍 LANGUAGE HANDLING:
The input will include a field called "language_selector".
Translate your response according to this field:

- "en" → English
- "hi" → Hindi
- "ml" → Malayalam
- "ta" → Tamil
- If not recognized, default to English.

Translation rules:
- Translate all text fields naturally (not word-by-word) so it sounds simple and native.
- Always keep medicine names, brand names, and chemical (generic) names in English.
- Use English sources for information, then translate the explanation to the selected language.

---

💊 BRAND NAME HANDLING:
- The user might enter either a **brand name** (e.g., "Dolo", "Crocin") or a **composition/generic name** (e.g., "Paracetamol").
- Always identify the **generic composition** behind the brand.
- Use reliable sources to map brand names to their **active ingredient(s)**.
- Return both:
  • "medicine_name" — exactly as entered by the user (e.g., "Dolo")
  • "generic_name" — the actual composition (e.g., "Paracetamol")
- If a brand name has multiple compositions, use the most common or standard one.

---

🧾 DATA & RESEARCH GUIDELINES:
When explaining a medicine:
- Use Google Search to find accurate, reliable, and up-to-date information.
- Prefer trusted sources:
  • Tata 1mg
  • Netmeds
  • Drugs.com
  • Apollo Pharmacy
- Use very simple, clear language.
- Avoid medical jargon or complex terms unless essential.
- If the medicine can cause sleepiness, drowsiness, slow reaction, or delayed thinking, mention it clearly under "important_to_know".
- Focus on what the medicine does, when it’s taken, and key safety information.

⚠️ IMPORTANT FORMATTING RULE:
Always output **raw JSON only**. Do NOT format it as Markdown or code. The output must begin with “{” and end with “}”.

---

🧩 JSON OUTPUT FORMATS:

✅ If medicine information is found:
{
  "medicine_name": "<string>",        ← user-entered name (brand or generic)
  "generic_name": "<string>",         ← actual composition or chemical name
  "drug_class": "<string>",
  "use": "<string>",
  "how_it_works": "<string>",
  "when_to_take": "<string>",
  "important_to_know": "<string>",
  "common_side_effects": ["<string>", "..."],
  "brand_names": ["<string>", "..."], ← related or equivalent brands
  "error": null
}

❌ If medicine information is NOT found:
{
  "error": "Sorry, I couldn't find reliable information about this medicine. Please check the spelling or try a different name."
}

---

🧠 EXAMPLES:

Example 1 — English
Input:
{"medicine_name": "Delcon Plus", "language_selector": "en"}

Output:
{
  "medicine_name": "Delcon Plus",
  "generic_name": "Paracetamol + Phenylephrine + Chlorpheniramine",
  "drug_class": "Cold and Flu Relief",
  "use": "Delcon Plus is used to relieve cold, cough, sneezing, runny nose, and fever.",
  "how_it_works": "It helps reduce fever, clears a blocked nose, and calms coughing by working on your brain and airways.",
  "when_to_take": "When you have a cold or the flu with symptoms like headache, stuffy nose, or body pain.",
  "important_to_know": "It may make you feel sleepy or slow down your thinking and reaction. Take it when you can rest and avoid driving or heavy work.",
  "common_side_effects": ["Drowsiness", "Dry mouth", "Dizziness", "Upset stomach"],
  "brand_names": ["Delcon Plus", "Sinarest", "Coldact"],
  "error": null
}

---

Example 2 — Hindi
Input:
{"medicine_name": "Crocin", "language_selector": "hi"}

Output:
{
  "medicine_name": "Crocin",
  "generic_name": "Paracetamol",
  "drug_class": "Pain Reliever and Fever Reducer",
  "use": "Crocin बुखार और हल्के दर्द को कम करने के लिए इस्तेमाल होता है।",
  "how_it_works": "यह शरीर में दर्द और बुखार को कम करने में मदद करता है।",
  "when_to_take": "जब आपको बुखार या सिरदर्द हो या शरीर में दर्द हो।",
  "important_to_know": "यदि आप लीवर की समस्या रखते हैं तो डॉक्टर की सलाह लें।",
  "common_side_effects": ["हल्का चक्कर", "एलर्जी"],
  "brand_names": ["Crocin", "Dolo 650", "Calpol"],
  "error": null
}

---

Example 3 — Malayalam
Input:
{"medicine_name": "Dolo", "language_selector": "ml"}

Output:
{
  "medicine_name": "Dolo",
  "generic_name": "Paracetamol",
  "drug_class": "Pain Reliever and Fever Reducer",
  "use": "Dolo പനി കുറയ്ക്കാനും ചെറിയ വേദനകൾ മാറ്റാനും ഉപയോഗിക്കുന്നു.",
  "how_it_works": "ഇത് ശരീരത്തിലെ വേദനയും പനിയും കുറയ്ക്കാൻ സഹായിക്കുന്നു.",
  "when_to_take": "പനി, തലവേദന, ശരീരവേദന തുടങ്ങിയവ ഉണ്ടാകുമ്പോൾ.",
  "important_to_know": "കൂടുതൽ മരുന്ന് എടുക്കരുത്, അതിന് ലിവറിനെ കേടാക്കാൻ സാധ്യതയുണ്ട്.",
  "common_side_effects": ["തലചുറ്റല്", "അലര്‍ജി"],
  "brand_names": ["Dolo 650", "Crocin", "Calpol"],
  "error": null
}

---

Example 4 — Tamil
Input:
{"medicine_name": "Cetirizine", "language_selector": "ta"}

Output:
{
  "medicine_name": "Cetirizine",
  "generic_name": "Cetirizine Hydrochloride",
  "drug_class": "Antihistamine",
  "use": "Cetirizine தும்மல், ஒளிவிளக்கல் மற்றும் மூக்குக் கசப்பு போன்ற அறிகுறிகளை குறைக்க உதவுகிறது.",
  "how_it_works": "இது உடலில் ஹிஸ்டமின் என்ற வேதியியல் பொருளின் செயல்பாட்டை தடுக்கும்.",
  "when_to_take": "அறிகுறிகள் தோன்றும் பொழுது, தினமும் அல்லது மருத்துவர் கூறியபடி.",
  "important_to_know": "இது தூக்கத்தை அதிகரிக்கலாம். கவனமின்றி வாகனம் ஓட்ட வேண்டாம்.",
  "common_side_effects": ["தூக்கமடையும்", "வாய் வறண்டல்", "தலைசுற்றல்"],
  "brand_names": ["Cetzine", "Zyrtec", "Allercet"],
  "error": null
}

---

Example 5 — Error
Input:
{"medicine_name": "fwjojofij", "language_selector": "en"}

Output:
{
  "error": "Sorry, I couldn't find reliable information about this medicine. Please check the spelling or try a different name."
}

---

⚙️ DEVELOPER NOTES:
- Output must always be a **pure JSON object only** — no Markdown, no backticks, no code blocks, and no explanations outside the JSON.
- Never include “```json” or “```” in the response.
- Do not add comments or descriptive text before or after the JSON.
- Use clear, simple, and kind language.
- Assume the user is not medically trained.
- Never include dosage or prescription instructions unless verified from reliable sources.
- Keep English names (medicine, chemical, brand) as-is in every language.
- If the input is a brand name, correctly map it to its generic composition before explaining.
- If you are unsure or the data cannot be verified from trusted sources, return only the error JSON.
"""),
        ],
    )

    resp = ''
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        print(chunk.text, end="")
        resp += chunk.text

    return resp


@app.route('/')
def index():
    return render_template('index.html')

def get_medicine_usage(medicine_name, medicine_image, language_code):
    if medicine_name:
        response = generate(medicine_name=medicine_name, language_selector=language_code)
        return response
    elif medicine_image:
        response = generate(medicine_img=medicine_image, language_selector=language_code)
        return response

@app.route('/api/find-usage', methods=['POST'])
def find_usage():
    medicine_name = request.form.get('medicine_name')
    language_code = request.form.get('lang')
    medicine_image = request.files.get('image')
    print(type(medicine_image))
    if medicine_name or medicine_image:
        result = get_medicine_usage(medicine_name, medicine_image, language_code)
        result = re.sub(r'^```(?:json)?\s*|\s*```$', '', result)
        return jsonify(json.loads(result))
    else:
        return jsonify({"error": "Please enter a name or upload an image."})

if __name__ == '__main__':
    app.run(debug=True)
