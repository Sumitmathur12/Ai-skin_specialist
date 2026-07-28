import anthropic
from dotenv import load_dotenv
import os
import base64
load_dotenv()
api_key = os.environ.get("MINIMAX_API_KEY")
base_url = "https://api.minimax.io/anthropic"

client = anthropic.Anthropic(api_key=api_key, base_url=base_url)


messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "Hello , what can you help me with?",       
            }
        ]
    }
]

video_path = os.path.join(folder, "test-video.mp4")
with open(video_path, "rb") as file:
    video_data = base64.b64encode(file.read()).decode("utf-8")

video_messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "video",
                "source": {
                    "type": "base64",
                    "media_type": "video/mp4",
                    "data": video_data,
                },
            },
            {
                "type": "text",
                "text": "What is happening in this video?",
            },
        ],
    }
]


folder =os.path.dirname((__file__))
image_path = os.path.join(folder, "Sample_page.png")




with open(image_path , "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "image",
                "source":{
                    "type": "base64",
                    "media_type": "image/png",
                    "data": image_data
                }
            }
        ]
    }
]

response = client.messages.create(
    model="MiniMax-M3",
    messages=messages,
    max_tokens=1000,
)

print(response)