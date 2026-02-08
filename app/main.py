import os
from fastapi import FastAPI, Form, Response
from mangum import Mangum
from twilio.twiml.messaging_response import MessagingResponse

# Import your custom logic from other files
from app.travel_logic import get_best_route, log_expense

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "Response-able AI Bot is Online"}

@app.get("/")
@app.get("/{proxy+}")  # This catches any GET request
async def root():
    return {"status": "Response-able AI Bot is Online"}

@app.post("/")
@app.post("/whatsapp")
@app.post("/{proxy+}")  # This catches any POST request
async def whatsapp_webhook(Body: str = Form(...), From: str = Form(...)):
    
    """
    Main entry point for Twilio WhatsApp messages.
    - Body: The text the driver sent.
    - From: The driver's WhatsApp number.
    """
    try:
        # 1. Process the travel request (LLM + Google Maps + Rail API)
        # This function should return a dict with: origin, dest, price, summary
        plan_data = get_best_route(Body)
        
        # 2. Log the data to DynamoDB for Friday's report
        log_expense(
            driver_phone=From,
            origin=plan_data.get('origin', 'Unknown'),
            destination=plan_data.get('dest', 'Unknown'),
            price=plan_data.get('price', '0.00')
        )
        
        # 3. Build the WhatsApp Response
        twiml_resp = MessagingResponse()
        twiml_resp.message(plan_data.get('summary', 'Processing your route...'))
        
        # Return as XML (Twilio requirement)
        return Response(content=str(twiml_resp), media_type="application/xml")

    except Exception as e:
        # Emergency catch-all for the driver
        error_resp = MessagingResponse()
        error_resp.message("Sorry, I hit a snag planning that route. I've logged the error.")
        print(f"CRITICAL ERROR: {str(e)}") # This goes to CloudWatch
        return Response(content=str(error_resp), media_type="application/xml")

# This is what AWS Lambda calls. 
# Matches the 'Handler' setting: app.main.handler
handler = Mangum(app, lifespan="off")

@app.get("/test")
def test_path():
    return {"message": "API is alive!"}