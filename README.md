**Bookit API**

A FastAPI-based booking system with PostgreSQL database, that allows a user to register,
login and check for availability of service for booking. 

**🏗️ Architecture Decisions**

*Framework: FastAPI (auto-generated docs, async support)*

*Database: PostgreSQL (Relational, Render.com hosting)*

*ORM: (SQLAlchemy + Pydantic)*

*Validation: Pydantic v2*

**🚀 How to Run Locally**
PostgreSQL (local or remote)

**Installation**

# Create virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Environment Setup
Create .env file:

# 📋 Environment Variables
DATABASE_URL=
SECRET_KEY = 
ALGORITHM = 
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRES = 10

# 📥Run Application

uvicorn app.main:app --reload

# 🌐 Deployment
Host: Render.com
Database: Render PostgreSQL
Base URL: https://bookit-my4c.onrender.com
Docs: https://bookit-my4c.onrender.com/docs


# Note
if you are running it on render host for easier access:

ADMIN
email: user2@example.com
password: string

USER:
email: user@example.com
password: string

# REVIEW ID
5ed2e036-e33d-451d-9aaf-a08a8d1f0000
48122f7b-ce20-4106-a13e-dfb3475eb0ed
