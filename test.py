import os
import google.generativeai as genai
import requests

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-pro",
  generation_config=generation_config,
)
url = "https://www.1mg.com/drugs/dolo-650-tablet-74467?srsltid=AfmBOopIPIeB3jN7N5ilsTnpoL5AzkDMfimF7VQ7TQTgUTNaqzIlnlOP"
markdown_webpage = requests.get(f"https://r.jina.ai/{url}").text



response = model.generate_content([
  "You are an AI for extracting only the medicine usage etc details from a given markdown and provide a formated beautiful designed html, the part that says the usage of medicine should be at top, you shouldn't include the details such as marketed by, FAQ and etc..",
  f"input: {markdown_webpage}",
  "output: ",
])

response = response.text[7:-3]

print(response)