# 📧 AI Email Intelligence System

> **"Turning Inbox Noise into Actionable Insights."**

This project is an automated AI assistant designed to declutter your email inbox. It uses **Google's Gemini AI** to read, categorize, and summarize emails, delivering only the most critical information (Tasks, Benefits, Urgent Alerts) directly to your messaging app (**LINE**) every morning. It also features an interactive chatbot to query your email history.

---

## 🚀 Key Features

### 1. 🤖 AI-Powered Analysis
Instead of simple keyword filtering, this system uses **Generative AI (Gemini 2.5 Flash)** to understand the *context* of emails.
* **Categories:** Classifies emails into `URGENT`, `BENEFIT` (Opportunities/Rewards), `TASK` (Assignments/Deadlines), or `NOISE` (General announcements).
* **Summarization:** Condenses long emails into 1-sentence summaries.
* **Extraction:** Automatically extracts Deadline Dates and Action Items.

### 2. 🌅 Automated Daily Briefing
* Runs automatically every morning via **GitHub Actions**.
* Fetches emails from the last 24 hours.
* Sends a neat, batched summary to LINE.
* **Smart Notification:** Prioritizes "Urgent" emails and groups "Benefits/Tasks" into a digestible list.

### 3. 💬 Interactive Chatbot
* A 24/7 server (hosted on PythonAnywhere/Render) that listens to your commands.
* **Ask the bot:**
    * *"Any tasks due soon?"*
    * *"Show me recent opportunities."*
    * *"Is there any urgent news?"*
* Retrieves data from the last 14 days to keep info relevant.

---

## 🏗️ Architecture

The system operates on a **Hybrid Architecture**:

1.  **The "Worker" (Batch Processing):**
    * Hosted on **GitHub Actions**.
    * Runs on a Schedule (Cron).
    * **Flow:** IMAP Fetch $\rightarrow$ AI Processing $\rightarrow$ Save to Database $\rightarrow$ Push Notification.

2.  **The "Server" (Real-time Interaction):**
    * Hosted on a Cloud Server (e.g., PythonAnywhere).
    * Connects to the same Database.
    * Responds to user chats via Webhooks.

---

## 🛠️ Tech Stack

* **Language:** Python 3.10
* **AI Engine:** Google Gemini (Generative AI)
* **Database:** Supabase (PostgreSQL)
* **Messaging:** LINE Messaging API
* **Automation:** GitHub Actions
* **Server Framework:** Flask

---

## ⚙️ Setup & Installation

### 1. Prerequisites
* Python 3.10+
* A Gmail account (with App Password enabled).
* A Supabase project (Free tier).
* A Google AI Studio API Key.
* A LINE Messaging API Channel.

### 2. Installation
Clone the repository:
```bash
git clone [https://github.com/your-username/ai-email-intelligence.git](https://github.com/your-username/ai-email-intelligence.git)
cd ai-email-intelligence
pip install -r requirements.txt
```
### 3. Configuration (.env)
Create a .env file in the root directory and add the following keys:
```
# Email Settings (IMAP)
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password

# Database (Supabase)
SUPABASE_URL=[https://your-project.supabase.co](https://your-project.supabase.co)
SUPABASE_KEY=your_service_role_key

# AI (Google Gemini)
GEMINI_API_KEY=your_gemini_api_key

# LINE Messaging API
LINE_CHANNEL_ACCESS_TOKEN=your_line_token
LINE_CHANNEL_SECRET=your_line_secret
LINE_USER_ID=your_user_id
```
### 4. Database Schema
Run this SQL query in your Supabase SQL Editor to create the necessary table:
```
CREATE TABLE emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_uid VARCHAR(255) UNIQUE NOT NULL,
    sender TEXT,
    subject TEXT,
    body TEXT,
    received_at TIMESTAMP WITH TIME ZONE,
    
    -- AI Analysis Result
    category VARCHAR(50),      -- 'URGENT', 'BENEFIT', 'TASK', 'NOISE'
    summary_text TEXT,
    action_items JSONB,
    deadline_date DATE,
    priority_score INTEGER,
    
    -- System Status
    is_notified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🏃‍♂️ Usage

### Option A: Running Locally (Testing)
To test the AI processing pipeline manually:
```
python ingest.py   # Step 1: Fetch emails
python process.py  # Step 2: Analyze with AI
python notify.py   # Step 3: Send report to LINE
```
To run the Chatbot server locally:
```
python app.py
```

### Option B: Deploying (Production)
1.  **Daily Automation:** Push code to GitHub. The workflow file in `.github/workflows/daily_run.yml` handles the scheduling. **Important:** Add your `.env` variables to **GitHub Secrets**.
2.  **Chatbot:** Deploy `app.py` to a hosting provider (like PythonAnywhere or Render) and set up the Webhook URL in the LINE Developer Console.

---

## 🛡️ Privacy Note

This project is designed for **personal use**. It processes email contents using an external AI provider (Google Gemini). Ensure you review the data privacy policies of the APIs used if dealing with highly sensitive information.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).




