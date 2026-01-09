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
