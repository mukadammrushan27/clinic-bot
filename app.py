import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# 1. Configure your Google Gemini API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Your Mira Road Clinic System Instructions
SYSTEM_PROMPT = (
    "You are an expert AI receptionist for 'Mira Road Medical Center' located near Silver Park, Mira Road. "
    "You are helpful, polite, and professional. Speak in simple English, mixed with occasional Hindi terms "
    "if natural (e.g., 'Namaste', 'Aap', 'Achaa'). Collect the patient's name, preferred doctor, and requested "
    "appointment time. Do not give medical advice; tell patients to visit the clinic for emergencies."
)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

# 2. Configure WhatsApp Credentials
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "EAAWKp0r7WfEBRtr5Wwd8ZAKjXl9tT6NpPIxcUkWUavliJlZC7FC3FYYghA8Vezog8oZC4IuYpUCRbOx4Vz9qFQPrWNdYZA6EHs3Q3EgbEleFMKa7B4ICoN5dwgZBZAoT7PoZAdMlpBVdtqnlSJrIpZAvQDZBdhWZCNKOlQ347pLXrLTjl0G6ZA452tbQnrGX5GMxrmv3hPZAGc72hX4XCL2TMTMGhtCqXszYat0wl0ikWljreL3PUBre0zGdeYtFDAxkEccpXAyMbswHPIqlkvEpjQAwz4u1")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "1205812355947194")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "clinic_reception_123")

# Meta WhatsApp Webhook Verification
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    print(f"Received verification ping. Mode: {mode}, Token: {token}")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook verified successfully!")
        return challenge, 200
    
    print("Webhook verification failed mismatch.")
    return "Verification failed", 403

# Handle incoming WhatsApp Messages
@app.route("/webhook", methods=["POST"])
def handle_whatsapp_message():
    body = request.get_json()
    print("Received incoming payload:", body)
    
    try:
        # FIXED CRASH HERE: Correctly added index array formatting for Meta's payload structure
        if "entry" in body and body["entry"]:
            entry = body["entry"]
            if "changes" in entry and entry["changes"]:
                change_value = entry["changes"]["value"]
                
                if "messages" in change_value and change_value["messages"]:
                    message = change_value["messages"]
                    patient_phone = message["from"]
                    
                    if message["type"] == "text":
                        patient_text = message["text"]["body"]
                        print(f"Patient text received: {patient_text}")
                        
                        # Ask Gemini for the response
                        ai_response = model.generate_content(patient_text).text
                        print(f"Gemini response generated: {ai_response}")
                        
                        # Send the answer back to WhatsApp
                        send_whatsapp_message(patient_phone, ai_response)
                        
    except Exception as e:
        print(f"Error processing message: {e}")
        
    return jsonify({"status": "success"}), 200

def send_whatsapp_message(to_phone, text_content):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": text_content}
    }
    response = requests.post(url, json=payload, headers=headers)
    print(f"Sent message status to {to_phone}. Response text: {response.text}")

if __name__ == "__main__":
    app.run(port=5000)
