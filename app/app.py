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

base_dir = os.path.dirname(os.path.abspath(__file__))
prompt_path = os.path.join(base_dir, "prompts", "system_prompt.txt")
with open(prompt_path, "r", encoding="utf-8") as f:
    system_prompt = f.read()


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
    else:
        raise ValueError("Either medicine_name or medicine_img must be provided.")

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
            types.Part.from_text(text=system_prompt),
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

def extract_json(text):
    try:
        # Find the first JSON object
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        else:
            return None
    except json.JSONDecodeError:
        return None

@app.route('/api/find-usage', methods=['POST'])
def find_usage():
    medicine_name = request.form.get('medicine_name')
    language_code = request.form.get('lang')
    medicine_image = request.files.get('image')
    print(type(medicine_image))
    if medicine_name or medicine_image:
        result = get_medicine_usage(medicine_name, medicine_image, language_code)
        
        # Robust JSON extraction
        json_data = extract_json(result)
        
        if json_data:
            return jsonify(json_data)
        else:
            # Fallback if extraction fails
            return jsonify({"error": "Failed to parse AI response", "raw_response": result})
    else:
        return jsonify({"error": "Please enter a name or upload an image."})

if __name__ == '__main__':
    app.run(debug=True)
