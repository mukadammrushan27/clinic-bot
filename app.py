import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# 1. Configure your Google Gemini API
# Get your free key from https://google.com
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

# 2. Configure WhatsApp Credentials (from Meta Developer Dashboard)
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "my_secret_token_123") # You invent this password

# Meta WhatsApp Webhook Verification
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification failed", 403

# Handle incoming WhatsApp Messages
@app.route("/webhook", methods=["POST"])
def handle_whatsapp_message():
    body = request.get_json()
    
    try:
        # Extract message content and sender info
        entry = body["entry"][0]["changes"][0]["value"]
        if "messages" in entry:
            message = entry["messages"][0]
            patient_phone = message["from"]
            
            # Ensure it is a text message
            if message["type"] == "text":
                patient_text = message["text"]["body"]
                
                # Ask Gemini for the response
                ai_response = model.generate_content(patient_text).text
                
                # Send the answer back to WhatsApp
                send_whatsapp_message(patient_phone, ai_response)
                
    except Exception as e:
        print(f"Error processing message: {e}")
        
    return jsonify({"status": "success"}), 200

def send_whatsapp_message(to_phone, text_content):
    url = f"https://facebook.com{PHONE_NUMBER_ID}/messages"
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
    requests.post(url, json=payload, headers=headers)

if __name__ == "__main__":
    app.run(port=5000)
