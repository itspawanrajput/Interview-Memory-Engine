import json
import os
from typing import Any

from openai import OpenAI


class AIService:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    @property
    def enabled(self) -> bool:
        return self.client is not None

    def transcribe_audio(self, file_path: str) -> str:
        if not self.client:
            raise RuntimeError("OpenAI is not configured. Set OPENAI_API_KEY.")

        with open(file_path, "rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio_file,
            )
        return transcript.text

    def analyze_transcript(self, transcript_text: str) -> dict[str, Any]:
        if not self.client:
            return {
                "summary": "OpenAI is not configured. Analysis unavailable.",
                "strengths": [],
                "weaknesses": ["Configure OPENAI_API_KEY to enable transcript feedback."],
                "questions": [],
            }

        prompt = (
            "You are an interview coach for data engineering candidates. "
            "Analyze the following transcript and return strict JSON with keys: "
            "summary (string), strengths (string[]), weaknesses (string[]), questions (object[]). "
            "Each questions item should contain question_text, category, tags (string[]), difficulty."
        )

        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": transcript_text[:14000]},
            ],
        )

        content = completion.choices[0].message.content or "{}"
        data = json.loads(content)
        data.setdefault("summary", "No summary returned")
        data.setdefault("strengths", [])
        data.setdefault("weaknesses", [])
        data.setdefault("questions", [])
        return data
