import os
import boto3
from datetime import datetime
from openai import OpenAI
from app.prompt import SYSTEM_PROMPT

# 1. Setup Clients
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('ResponseAbleExpenses')

def get_best_route(user_input: str):
    """
    Combines AI reasoning with travel data.
    """
    # 2. Ask the AI to plan the route based on your prompt.py instructions
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ]
    )
    
    ai_summary = response.choices[0].message.content

    # 3. For the MVP, we'll assume a fixed price 
    # (You can swap this for the TransportAPI function later tonight)
    estimated_price = "24.50" 
    
    # 4. Extract basic info for the database (Simplified for Day 1)
    # We'll treat the whole summary as the 'plan'
    return {
        "origin": "Extracted via AI",
        "dest": "Extracted via AI",
        "price": estimated_price,
        "summary": ai_summary
    }

def log_expense(driver_phone, origin, destination, price):
    """
    Saves the data to DynamoDB for your Friday report.
    """
    try:
        table.put_item(
            Item={
                'driver_id': driver_phone,
                'timestamp': datetime.utcnow().isoformat(),
                'origin': origin,
                'destination': destination,
                'price': str(price)
            }
        )
    except Exception as e:
        print(f"DB Error: {e}")