# AI Interviewer

An AI-powered interview application built with Django and Claude API. The system conducts adaptive interviews on any topic, adjusting question complexity based on the candidate's experience level.

## Features

- Adaptive AI-generated questions (3-5) based on topic and experience level
- Junior / Mid-Level / Senior difficulty modes
- Real-time interview flow with context-aware follow-up questions
- AI-generated summary, sentiment analysis and keyword extraction
- Interview history with past transcripts
- PDF export of full interview transcript
- Simple authentication system

## Tech Stack

- **Backend:** Python 3.13 + Django 6
- **AI:** Anthropic Claude Sonnet (claude-sonnet-4-6)
- **Frontend:** HTML + Tailwind CSS
- **Database:** SQLite
- **PDF Generation:** ReportLab
- **Deployment:** Docker + Portainer + Cloudflare Tunnel

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False

# Anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# App Authentication
APP_USERNAME=your-username
APP_PASSWORD=your-password

# Database (optional, defaults to db.sqlite3 in project root)
DB_PATH=/app/data/db.sqlite3
```

### How to get the values:

| Variable | How to get it |
|---|---|
| `SECRET_KEY` | Generate at [djecrety.ir](https://djecrety.ir) |
| `ANTHROPIC_API_KEY` | Get from [console.anthropic.com](https://console.anthropic.com) |
| `APP_USERNAME` | Choose any username |
| `APP_PASSWORD` | Choose a strong password |

## Local Development

### Prerequisites
- Python 3.13+
- Git

### Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/ai-interviewer.git
cd ai-interviewer
```

2. Create and activate virtual environment:
```bash
python -m venv venv --without-pip
source venv/Scripts/activate  # Windows
source venv/bin/activate       # Linux/Mac
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python get-pip.py
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file with your variables (see above)

5. Run migrations:
```bash
python manage.py migrate
```

6. Create admin user:
```bash
python manage.py createsuperuser
```

7. Start the server:
```bash
python manage.py runserver
```

8. Open [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Docker Deployment

### Using Docker Compose

1. Clone the repository on your server
2. Create `.env` file with your variables
3. Build and run:
```bash
docker-compose up -d
```

### Using Portainer

1. In Portainer, go to **Stacks → Add Stack**
2. Paste the contents of `docker-compose.yml`
3. Add your environment variables
4. Click **Deploy the stack**

## How It Works

1. User selects a topic and experience level (Junior / Mid / Senior)
2. Claude generates the first question adapted to the level
3. After each answer, Claude receives the full conversation history and decides whether to continue or end the interview
4. At the end, Claude generates a summary, sentiment score and keywords
5. Full transcript is saved to the database and can be exported as PDF
