from openai import OpenAI
import base64
from API import *
client = OpenAI(
    api_key=api_key,
    base_url="https://api.proxyapi.ru/openai/v1",
)

prompt = """
Стеклянная бутылка, внутри которой плывет корабль посреди шторма
"""

result = client.images.generate(
    model="gpt-image-1-mini",
    prompt=prompt
)

image_base64 = result.data[0].b64_json
image_bytes = base64.b64decode(image_base64)

with open("image1.png", "wb") as f:
    f.write(image_bytes)