import os
import googlemaps
from datetime import datetime
from openai import OpenAI

# Clients
gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_best_route(user_text):
    # STEP 1: Strict Extraction with AI
    extraction_prompt = f"""
    You are a logistics assistant. Extract the Origin and Destination from this text: "{user_text}"
    Rules:
    - If the user says "dropped at", "starting from", or "I am at", that is the ORIGIN.
    - If the user says "going to", "head to", or "to", that is the DESTINATION.
    - Output ONLY in this format: ORIGIN|DESTINATION
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": extraction_prompt}]
    )
    extracted = response.choices[0].message.content.strip()
    origin, dest = extracted.split("|")

    # STEP 2: Get Technical Step-by-Step from Google
    now = datetime.now()
    directions_result = gmaps.directions(
        origin,
        dest,
        mode="transit",
        departure_time=now
    )

    if not directions_result:
        return {"summary": "I couldn't find a transit route for that journey. Is the postcode correct?"}

    # Extract the technical data to give to the AI
    leg = directions_result[0]['legs'][0]
    raw_steps = []
    for step in leg['steps']:
        instr = step.get('html_instructions', 'Walk')
        duration = step['duration']['text']
        # If it's a bus/train, get the specific details
        transit = step.get('transit_details')
        if transit:
            line = transit['line']['short_name']
            dept_stop = transit['departure_stop']['name']
            dept_time = transit['departure_time']['text']
            instr = f"Take {line} from {dept_stop} at {dept_time}"
        raw_steps.append(f"{instr} ({duration})")

    # STEP 3: Final Formatting for WhatsApp
    summary_prompt = f"""
    Convert these technical directions into a friendly, professional WhatsApp message for a driver.
    Origin: {origin}
    Destination: {dest}
    Arrival Time: {leg['arrival_time']['text']}
    Steps: {", ".join(raw_steps)}

    Format like this:
    📍 *Route to {dest}*
    🏁 Arrive by: {leg['arrival_time']['text']}
    
    *Steps:*
    - [Formatted Step 1]
    - [Formatted Step 2]
    
    💰 Estimated Fare: [Guess based on UK prices]
    💡 Driver Tip: [One quick tip about the destination area]
    """

    final_summary = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": summary_prompt}]
    )

    return {
        "origin": origin,
        "dest": dest,
        "price": "£5-£10", # You can parse this from Google's 'fare' if available
        "summary": final_summary.choices[0].message.content.strip()
    }