import os
import json
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv
import time
import logging

load_dotenv()
logger = logging.getLogger(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-3.5-flash"

EXTRACTION_PROMPT = """
You are reading an ID document — this could be an Indian domestic ID (Aadhaar, PAN, Voter ID, Driving License) or a Passport.

First, identify the document type. Then extract fields according to these rules:

FOR DOMESTIC IDs (Aadhaar, PAN, Voter ID, Driving License):
- full_name: the person's full name exactly as printed. If unreadable, null.
- given_name: always null (not used for domestic IDs)
- surname: always null (not used for domestic IDs)
- id_number: the ID number printed on the card (Aadhaar number, PAN number, Voter ID number, License number). If unreadable, null.
- dob: date of birth exactly as printed. If unreadable, null.
- gender: "Male" or "Female" (normalize from M/F if abbreviated). If unreadable, null.
- issue_date: always null (not used for domestic IDs)
- expiry_date: always null (not used for domestic IDs)

FOR PASSPORT:
- full_name: always null (not used for passports)
- given_name: the given name(s) / first name(s) exactly as printed, separate from surname. If unreadable, null.
- surname: the surname / family name exactly as printed. If unreadable, null.
- id_number: the passport number. If unreadable, null.
- dob: date of birth exactly as printed. If unreadable, null.
- gender: "Male" or "Female" (normalize from M/F if abbreviated). If unreadable, null.
- issue_date: date of issue exactly as printed. If unreadable, null.
- expiry_date: date of expiry exactly as printed. If unreadable, null.

Always include this field regardless of document type:
- document_type: e.g. "Aadhaar", "PAN", "Voter ID", "Driving License", "Passport". If unclear, null.

Return ONLY valid JSON in this exact shape, no markdown, no explanation:

{
  "document_type": string or null,
  "full_name": string or null,
  "given_name": string or null,
  "surname": string or null,
  "id_number": string or null,
  "dob": string or null,
  "gender": "Male" or "Female" or null,
  "issue_date": string or null,
  "expiry_date": string or null
}

Do NOT guess or hallucinate any field. If unreadable or not applicable per the rules above, return null for that field. Return ONLY the JSON object.
"""


def _derive_title(gender: str | None) -> str | None:
    if gender is None:
        return None
    normalized = gender.strip().upper()
    if normalized in ("MALE", "M"):
        return "Mr"
    elif normalized in ("FEMALE", "F"):
        return "Ms"
    return None


def _call_gemini(file_bytes: bytes, mime_type: str) -> str:
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                EXTRACTION_PROMPT,
            ],
            config=types.GenerateContentConfig(
            response_mime_type="application/json",
            max_output_tokens=2048,
)
            ),
        

        return response.text.strip()

    except Exception as e:
        logger.exception("Gemini API request failed")
        raise RuntimeError("Gemini API request failed") from e


def extract_id_details(file_bytes: bytes, mime_type: str) -> dict:
    """
    Sends ID/passport file to Gemini, returns extracted fields.
    Handles both domestic ID format (full_name) and passport format (given_name/surname).
    """
    data = None

    for attempt in range(2):
        try:
            raw_text = _call_gemini(file_bytes, mime_type)
            match = re.search(r'\{.*?\}', raw_text, re.DOTALL)
            cleaned = match.group(0) if match else raw_text
            data = json.loads(cleaned)
            break

        except (json.JSONDecodeError, RuntimeError) as e:
            last_error = e
            if attempt == 0:
                time.sleep(1)
                continue
            raise ValueError("Gemini extraction failed after retry.") from e

    gender = data.get("gender")

    return {
        "document_type": data.get("document_type"),
        "full_name": data.get("full_name"),
        "given_name": data.get("given_name"),
        "surname": data.get("surname"),
        "id_number": data.get("id_number"),
        "dob": data.get("dob"),
        "gender": gender,
        "title": _derive_title(gender),
        "issue_date": data.get("issue_date"),
        "expiry_date": data.get("expiry_date"),
    }