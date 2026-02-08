from fastapi import FastAPI, Form, Response
from mangum import Mangum

app = FastAPI()

@app.post("/")
async def debug_webhook(Body: str = Form(None)):
    # This uses almost ZERO memory
    xml_response = f"<Response><Message>Echo: {Body}</Message></Response>"
    return Response(content=xml_response, media_type="application/xml")

handler = Mangum(app)