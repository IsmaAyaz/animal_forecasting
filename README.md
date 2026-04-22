🐐 Livestock Population Simulation Dashboard

Project Overview

This project is a Livestock Population Simulation System that models the growth, reproduction, selling, and mortality of animals such as:

🐐 Goats
🐮 Cows
🐃 Buffalo

It uses:

Streamlit → Interactive frontend dashboard

FastAPI → Backend simulation engine

NumPy & Pandas → Data processing

Matplotlib → Visualization

The system allows users to simulate livestock population dynamics over time with customizable biological and economic parameters.

Features:

🔢 Population Simulation
Male & female population tracking
Age-based distribution
Multi-iteration simulation for realistic results

🐣 Reproduction Modeling
Pregnancy probability
Birth distribution (1, 2, 3+ kids)
Female/male birth ratio

⚰️ Mortality System
Age-based death probabilities
Customizable death rates per age group

💰 Selling Logic
Selling based on age thresholds
Adjustable selling probabilities
Separate tracking for male & female sales

📊 Visualization Dashboard
Population trends over time
Selling analysis
Deaths & births graphs
Final simulation summary

📁 Export Options
Download simulation data (CSV)
Download summary report (TXT)

🗂️ Project Structure

├── animal_params.py   # Default parameters for each animal

├── goat.py            # Streamlit frontend UI

├── main.py            # FastAPI backend API

├── model.py           # Core simulation logic

├── requirements.txt   # Project dependencies

How to Run the Project:

1️⃣ Clone the Repository

git clone https://github.com/IsmaAyaz/animal_forecasting.git

cd livestock-simulation

2️⃣ Install Dependencies

pip install -r requirements.txt

3️⃣ Start Backend (FastAPI)

uvicorn main:app --reload

Backend will run at:

http://localhost:8000

4️⃣ Start Frontend (Streamlit)

streamlit run goat.py

How It Works:

User inputs:
Initial population
Age distribution
Probabilities (birth, death, selling)
Streamlit sends request to FastAPI

FastAPI:
Runs multiple simulation iterations
Uses stochastic (random) modeling
Aggregates results
Results returned and visualized in dashboard

📊 Key Parameters

Parameter	Description

t_prod_start	Age when reproduction starts

t_prod_end	Age when reproduction ends

p_get_pregnant	Pregnancy probability

p_kids	Distribution of number of kids

death_probs	Age-based mortality

p_sell_male/female	Selling probability

