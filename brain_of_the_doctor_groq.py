import base64
import os
import re
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq
from PIL import Image


load_dotenv()


def encode_image_for_groq(image_input):
    if isinstance(image_input, Image.Image):
        image = image_input
    elif isinstance(image_input, (str, Path)):
        image = Image.open(image_input)
    elif hasattr(image_input, "name"):
        image = Image.open(image_input.name)
    elif isinstance(image_input, dict) and "path" in image_input:
        image = Image.open(image_input["path"])
    else:
        image = Image.open(image_input)

    image.thumbnail((1024, 1024))

    buffer = BytesIO()
    image.convert("RGB").save(buffer, format="JPEG", quality=75)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def clean_text_for_speech(text):
    if not text:
        return ""

    # 1. Take text after </think> if present
    if "</think>" in text:
        text = text.split("</think>")[-1].strip()

    # 2. Strip unclosed <think> tag if present before drafts/paragraphs
    text = re.sub(r"^<think>.*?(?=(?:Draft\s*\d*|Based on|Hello|Hi|I recommend|It looks|To help|Managing|\n\n|$))", "", text, flags=re.DOTALL | re.IGNORECASE).strip()

    # 3. Remove review block (e.g. 4. Review against constraints...)
    text = re.sub(r"\d+\.\s*Review against constraints.*$", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"Review against constraints.*$", "", text, flags=re.DOTALL | re.IGNORECASE)

    # 4. If there are Drafts (Draft 1, Draft 2, Draft 3), pick the last draft's content!
    draft_matches = list(re.finditer(r"Draft\s*\d*[^:]*:\s*(.*?)(?=(?:Draft\s*\d*|\d+\.|$))", text, re.DOTALL | re.IGNORECASE))
    if draft_matches:
        text = draft_matches[-1].group(1).strip()

    # 5. Filter out any remaining metadata / checklist lines
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    clean_lines = []
    for line in lines:
        if re.search(r"^(<think>|Careful skin|General info|Confident|Reassurance|Constraint|Thinking|Thought|Analyze|\d+\.|\*|\-)", line, re.IGNORECASE):
            continue
        clean_lines.append(line)

    result = " ".join(clean_lines) if clean_lines else text

    # 6. Remove sentence count notes e.g. (3 sentences) and markdown symbols
    result = re.sub(r"\(\d+\s*sentences?\)", "", result, flags=re.IGNORECASE)
    result = re.sub(r"[*#`_]", "", result).strip()
    return result


def brain_of_the_doctor(patient_text, image_filepath=None, video_filepath=None):
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("Missing GROQ_API_KEY in .env or environment")
    groq_api_key = groq_api_key.strip()

    if not image_filepath:
        raise ValueError("Groq vision requires an image. Please upload a skin image.")

    # Groq vision does not accept video here. When main.py passes both image and
    # video, this uses the same image as the visual input and ignores the video.
    image_data = encode_image_for_groq(image_filepath)

    prompt = (
        "You are a confident, natural doctor specializing in skin care. Speak with the reassurance, clarity, and authority of a real doctor. "
        "Limit your entire response to two or three sentences maximum. "
        "If the patient has provided a video, explain that you are reviewing the uploaded image because this model cannot process video directly. "
        "CRITICAL: Output ONLY the final plain text doctor response to the patient. Do NOT output any thinking steps, Draft 1/2/3, bullet points, checklists, or constraint reviews.\n\n"
        f"Patient text: {patient_text}"
    )

    if video_filepath:
        prompt += "\nThe patient also uploaded a video, but use the provided image as the visual reference."

    client = Groq(api_key=groq_api_key)
    model_name = os.environ.get("GROQ_MODEL", "qwen/qwen3.6-27b")
    response = client.chat.completions.create(
        model=model_name,
        max_completion_tokens=1000,
        messages=[
            {
                "role": "system",
                "content": "You are a careful skin care assistant. Give general information, not a diagnosis.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}",
                        },
                    },
                ],
            },
        ],
    )

    raw_content = response.choices[0].message.content or ""
    cleaned_content = clean_text_for_speech(raw_content)
    if not cleaned_content:
        cleaned_content = raw_content.replace("<think>", "").replace("</think>", "").strip()
    return cleaned_content[:1500]


# OLD CODE KEPT FOR REFERENCE
# import base64
# import os
# from io import BytesIO
#
# from dotenv import load_dotenv
# from groq import Groq
# from PIL import Image
#
#
# folder = os.path.dirname(__file__)
# env_path = os.path.join(folder, ".env")
# load_dotenv(env_path)
#
# api_key = os.environ.get("GROQ_API_KEY")
# if not api_key:
#     raise ValueError("Missing GROQ_API_KEY in .env or environment")
#
#
# image_path = os.path.join(folder, "sample-image.png")
#
# image = Image.open(image_path)
# image.thumbnail((1024, 1024))
#
# buffer = BytesIO()
# image.convert("RGB").save(buffer, format="JPEG", quality=75)
# image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
#
# client = Groq(api_key=api_key)
#
# response = client.chat.completions.create(
#     model=os.environ.get("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct"),
#     max_completion_tokens=1000,
#     messages=[
#         {
#             "role": "system",
#             "content": "You are a helpful medical assistant. Give general information, not a diagnosis.",
#         },
#         {
#             "role": "user",
#             "content": [
#                 {
#                     "type": "text",
#                     "text": "What do you see in this image? Give general skin care advice, not a diagnosis.",
#                 },
#                 {
#                     "type": "image_url",
#                     "image_url": {
#                         "url": f"data:image/jpeg;base64,{image_data}",
#                     },
#                 },
#             ],
#         },
#     ],
# )
#
# print(response.choices[0].message.content)