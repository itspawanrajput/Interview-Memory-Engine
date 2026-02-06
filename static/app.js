const transcriptForm = document.getElementById('transcript-form');
const questionForm = document.getElementById('question-form');
const transcriptsEl = document.getElementById('transcripts');
const questionsEl = document.getElementById('questions');
const quizEl = document.getElementById('quiz');
const analyticsEl = document.getElementById('analytics');
const startQuizBtn = document.getElementById('start-quiz');
const submitQuizBtn = document.getElementById('submit-quiz');
const refreshAnalyticsBtn = document.getElementById('refresh-analytics');

let currentQuiz = [];

const escapeHtml = (value) =>
  String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');

async function loadTranscripts() {
  const res = await fetch('/api/transcripts');
  const data = await res.json();
  if (!data.length) {
    transcriptsEl.innerHTML = '<p>No transcripts yet.</p>';
    return;
  }

  transcriptsEl.innerHTML = data
    .map(
      (item) => `
      <div class="item">
        <strong>${escapeHtml(item.title || 'Untitled transcript')}</strong>
        <p>${escapeHtml(item.transcript_text.slice(0, 200))}...</p>
        <button onclick="analyzeTranscript(${item.id})">Analyze With AI</button>
      </div>
    `,
    )
    .join('');
}

async function loadQuestions() {
  const res = await fetch('/api/questions');
  const data = await res.json();
  if (!data.length) {
    questionsEl.innerHTML = '<p>No questions yet.</p>';
    return;
  }

  questionsEl.innerHTML = data
    .map(
      (q) => `
      <div class="item">
        <strong>${escapeHtml(q.question_text)}</strong>
        <div>Category: ${escapeHtml(q.category)} | Difficulty: ${escapeHtml(q.difficulty)}</div>
        <div>Tags: ${escapeHtml((q.tags || []).join(', '))}</div>
      </div>
    `,
    )
    .join('');
}

window.analyzeTranscript = async function analyzeTranscript(id) {
  const res = await fetch(`/api/transcripts/${id}/analyze`, { method: 'POST' });
  const data = await res.json();
  if (!res.ok) {
    alert(data.error || 'Failed to analyze transcript');
    return;
  }
  alert(`Analysis complete. Added ${data.created_questions.length} questions.`);
  await loadQuestions();
};

transcriptForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const formData = new FormData(transcriptForm);
  const res = await fetch('/api/transcripts', {
    method: 'POST',
    body: formData,
  });
  const data = await res.json();
  if (!res.ok) {
    alert(data.error || 'Failed to save transcript');
    return;
  }
  transcriptForm.reset();
  await loadTranscripts();
});

questionForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const formData = new FormData(questionForm);
  const payload = {
    question_text: formData.get('question_text'),
    category: formData.get('category'),
    tags: String(formData.get('tags') || '')
      .split(',')
      .map((x) => x.trim())
      .filter(Boolean),
    difficulty: formData.get('difficulty'),
  };

  const res = await fetch('/api/questions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) {
    alert(data.error || 'Failed to save question');
    return;
  }

  questionForm.reset();
  await loadQuestions();
});

startQuizBtn.addEventListener('click', async () => {
  const res = await fetch('/api/quiz?limit=5');
  const data = await res.json();
  currentQuiz = data;

  if (!data.length) {
    quizEl.innerHTML = '<p>Add questions before starting quiz mode.</p>';
    submitQuizBtn.disabled = true;
    return;
  }

  quizEl.innerHTML = data
    .map(
      (q, idx) => `
      <div class="item">
        <strong>Q${idx + 1}.</strong> ${escapeHtml(q.question_text)}
        <label>Mark as correct?
          <input type="checkbox" data-quiz-correct="${idx}" />
        </label>
      </div>
    `,
    )
    .join('');
  submitQuizBtn.disabled = false;
});

submitQuizBtn.addEventListener('click', async () => {
  const checks = [...document.querySelectorAll('[data-quiz-correct]')];
  const correctAnswers = checks.filter((x) => x.checked).length;
  const payload = {
    total_questions: currentQuiz.length,
    correct_answers: correctAnswers,
  };

  const res = await fetch('/api/quiz-attempts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const data = await res.json();
  if (!res.ok) {
    alert(data.error || 'Failed to save quiz attempt');
    return;
  }

  alert(`Saved attempt ${data.id}. Score: ${correctAnswers}/${currentQuiz.length}`);
  await loadAnalytics();
});

async function loadAnalytics() {
  const res = await fetch('/api/analytics');
  const data = await res.json();
  analyticsEl.textContent = JSON.stringify(data, null, 2);
}

refreshAnalyticsBtn.addEventListener('click', loadAnalytics);

Promise.all([loadTranscripts(), loadQuestions(), loadAnalytics()]);
