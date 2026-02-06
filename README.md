# Interview Memory Engine

A personalized interview preparation application focused on **data engineering roles**. The app helps you store interview transcripts, receive AI feedback, organize questions by topic/tags, and practice with quiz/flashcard workflows.

## Features

- **Interview Transcript Management**
  - Upload transcript text directly.
  - Upload an audio recording (`.wav`, `.mp3`, `.m4a`, `.mp4`) and automatically transcribe it when OpenAI is configured.
  - Persist all transcripts in SQLite.
- **ChatGPT Integration**
  - Analyze transcripts for strengths/weaknesses.
  - Extract likely interview questions and suggested topics.
- **Question Categorization and Tagging**
  - Store extracted/manual questions with categories (`SQL`, `Python`, `Data Modeling`, `Behavioral`, etc.).
  - Add tags for retrieval and grouping.
- **Practice and Quiz Mode**
  - Pull random questions from saved question bank.
  - Submit quiz attempts and keep score history.
- **Progress Tracking and Analytics**
  - Track attempts over time.
  - Surface strengths and weak areas by category.

## Tech Stack

- **Backend:** Python + Flask
- **Frontend:** HTML/CSS/vanilla JS (single-page style)
- **Database:** SQLite
- **AI Integration:** OpenAI API (chat + transcription)

## Project Structure

- `app.py` – Flask application, REST API, and route rendering.
- `db.py` – SQLite initialization and data access helpers.
- `ai_service.py` – OpenAI transcript analysis + transcription integration.
- `templates/index.html` – Main UI.
- `static/app.js` – Frontend behavior and API calls.
- `static/styles.css` – Styling.
- `uploads/` – Stored recording files (created at runtime).

## Quick Start

1. Create and activate a Python virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set optional environment variables:

   ```bash
   export OPENAI_API_KEY="your_key_here"
   export FLASK_SECRET_KEY="replace_me"
   export IME_DB_PATH="interview_memory.db"
   ```

4. Run the app:

   ```bash
   python app.py
   ```

5. Open http://localhost:5000.

## API Overview

- `POST /api/transcripts`
  - Multipart form with either `transcript_text` or `recording` (+ optional `title`).
- `GET /api/transcripts`
  - List stored transcripts.
- `POST /api/transcripts/<id>/analyze`
  - Uses ChatGPT to generate feedback and extract questions.
- `GET /api/questions`
  - List questions (`?category=` optional filter).
- `POST /api/questions`
  - Create question manually.
- `GET /api/quiz?limit=5`
  - Randomized practice questions.
- `POST /api/quiz-attempts`
  - Save quiz results.
- `GET /api/analytics`
  - Progress summary and weak categories.

## Security and Privacy Notes

- SQLite database and uploaded recordings stay local to your deployment.
- Keep `OPENAI_API_KEY` in environment variables and never hard-code secrets.
- Add authentication and role-based access before multi-user deployment.
- For production: run behind HTTPS + encrypted storage at rest.

## Future Enhancements

- User authentication and profile-specific data isolation.
- SSO integration for team use.
- Better spaced-repetition logic for flashcards.
- Dashboard visualizations (charts for trend lines).
- Scheduled mock interview sessions with reminders.
