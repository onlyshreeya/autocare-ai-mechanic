
# AutoCare AI Mechanic

### Your AI-powered assistant for smarter car care.

AutoCare AI Mechanic is an AI-powered automotive assistance platform designed to help users understand vehicle issues, explore possible causes, and manage service bookings — all in one place.

Powered by AI, the application provides an interactive chat experience, vehicle diagnosis support, and a booking system through a modern web interface.

**Live Demo:** [AutoCare AI Mechanic](https://autocare-ai-mechanic.vercel.app)

**GitHub Repository:** [onlyshreeya/autocare-ai-mechanic](https://github.com/onlyshreeya/autocare-ai-mechanic)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Live Demo](#live-demo)
- [Tech Stack](#tech-stack)
- [System Architecture](#system-architecture)
- [Application Modules](#application-modules)
- [API Overview](#api-overview)
- [Getting Started](#getting-started)
- [Environment Configuration](#environment-configuration)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [Future Improvements](#future-improvements)
- [Author](#author)

---

## Overview

Car troubles can be confusing, especially when users don't know what might be causing an issue or what to do next.

AutoCare AI Mechanic aims to make automotive assistance more accessible through an AI-powered platform that helps users:

- Ask questions about vehicle problems.
- Explore potential causes of common car issues.
- Get AI-assisted diagnostic guidance.
- Create and manage service bookings.

The project combines a React-based frontend, a Django REST API, and Google's Gemini AI to deliver an interactive automotive assistance experience.

> AutoCare AI provides informational guidance and is not a substitute for a qualified mechanic or professional vehicle inspection.

---

## Features

### AI-Powered Chat Assistant
- Interactive chat for automotive questions.
- AI-generated responses to vehicle-related queries.
- Chat history support through the backend API.

### Vehicle Diagnosis
- Submit vehicle-related issues for AI-assisted diagnosis.
- Receive diagnostic information to help understand potential problems.
- Access diagnosis records through the application.

### Service Booking System
- Create service bookings through the application.
- Submit booking information to the backend.
- Retrieve booking records through the API.

### Full-Stack Integration
- React frontend connected to a Django REST backend.
- API-driven communication between frontend and backend.
- Deployed frontend and backend infrastructure.

---

## Live Demo

Try the deployed application:

### [Launch AutoCare AI Mechanic](https://autocare-ai-mechanic.vercel.app)

The live application includes chat, diagnosis, and booking functionality.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React |
| Frontend Tooling | Vite |
| Backend | Python, Django |
| API | Django REST Framework |
| AI Integration | Google Gemini |
| Database | SQLite |
| Frontend Deployment | Vercel |
| Backend Hosting | AWS EC2 |
| HTTPS Tunnel | ngrok |

---

## System Architecture

```text
                 USER
                  |
                  v
        React + Vite Frontend
              (Vercel)
                  |
                  v
             HTTPS API
               ngrok
                  |
                  v
          Django REST API
              (AWS EC2)
                  |
          +-------+-------+
          |       |       |
          v       v       v
        Chat  Diagnosis  Booking
          |       |       |
          +-------+-------+
                  |
                  v
           SQLite Database

       Gemini AI powers AI features
```

The frontend communicates with the Django backend through API requests. The backend handles application logic, database operations, and AI-powered functionality.

---

## Application Modules

### 1. Chat API

Handles automotive conversations and AI-generated responses.

### 2. Diagnosis API

Processes vehicle diagnosis requests and provides diagnostic information.

### 3. Booking API

Handles service booking creation and retrieval.

---

## API Overview

The backend exposes REST API endpoints for the application's main features.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/chat/` | Retrieve chat history |
| POST | `/api/chat/` | Submit a chat message |
| GET | `/api/diagnosis/` | Retrieve diagnosis records |
| POST | `/api/diagnosis/` | Submit a diagnosis request |
| GET | `/api/bookings/` | Retrieve bookings |
| POST | `/api/bookings/` | Create a booking |

Additional booking detail and status endpoints are available in the backend.

---

## Getting Started

Follow these steps to run AutoCare AI Mechanic locally.

### Prerequisites

Make sure you have the following installed:

- Node.js and npm
- Python 3.12
- Git
- A Google Gemini API key

### 1. Clone the Repository

```bash
git clone https://github.com/onlyshreeya/autocare-ai-mechanic.git

cd autocare-ai-mechanic
```

### 2. Set Up the Backend

From the project root, create and activate a virtual environment.

**Windows:**

```bash
python -m venv .venv

.venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv .venv

source .venv/bin/activate
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Apply database migrations:

```bash
python manage.py migrate
```

Start the Django development server:

```bash
python manage.py runserver
```

The backend will be available at:

`http://127.0.0.1:8000`

### 3. Set Up the Frontend

Open a new terminal and navigate to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Create a `.env` file in the `frontend` directory:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start the frontend development server:

```bash
npm run dev
```

Open the local URL provided by Vite in your browser.

---

## Environment Configuration

The application requires environment-specific configuration for the frontend API URL and Gemini AI integration.

### Frontend

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | Base URL of the Django backend |

Example:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### Backend

Configure the Gemini API key using the environment variable expected by the backend's AI integration.

Keep API keys and other secrets out of source control. Never commit `.env` files, credentials, or private keys.

---

## Deployment

AutoCare AI Mechanic is deployed using the following infrastructure:

| Component | Platform |
|---|---|
| Frontend | Vercel |
| Backend | AWS EC2 |
| HTTPS Tunneling | ngrok |

The frontend is deployed on Vercel, while the Django backend runs on an AWS EC2 instance. ngrok provides an HTTPS endpoint for communication between the deployed frontend and backend.

The backend and ngrok are configured as systemd services to support automatic restarts.

**Deployment note:** The backend's public API endpoint depends on the configured ngrok tunnel. Availability may be affected by tunnel configuration, service health, or hosting availability.

---

## Project Structure

```text
autocare-ai-mechanic/
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── config/
│   └── wsgi.py
│
├── manage.py
├── requirements.txt
├── .gitignore
└── README.md
```

*The structure above highlights the main application components. Individual files and folders may vary as the project evolves.*

---

## Future Improvements

- Add user authentication and personalized vehicle profiles.
- Expand diagnostic capabilities with structured vehicle information.
- Improve booking management and service status tracking.
- Add automated testing for frontend and backend APIs.
- Configure a dedicated backend domain with managed HTTPS.
- Add monitoring, logging, and production deployment hardening.

---

## Author

**Shreeya Srivastava**

B.Tech CSE — AI & ML

- GitHub: [@onlyshreeya](https://github.com/onlyshreeya)
- Project: [AutoCare AI Mechanic](https://github.com/onlyshreeya/autocare-ai-mechanic)
- Live Demo: [autocare-ai-mechanic.vercel.app](https://autocare-ai-mechanic.vercel.app)

---

If you find this project interesting, feel free to explore the repository!

**Built with React, Django, and Gemini AI.**
