

Campus Connect AI (CAI) 🚀

Your AI-powered assistant for seamless campus navigation and support!

📌 Overview

Campus Connect AI (CAI) is an intelligent assistant designed to streamline faculty-student interactions, simplify campus-related queries, and provide instant access to essential academic and administrative resources.

✨ Features

🔹 AI-Powered Query System
	•	Ask campus-related questions and get instant AI responses.
	•	Trained on university-specific data to provide accurate and contextual answers.
	•	Supports text-based and voice-based interactions.

📢 Announcements & Notifications
	•	View official university updates and faculty announcements.
	•	Get real-time notifications for deadlines, exams, and events.

📚 Course & Assignment Assistance
	•	Get information on courses, syllabus, and study materials.
	•	View upcoming assignments, deadlines, and faculty feedback.
	•	AI-generated study tips based on previous student interactions.

📅 Calendar & Timetable Management
	•	View your class schedule and faculty availability.
	•	AI can suggest optimal study slots based on workload.
	•	Sync with Google Calendar for reminders.

🔬 Research & Faculty Directory (ProfConnect)
	•	Find professors based on department, research area, and availability.
	•	Request meetings or research collaborations.
	•	Get faculty office hours and contact details.

📊 Analytics Dashboard
	•	Track academic progress and engagement statistics.
	•	Get personalized insights on performance and improvement areas.

## Automated project health

CAI records a daily, offline project-health snapshot in [`reports/project-health.md`](reports/project-health.md). The scheduled workflow compiles the backend, inventories Flask and API routes, checks dependency hygiene, and appends the results to a CSV history. It intentionally does not call the hosted AI, Firebase, or OAuth services: those require credentials or a locally running Ollama model and would make CI results unreliable.

🌗 Dark Mode Support
	•	Switch between Light Mode and Dark Mode for a better user experience.

🚀 Future Enhancements
	•	Enhanced AI Model: Improve accuracy with more training data.
	•	Multilingual Support: Expand accessibility with multiple language options.
	•	Integration with University Systems: Seamless login via student/faculty portals.
	•	Mobile App Version: Native Android/iOS support for on-the-go access.
