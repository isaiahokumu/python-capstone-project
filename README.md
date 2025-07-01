# Python-capstone-project
#  🩺 Paediatric Clinical Assessment TOOL
A Python capstone project supervised by ~ Melody Bonareri

____________________________

### Project Description

This project is a digital tool that aims to provide real-time decision-making for on-ground diagnosis based on a triage workflow system. 

____________________________

### Problem solved
This is a **Streamlit-based web application** for real-time clinical assessment and disease surveillance, it is tailored for paediatric cases such as **Meningitis** and **Diarrhoea**. It integrates patient classification workflows, outbreak monitoring via web scraping, PDF/CSV report generation, emergency alerts, and analytics.
Guiding clinical workers to an interactive, user-friendly system that maximizes accurate diagnosis of the severity of a particular condition, recommending appropriate treatment plans, and focusing on disease forecasting to mitigate outbreaks and reduce mortality rates.

____________________________

## 🚀 Features

- **Patient Assessment**
  - Meningitis and Diarrhoea classification workflows
  - Automated patient ID and initials generation
  - Save, export (CSV & PDF), and analyze patient data

- **Disease Outbreak Monitoring**
  - Web scraping from WHO and CDC
  - Location-based outbreak reports with severity level
  - Mock data support for offline/demo use

- **Emergency Alerts**
  - Customizable alert thresholds
  - Live alert dashboard with severity tags

- **Analytics Dashboard**
  - Condition trends by age, gender, type
  - Pie charts, bar graphs, and time-series plots
  - Key metrics: cases, deaths, patients, alerts

- **Database Management**
  - SQLite-backed storage for patients, outbreaks, alerts
  - CSV export and record cleanup tools

____________________________

### Technologies Used

> - **Frontend**: [Streamlit](https://streamlit.io/)
> - **Backend**: Python (OOP)
> - **Database**: SQLite
> - **Data Viz**: Plotly, pandas
> - **Reporting**: ReportLab (PDF), CSV
> - **Web Scraping**: BeautifulSoup + requests

____________________________

### Data Source

Manual creation
Ministry of health website [health.go.ke]
CDC website

____________________________

### Success Criteria

This program will allow the user to enter the patient's details, output them as initials for confidentiality, prompt the user on various symptoms, relay the severity of the disease, and provide appropriate treatment options.

I'll consider it a success if it handles at least 5 entries with anonymization of critical data information and appropriate error handling, if it can save data to the database and show outbreak alerts
____________________________

### Stretch goals
Multi-language support

_____________________________

### 📦 Installation

```bash
git clone https://github.com/yourusername/pcat-clinical-tool.git
cd pcat-clinical-tool
pip install -r requirements.txt
streamlit run pcat.py



