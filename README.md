# AI Coach

A lightweight Python toolkit for generating skill gap analyses, personalized learning plans, and interview practice feedback for candidates. It uses a simple skill taxonomy to map match explanations to actionable steps, recommend courses/projects/readings, and surface dashboard reminders.

## Features
- Generate gap analyses from match explanations and convert them into actionable plans (quick wins, medium-term upskilling, interview prep).
- Provide recommended courses/projects/readings tied to the skill taxonomy and track completion status.
- Behavioral and functional interview practice modules with rubric-based evaluation and structured feedback.
- Progress view for dashboards with reminders/notifications to keep candidates on track.

## Running the demo
```bash
pip install -e .
python -m ai_coach.main
```
The demo prints:
- Gap analysis with quick-win, medium-term, and interview-prep items.
- Recommended resources with completion status.
- Behavioral and functional practice evaluations with rubric-aligned feedback.
- Dashboard summary including completion rate, trends, and reminders.

## Project layout
- `src/ai_coach/data/skill_taxonomy.json` – Skill taxonomy with resources.
- `src/ai_coach/` – Core modules for gap analysis, recommendations, practice evaluation, and dashboard utilities.
