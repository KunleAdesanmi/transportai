import os
from datetime import datetime


# Initialize clients inside the file but outside the function
# Ensure these environment variables are set in AWS Lambda


def get_best_route(user_text):
    import googlemaps
    from openai import OpenAI
    gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_KEY"))
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        # --- STEP 1: AI EXTRACTION ---
        # We force the AI to identify the start and end strictly.
        extraction_prompt = f"""
        Identify the travel 'Origin' and 'Destination' from the following text: "{user_text}"
        Rules:
        - "Dropped at", "Starting from", or "I am at" = ORIGIN.
        - "Going to", "Heading to", or "Destination" = DESTINATION.
        - If the user says they are AT a location, that is the START.
        - Output ONLY as: ORIGIN|DESTINATION
        """
        
        extract_res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are a logistics parser."},
                      {"role": "user", "content": extraction_prompt}]
        )
        
        raw_extract = extract_res.choices[0].message.content.strip()
        if "|" not in raw_extract:
            return {"summary": "I couldn't clearly identify your start and end point. Please try: 'From [Postcode] to [Postcode]'"}
            
        origin, dest = raw_extract.split("|")

        # --- STEP 2: GOOGLE MAPS DIRECTIONS ---
        now = datetime.now()
        directions_result = gmaps.directions(
            origin,
            dest,
            mode="transit",
            departure_time=now
        )

        if not directions_result:
            return {"summary": f"I found the locations ({origin} to {dest}), but Google couldn't find a public transport route. It might be walking distance or not served by transit right now."}

        # --- STEP 3: DATA PARSING ---
        leg = directions_result[0]['legs'][0]
        arrival_time = leg.get('arrival_time', {}).get('text', 'N/A')
        total_duration = leg.get('duration', {}).get('text', 'N/A')
        
        steps_list = []
        for step in leg.get('steps', []):
            # Clean up HTML tags like <b> from Google instructions
            instr = step.get('html_instructions', 'Proceed').replace('<b>', '').replace('</b>', '').replace('<div style="font-size:0.9em">', ' - ').replace('</div>', '')
            duration = step.get('duration', {}).get('text', '')
            
            # Check for transit-specific info (Bus/Train)
            transit = step.get('transit_details')
            if transit:
                line = transit.get('line', {}).get('short_name', 'Transit')
                dept_stop = transit.get('departure_stop', {}).get('name', 'stop')
                dept_time = transit.get('departure_time', {}).get('text', 'scheduled time')
                instr = f"🚌 Take {line} from {dept_stop} at {dept_time}"
            
            steps_list.append(f"{instr} ({duration})")

        # --- STEP 4: FINAL AI FORMATTING ---
        # We give the AI the REAL steps so it doesn't have to hallucinate.
        summary_prompt = f"""
        Format this travel plan into a friendly WhatsApp message for a driver.
        Origin: {origin}
        Destination: {dest}
        Total Duration: {total_duration}
        Arrive By: {arrival_time}
        Steps:
        {chr(10).join(steps_list)}

        Use emojis, bold text, and keep it concise. Include a 'Driver Tip' based on the destination.
        """

        final_res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": summary_prompt}]
        )
        
        summary = final_res.choices[0].message.content.strip()

        return {
            "origin": origin,
            "dest": dest,
            "summary": summary,
            "price": "£2-£6" # Default estimate for UK local transit
        }

    except Exception as e:
        print(f"ERROR IN TRAVEL LOGIC: {str(e)}")
        return {"summary": f"❌ Sorry, I hit a snag: {str(e)}"}