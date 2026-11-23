import google.generativeai as genai
import os

print("Fetching available models...")
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

try:
    models = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
    print("\nAvailable models for your API key:")
    for m in models:
        print(f"- {m}")
except Exception as e:
    print(f"Error fetching models: {e}")
