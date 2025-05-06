# 📈 Finance

**Finance** is a stock trading simulator built with **Python**, **Flask**, and **SQLite**.  
It offers a simple web interface for simulating buying/selling stocks, and tracking portfolio performance.

The app uses two API:s. One to get the current prices of stocks (yfinance), and another to get memes for HTTP error messages (memegen).

---

## 🌐 Live Preview

🚀 [View the deployed app on Heroku](https://finance-project-ee67b06a0b41.herokuapp.com/)  

---

## 🔧 Tech Stack

- 🐍 **Python** (Flask)
- 🗄️ **SQLite** (lightweight database)
- 🧪 **HTML/CSS** (for UI templates)
- 🐳 **Docker** (containerized for portability)
- 🔁 **GitHub Actions** (CI/CD pipeline)
- ☁️ **Heroku** (production deployment)

---

## 🔄 CI/CD Workflow

This repository includes a fully automated deployment pipeline using **GitHub Actions**:

- ✅ Builds Docker image from the latest `main` branch
- 📦 Pushes the image to:
  - Docker Hub (`rapt9/finance`)
  - Heroku Container Registry
- 🚀 Automatically deploys the new version to Heroku

## Getting Started (Local Dev)

```bash
# Clone the repo
git clone https://github.com/rapt9/finance
cd finance

# Install dependencies
pip install -r requirements.txt

# Run the app
flask run

# Create an account at http://localhost:5000/register⁠ and start trading! 
```
## 🐳 Getting started (Pull from Docker Hub)
```bash
docker pull rapt9/finance:latest
docker run -d -p 5000:5000 rapt9/finance

# Create an account at http://localhost:5000/register⁠ and start trading! 
```
