import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

import db
from ai_service import AIService

load_dotenv()

UPLOAD_DIR = Path("uploads")
ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".mp4"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024

UPLOAD_DIR.mkdir(exist_ok=True)
db.init_db()
ai_service = AIService()


@app.get("/")
def index():
    return render_template("index.html", ai_enabled=ai_service.enabled)


@app.get("/api/transcripts")
def list_transcripts():
    return jsonify(db.list_transcripts())


@app.post("/api/transcripts")
def create_transcript():
    title = request.form.get("title")
    transcript_text = (request.form.get("transcript_text") or "").strip()
    recording = request.files.get("recording")

    source_type = "text"
    source_path = None

    if recording and recording.filename:
        filename = secure_filename(recording.filename)
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_AUDIO_EXTENSIONS:
            return jsonify({"error": f"Unsupported file type: {ext}"}), 400

        output_path = UPLOAD_DIR / filename
        recording.save(output_path)
        source_type = "audio"
        source_path = str(output_path)

        if not transcript_text:
            try:
                transcript_text = ai_service.transcribe_audio(str(output_path))
            except RuntimeError as exc:
                return jsonify({"error": str(exc)}), 400

    if not transcript_text:
        return jsonify({"error": "Provide transcript_text or upload recording."}), 400

    transcript_id = db.insert_transcript(title, source_type, source_path, transcript_text)
    return jsonify({"id": transcript_id, "transcript_text": transcript_text}), 201


@app.post("/api/transcripts/<int:transcript_id>/analyze")
def analyze_transcript(transcript_id: int):
    transcript = db.get_transcript(transcript_id)
    if not transcript:
        return jsonify({"error": "Transcript not found"}), 404

    analysis = ai_service.analyze_transcript(transcript["transcript_text"])
    db.insert_feedback(
        transcript_id=transcript_id,
        summary=analysis["summary"],
        strengths=analysis.get("strengths", []),
        weaknesses=analysis.get("weaknesses", []),
    )

    created_ids = []
    for q in analysis.get("questions", []):
        question_text = (q.get("question_text") or "").strip()
        if not question_text:
            continue
        category = q.get("category") or "General"
        tags = q.get("tags") or []
        difficulty = q.get("difficulty") or "medium"
        created_ids.append(
            db.add_question(
                transcript_id=transcript_id,
                question_text=question_text,
                category=category,
                tags=tags,
                difficulty=difficulty,
            )
        )

    return jsonify({"analysis": analysis, "created_questions": created_ids})


@app.get("/api/questions")
def list_questions():
    category = request.args.get("category")
    return jsonify(db.list_questions(category=category))


@app.post("/api/questions")
def create_question():
    payload = request.get_json(force=True)
    question_text = (payload.get("question_text") or "").strip()
    category = (payload.get("category") or "General").strip()
    tags = payload.get("tags") or []
    difficulty = (payload.get("difficulty") or "medium").strip()

    if not question_text:
        return jsonify({"error": "question_text is required"}), 400

    question_id = db.add_question(
        question_text=question_text,
        category=category,
        tags=tags,
        difficulty=difficulty,
    )
    return jsonify({"id": question_id}), 201


@app.get("/api/quiz")
def get_quiz():
    limit = int(request.args.get("limit", 5))
    limit = max(1, min(limit, 20))
    return jsonify(db.random_quiz_questions(limit=limit))


@app.post("/api/quiz-attempts")
def save_quiz_attempt():
    payload = request.get_json(force=True)
    total_questions = int(payload.get("total_questions", 0))
    correct_answers = int(payload.get("correct_answers", 0))

    if total_questions <= 0 or correct_answers < 0 or correct_answers > total_questions:
        return jsonify({"error": "Invalid quiz attempt payload"}), 400

    attempt_id = db.save_quiz_attempt(total_questions=total_questions, correct_answers=correct_answers)
    return jsonify({"id": attempt_id}), 201


@app.get("/api/analytics")
def analytics():
    return jsonify(db.analytics_snapshot())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
