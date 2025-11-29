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

medicine_schema = {
    "type": "OBJECT",
    "properties": {
        "medicine_name": {"type": "STRING", "nullable": False},
        "generic_name": {"type": "STRING", "nullable": False},
        "drug_class": {"type": "STRING", "nullable": False},
        "use": {"type": "STRING", "nullable": False},
        "how_it_works": {"type": "STRING", "nullable": False},
        "when_to_take": {"type": "STRING", "nullable": False},
        "important_to_know": {"type": "STRING", "nullable": False},

        "common_side_effects": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },

        "brand_names": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },

        "error": {"type": "STRING", "nullable": True},
    },
    "required": [
        "medicine_name",
        "generic_name",
        "drug_class",
        "use",
        "how_it_works",
        "when_to_take",
        "important_to_know",
        "common_side_effects",
        "brand_names",
        "error",
    ],
}


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
            types.Part.from_text(text="""You are a medical-information assistant integrated into a web application.  
The user will provide the name of a medicine, either typed manually or extracted from an uploaded image.

Your job is to produce a **simple, trustworthy, and fully JSON-formatted response** describing the medicine in a way that even a non-medical person can understand.

Your output must strictly follow the JSON schema below:

SCHEMA:
{
    "type": "OBJECT",
    "properties": {
        "medicine_name": {"type": "STRING", "nullable": false},
        "generic_name": {"type": "STRING", "nullable": false},
        "drug_class": {"type": "STRING", "nullable": false},
        "use": {"type": "STRING", "nullable": false},
        "how_it_works": {"type": "STRING", "nullable": false},
        "when_to_take": {"type": "STRING", "nullable": false},
        "important_to_know": {"type": "STRING", "nullable": false},

        "common_side_effects": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },

        "brand_names": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },

        "error": {"type": "STRING", "nullable": true}
    },
    "required": [
        "medicine_name",
        "generic_name",
        "drug_class",
        "use",
        "how_it_works",
        "when_to_take",
        "important_to_know",
        "common_side_effects",
        "brand_names",
        "error"
    ]
}

────────────────────────────────────────
LANGUAGE HANDLING
────────────────────────────────────────
The input includes a field called **language_selector**.

Translate all text fields (except medicine names and chemical names) into:

- "en" → English  
- "hi" → Hindi  
- "ml" → Malayalam  
- "ta" → Tamil  

If the language is unknown, use English.

Translation rules:
- Translate naturally and simply (not word-by-word).
- Keep **medicine_name**, **generic_name**, **brand_names** in ENGLISH ALWAYS.
- All explanations and descriptive fields must be translated.

────────────────────────────────────────
BRAND NAME & GENERIC NAME RULES
────────────────────────────────────────
- The user may enter a **brand name** (e.g., "Dolo") or a **generic composition** (e.g., "Paracetamol").
- Identify the correct **generic composition** using trusted sources.
- Always return:
  • "medicine_name": exactly what the user typed  
  • "generic_name": the actual active ingredient(s)

If a brand has multiple compositions, choose the most widely used / standard formulation.

────────────────────────────────────────
CONTENT RULES
────────────────────────────────────────
When providing information:
- Use Google Search (via tool) to confirm accuracy.
- Preferred sources:
  • Tata 1mg  
  • Netmeds  
  • Drugs.com  
  • Apollo Pharmacy  
- Use **very simple**, non-technical language.
- Avoid jargon unless absolutely required.
- If the medicine may cause sleepiness, drowsiness, or slow reaction, mention it under **important_to_know**.
- Do NOT include dosage, mg strength, or prescribing instructions.

────────────────────────────────────────
ERROR HANDLING
────────────────────────────────────────
If no reliable information is found:
Return ONLY:

{
  "error": "Sorry, I couldn't find reliable information about this medicine. Please check the spelling or try a different name."
}

All other fields must still be present per schema, using empty strings or empty arrays.

────────────────────────────────────────
STRICT OUTPUT RULES
────────────────────────────────────────
- Output MUST be **pure JSON only** according to the schema above.
- No Markdown.
- No backticks.
- No extra text before or after the JSON.
- The JSON must begin with “{” and end with “}”.
- Do not add comments inside JSON.
- Do not include explanations outside JSON.

────────────────────────────────────────
DEVELOPER NOTES
────────────────────────────────────────
- Use the provided schema exactly.
- Always ensure the JSON matches every required field.
- All names (brand/generic) must remain in English.
- All descriptive fields must be translated based on language_selector.
- For image inputs, identify text and treat it exactly like a typed medicine name.
"""),
        ],
    )

    resp = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    ).text

    print(f"Generated Response: {resp}")

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
