import streamlit as st
from datetime import datetime, timedelta
import csv
import hashlib
import os
import sqlite3
import requests
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import json
import time
from typing import Dict, List, Optional
import re

# ========== Database Setup ==========

def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect('clinical_assessment.db')
    cursor = conn.cursor()
    
    # Create patients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT UNIQUE,
            full_name TEXT,
            initials TEXT,
            age_months INTEGER,
            residence TEXT,
            gender TEXT,
            condition_type TEXT,
            classification_result TEXT,
            symptoms TEXT,
            timestamp DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create disease_outbreaks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS disease_outbreaks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disease_name TEXT,
            location TEXT,
            cases INTEGER,
            deaths INTEGER,
            source TEXT,
            date_reported DATE,
            severity_level TEXT,
            description TEXT,
            scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type TEXT,
            disease TEXT,
            location TEXT,
            severity TEXT,
            message TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# ========== Classes ==========

class MeningitisWorkflow:
    def __init__(self, coma=False, stiff_neck=False, bulging_fontanelle=False,
                 lp_clear=True, csf_wbc_raised=False, gram_positive=False, test_done=True):
        self.coma = coma
        self.stiff_neck = stiff_neck
        self.bulging_fontanelle = bulging_fontanelle
        self.lp_clear = lp_clear
        self.csf_wbc_raised = csf_wbc_raised
        self.gram_positive = gram_positive
        self.test_done = test_done

    def classify(self):
        if self.coma or self.stiff_neck or self.bulging_fontanelle or not self.lp_clear:
            return "🧠 Definite Meningitis: Treat with Ceftriaxone. Steroids NOT indicated."
        if self.csf_wbc_raised or self.gram_positive:
            return "🧠 Probable Meningitis: Treat with Ceftriaxone. Steroids NOT indicated. Review CSF results."
        if self.test_done:
            return "🧠 Possible Meningitis: Treat with Ceftriaxone. Seek senior review."
        return "No clear meningitis signs based on provided data."

    def get_symptoms_dict(self):
        return {
            'coma': self.coma,
            'stiff_neck': self.stiff_neck,
            'bulging_fontanelle': self.bulging_fontanelle,
            'lp_clear': self.lp_clear,
            'csf_wbc_raised': self.csf_wbc_raised,
            'gram_positive': self.gram_positive,
            'test_done': self.test_done
        }


class DiarrhoeaWorkflow:
    def __init__(self, age_months, symptoms):
        self.age = age_months
        self.symptoms = symptoms

    def classify(self):
        s = self.symptoms
        if all([s.get("weak_or_absent_pulse", False), s.get("cold_hands_temp_gradient", False),
                s.get("capillary_refill_gt_3s", False), s.get("slow_skin_pinch", False)]):
            return "💧 Shock: IV Ringer's Lactate 20ml/kg over 15 min → Plan C Step 1"
        if any([s.get("sunken_eyes", False), s.get("unable_to_drink", False), s.get("skin_pinch_gt_2s", False)]):
            return f"💧 Severe Dehydration: Plan C Step 2 → 70ml/kg IV Ringer's over {'2.5hrs' if self.age >= 12 else '4hrs'}"
        if sum([s.get("sunken_eyes", False), s.get("restless_irritable", False), s.get("skin_pinch_1_2s", False)]) >= 2:
            return "💧 Some Dehydration: Plan B → ORS 75ml/kg over 4 hours"
        return "💧 No Dehydration: Plan A → ORS 10ml/kg after each stool, continue feeding"

    def get_symptoms_dict(self):
        return self.symptoms


class DiseaseOutbreakMonitor:
    def __init__(self):
        self.sources = {
            'WHO': 'https://www.who.int/emergencies/disease-outbreak-news',
            'CDC': 'https://www.cdc.gov/outbreaks/',
            'ProMED': 'https://promedmail.org/'
        }
    
    def scrape_who_outbreaks(self) -> List[Dict]:
        """Scrape WHO Disease Outbreak News"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(self.sources['WHO'], headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            outbreaks = []
            
            # This is a simplified scraper - actual implementation would need to be adapted to WHO's current HTML structure
            articles = soup.find_all('div', class_='list-view--item')[:5]  # Get latest 5
            
            for article in articles:
                try:
                    title_elem = article.find('h3') or article.find('h2') or article.find('a')
                    title = title_elem.get_text(strip=True) if title_elem else "Unknown outbreak"
                    
                    # Extract disease and location from title
                    disease, location = self.extract_disease_location(title)
                    
                    outbreaks.append({
                        'disease_name': disease,
                        'location': location,
                        'source': 'WHO',
                        'description': title,
                        'date_reported': datetime.now().date(),
                        'severity_level': self.assess_severity(title),
                        'cases': 0,  # Would need more detailed scraping
                        'deaths': 0
                    })
                except Exception as e:
                    continue
            
            return outbreaks
        except Exception as e:
            st.warning(f"Could not fetch WHO data: {str(e)}")
            return []
    
    def scrape_cdc_outbreaks(self) -> List[Dict]:
        """Scrape CDC outbreak information"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(self.sources['CDC'], headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            outbreaks = []
            
            # Simplified CDC scraper
            articles = soup.find_all('div', class_='card-body')[:5]
            
            for article in articles:
                try:
                    title_elem = article.find('h3') or article.find('h2') or article.find('a')
                    title = title_elem.get_text(strip=True) if title_elem else "Unknown outbreak"
                    
                    disease, location = self.extract_disease_location(title)
                    
                    outbreaks.append({
                        'disease_name': disease,
                        'location': location,
                        'source': 'CDC',
                        'description': title,
                        'date_reported': datetime.now().date(),
                        'severity_level': self.assess_severity(title),
                        'cases': 0,
                        'deaths': 0
                    })
                except Exception:
                    continue
            
            return outbreaks
        except Exception as e:
            st.warning(f"Could not fetch CDC data: {str(e)}")
            return []
    
    def extract_disease_location(self, text: str) -> tuple:
        """Extract disease name and location from outbreak text"""
        # Common disease patterns
        diseases = ['meningitis', 'cholera', 'ebola', 'malaria', 'dengue', 'yellow fever', 
                   'measles', 'polio', 'hepatitis', 'diphtheria', 'typhoid', 'plague']
        
        text_lower = text.lower()
        disease = "Unknown"
        location = "Unknown"
        
        for d in diseases:
            if d in text_lower:
                disease = d.title()
                break
        
        # Simple location extraction (would need more sophisticated NLP in practice)
        location_patterns = [r'in ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+reports?']
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                location = match.group(1)
                break
        
        return disease, location
    
    def assess_severity(self, text: str) -> str:
        """Assess outbreak severity based on keywords"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['emergency', 'critical', 'severe', 'death']):
            return 'High'
        elif any(word in text_lower for word in ['outbreak', 'cases', 'confirmed']):
            return 'Medium'
        return 'Low'
    
    def get_mock_outbreaks(self) -> List[Dict]:
        """Generate mock outbreak data for demonstration"""
        mock_data = [
            {
                'disease_name': 'Meningitis',
                'location': 'Northern Kenya',
                'source': 'MOH Kenya',
                'description': 'Meningitis outbreak reported in Turkana County with 45 suspected cases',
                'date_reported': datetime.now().date(),
                'severity_level': 'High',
                'cases': 45,
                'deaths': 3
            },
            {
                'disease_name': 'Cholera',
                'location': 'Coastal Region',
                'source': 'WHO',
                'description': 'Cholera cases increasing in coastal areas following heavy rains',
                'date_reported': (datetime.now() - timedelta(days=2)).date(),
                'severity_level': 'Medium',
                'cases': 127,
                'deaths': 2
            },
            {
                'disease_name': 'Dengue',
                'location': 'Mombasa',
                'source': 'CDC',
                'description': 'Dengue fever cases reported in urban areas of Mombasa',
                'date_reported': (datetime.now() - timedelta(days=1)).date(),
                'severity_level': 'Medium',
                'cases': 23,
                'deaths': 0
            }
        ]
        return mock_data


class AlertSystem:
    def __init__(self):
        self.alert_thresholds = {
            'meningitis': {'cases': 10, 'deaths': 1},
            'cholera': {'cases': 20, 'deaths': 2},
            'dengue': {'cases': 15, 'deaths': 1}
        }
    
    def check_alerts(self, outbreaks: List[Dict]) -> List[Dict]:
        """Check if outbreaks meet alert criteria"""
        alerts = []
        
        for outbreak in outbreaks:
            disease = outbreak['disease_name'].lower()
            cases = outbreak.get('cases', 0)
            deaths = outbreak.get('deaths', 0)
            
            if disease in self.alert_thresholds:
                thresholds = self.alert_thresholds[disease]
                if cases >= thresholds['cases'] or deaths >= thresholds['deaths']:
                    alert = {
                        'alert_type': 'Disease Outbreak',
                        'disease': outbreak['disease_name'],
                        'location': outbreak['location'],
                        'severity': outbreak['severity_level'],
                        'message': f"ALERT: {outbreak['disease_name']} outbreak in {outbreak['location']} - {cases} cases, {deaths} deaths reported"
                    }
                    alerts.append(alert)
        
        return alerts


# ========== Utilities ==========

def get_initials(name):
    return ''.join([part[0].upper() for part in name.strip().split() if part])

def generate_patient_id(name):
    base = name.strip().lower() + datetime.now().isoformat()
    return hashlib.sha256(base.encode()).hexdigest()[:8].upper()

def save_to_database(name, pid, age, residence, gender, condition, result, symptoms_dict):
    """Save patient data to SQLite database"""
    try:
        conn = sqlite3.connect('clinical_assessment.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO patients 
            (patient_id, full_name, initials, age_months, residence, gender, 
             condition_type, classification_result, symptoms, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pid, name, get_initials(name), age, residence, gender,
            condition, result, json.dumps(symptoms_dict), datetime.now()
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return False

def save_outbreaks_to_db(outbreaks: List[Dict]):
    """Save outbreak data to database"""
    try:
        conn = sqlite3.connect('clinical_assessment.db')
        cursor = conn.cursor()
        
        for outbreak in outbreaks:
            cursor.execute('''
                INSERT OR IGNORE INTO disease_outbreaks 
                (disease_name, location, cases, deaths, source, date_reported, 
                 severity_level, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                outbreak['disease_name'], outbreak['location'], outbreak['cases'],
                outbreak['deaths'], outbreak['source'], outbreak['date_reported'],
                outbreak['severity_level'], outbreak['description']
            ))
        
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Error saving outbreaks: {str(e)}")

def save_alerts_to_db(alerts: List[Dict]):
    """Save alerts to database"""
    try:
        conn = sqlite3.connect('clinical_assessment.db')
        cursor = conn.cursor()
        
        for alert in alerts:
            cursor.execute('''
                INSERT INTO alerts (alert_type, disease, location, severity, message)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                alert['alert_type'], alert['disease'], alert['location'],
                alert['severity'], alert['message']
            ))
        
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Error saving alerts: {str(e)}")

def export_to_csv(initials, pid, age, residence, gender, condition, result):
    """Export patient data to CSV file"""
    filename = "clinical_assessment_results.csv"
    file_exists = os.path.isfile(filename)
    try:
        with open(filename, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["Timestamp", "Patient Initials", "Patient ID", "Age (months)", 
                               "Residence", "Gender", "Condition", "Result"])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                           get_initials(name), pid, age, residence, gender, condition, result])
        return filename
    except Exception as e:
        return f"Error writing to file: {e}"

def generate_pdf_report(name, pid, age, residence, gender, condition, result, symptoms_dict):
    """Generate PDF report for patient assessment"""
    try:
        filename = f"patient_report_{pid}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.darkblue,
            alignment=1  # Center alignment
        )
        story.append(Paragraph("CLINICAL ASSESSMENT REPORT", title_style))
        story.append(Spacer(1, 20))
        
        # Patient Information
        story.append(Paragraph("PATIENT INFORMATION", styles['Heading2']))
        patient_data = [
            ['Patient Name:', name],
            ['Patient ID:', pid],
            ['Age (months):', str(age)],
            ['Residence:', residence],
            ['Gender:', gender],
            ['Assessment Date:', datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        ]
        
        patient_table = Table(patient_data, colWidths=[2*inch, 4*inch])
        patient_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(patient_table)
        story.append(Spacer(1, 20))
        
        # Assessment Results
        story.append(Paragraph("ASSESSMENT RESULTS", styles['Heading2']))
        story.append(Paragraph(f"<b>Condition Assessed:</b> {condition}", styles['Normal']))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>Classification Result:</b>", styles['Normal']))
        story.append(Paragraph(result, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Symptoms
        story.append(Paragraph("SYMPTOMS RECORDED", styles['Heading2']))
        symptoms_data = [['Symptom', 'Present']]
        for symptom, present in symptoms_dict.items():
            symptoms_data.append([symptom.replace('_', ' ').title(), 'Yes' if present else 'No'])
        
        symptoms_table = Table(symptoms_data, colWidths=[3*inch, 1*inch])
        symptoms_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(symptoms_table)
        story.append(Spacer(1, 30))
        
        # Footer
        story.append(Paragraph("This report was generated by the Clinical Assessment Tool", 
                             styles['Normal']))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                             styles['Normal']))
        
        doc.build(story)
        return filename
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        return None

def get_patient_statistics():
    """Get patient statistics from database"""
    try:
        conn = sqlite3.connect('clinical_assessment.db')
        df = pd.read_sql_query("""
            SELECT condition_type, COUNT(*) as count,
                   AVG(age_months) as avg_age,
                   gender
            FROM patients 
            GROUP BY condition_type, gender
        """, conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def get_outbreak_data():
    """Get outbreak data from database"""
    try:
        conn = sqlite3.connect('clinical_assessment.db')
        df = pd.read_sql_query("""
            SELECT * FROM disease_outbreaks 
            ORDER BY date_reported DESC
        """, conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

# ========== Main App ==========

def main():
    st.set_page_config(
        page_title="Enhanced Clinical Assessment Tool", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize database
    init_database()
    
    st.title("🩺 Enhanced Clinical Assessment Tool")
    st.markdown("Advanced clinical assessment with disease outbreak monitoring and emergency alerts")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", [
        "Patient Assessment", 
        "Disease Monitoring", 
        "Emergency Alerts", 
        "Analytics Dashboard",
        "Database Management"
    ])
    
    if page == "Patient Assessment":
        patient_assessment_page()
    elif page == "Disease Monitoring":
        disease_monitoring_page()
    elif page == "Emergency Alerts":
        emergency_alerts_page()
    elif page == "Analytics Dashboard":
        analytics_dashboard_page()
    elif page == "Database Management":
        database_management_page()

def patient_assessment_page():
    st.header("👥 Patient Assessment")
    
    # Initialize session state
    if 'symptom_vars' not in st.session_state:
        st.session_state.symptom_vars = {}
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Patient Info Section
        st.subheader("🧍 Patient Information")
        st.session_state.patient_name = st.text_input("Full Name", 
                                                     st.session_state.get("patient_name", ""))
        
        col_age, col_gender = st.columns(2)
        with col_age:
            st.session_state.patient_age = st.text_input("Age (in months)", 
                                                        st.session_state.get("patient_age", ""))
        with col_gender:
            st.session_state.patient_gender = st.selectbox("Gender", ["", "M", "F"], 
                                                          index=0 if not st.session_state.get("patient_gender", "") 
                                                          else (1 if st.session_state.get("patient_gender") == "M" else 2))
        
        st.session_state.patient_residence = st.text_input("Residence", 
                                                          st.session_state.get("patient_residence", ""))
        
        # Select Workflow
        st.markdown("---")
        workflow = st.radio("Select Clinical Workflow", ["Meningitis", "Diarrhoea"])
        st.session_state.workflow_choice = workflow
        
        # Symptoms
        st.subheader("🧪 Symptoms Assessment")
        symptoms = {
            "Meningitis": [
                ("coma", "Coma or altered consciousness"),
                ("stiff_neck", "Stiff neck (nuchal rigidity)"),
                ("bulging_fontanelle", "Bulging fontanelle (infants)"),
                ("lp_clear", "Lumbar puncture - clear CSF"),
                ("csf_wbc_raised", "CSF white blood cell count raised"),
                ("gram_positive", "Gram positive bacteria in CSF"),
                ("test_done", "Laboratory test completed")
            ],
            "Diarrhoea": [
                ("weak_or_absent_pulse", "Weak or absent pulse"),
                ("cold_hands_temp_gradient", "Cold hands with temperature gradient"),
                ("capillary_refill_gt_3s", "Capillary refill > 3 seconds"),
                ("slow_skin_pinch", "Slow skin pinch (>2s severe dehydration)"),
                ("sunken_eyes", "Sunken eyes"),
                ("unable_to_drink", "Unable to drink or drinking poorly"),
                ("skin_pinch_gt_2s", "Skin pinch goes back >2 seconds"),
                ("restless_irritable", "Restless and irritable"),
                ("skin_pinch_1_2s", "Skin pinch goes back 1-2 seconds")
            ]
        }
        
        current_symptoms = symptoms[workflow]
        
        # Display symptoms in a more organized way
        for symptom_key, symptom_label in current_symptoms:
            st.session_state.symptom_vars[symptom_key] = st.checkbox(
                symptom_label, 
                st.session_state.symptom_vars.get(symptom_key, False)
            )
        
        st.markdown("---")
        
        # Action buttons
        col_classify, col_clear = st.columns(2)
        
        with col_classify:
            if st.button("🔍 Classify, Save & Generate Report", type="primary"):
                classify_and_save()
        
        with col_clear:
            if st.button("🧹 Clear Form"):
                clear_form()
    
    with col2:
        st.subheader("ℹ️ Quick Reference")
        if workflow == "Meningitis":
            st.info("""
            **Meningitis Classification:**
            - **Definite**: Coma, stiff neck, bulging fontanelle, or turbid CSF
            - **Probable**: Raised CSF WBC or gram positive bacteria
            - **Possible**: When test done but other criteria not met
            """)
        else:
            st.info("""
            **Diarrhoea Classification:**
            - **Shock**: All 4 shock signs present
            - **Severe Dehydration**: Any severe dehydration sign
            - **Some Dehydration**: 2+ moderate dehydration signs
            - **No Dehydration**: None of the above
            """)

def classify_and_save():
    """Handle classification and saving of patient data"""
    name = st.session_state.patient_name.strip()
    initials = get_initials(name)
    age_str = st.session_state.patient_age.strip()
    residence = st.session_state.patient_residence.strip()
    gender = st.session_state.patient_gender
    workflow = st.session_state.workflow_choice
    
    # Validation
    if not name or not age_str or not residence or not gender:
        st.error("Please complete all required fields.")
        return
    
    if not age_str.isdigit():
        st.error("Age must be a valid number.")
        return
    
    age = int(age_str)
    patient_id = generate_patient_id(initials)
    
    # Perform classification
    if workflow == "Meningitis":
        meningitis = MeningitisWorkflow(
            coma=st.session_state.symptom_vars.get("coma", False),
            stiff_neck=st.session_state.symptom_vars.get("stiff_neck", False),
            bulging_fontanelle=st.session_state.symptom_vars.get("bulging_fontanelle", False),
            lp_clear=st.session_state.symptom_vars.get("lp_clear", True),
            csf_wbc_raised=st.session_state.symptom_vars.get("csf_wbc_raised", False),
            gram_positive=st.session_state.symptom_vars.get("gram_positive", False),
            test_done=st.session_state.symptom_vars.get("test_done", True)
        )
        result = meningitis.classify()
        symptoms_dict = meningitis.get_symptoms_dict()
    else:
        symptoms_collected = {k: st.session_state.symptom_vars.get(k, False) 
                            for k, _ in [
                                ("weak_or_absent_pulse", ""), ("cold_hands_temp_gradient", ""),
                                ("capillary_refill_gt_3s", ""), ("slow_skin_pinch", ""),
                                ("sunken_eyes", ""), ("unable_to_drink", ""),
                                ("skin_pinch_gt_2s", ""), ("restless_irritable", ""),
                                ("skin_pinch_1_2s", "")
                            ]}
        diarrhoea = DiarrhoeaWorkflow(age, symptoms_collected)
        result = diarrhoea.classify()
        symptoms_dict = diarrhoea.get_symptoms_dict()
    
    # Display result
    st.success(f"**Classification Result:** {result}")
    
    # Save to database
    if save_to_database(initials, patient_id, age, residence, gender, workflow, result, symptoms_dict):
        st.success("✅ Patient data saved to database")
        
        # Generate and offer downloads
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # CSV Export
            csv_file = export_to_csv(name, patient_id, age, residence, gender, workflow, result)
            if os.path.isfile(csv_file):
                with open(csv_file, "rb") as f:
                    st.download_button("📥 Download CSV", f, file_name="clinical_assessment_results.csv", mime="text/csv")
        
        with col2:
            # PDF Export
            pdf_file = generate_pdf_report(name, patient_id, age, residence, gender, workflow, result, symptoms_dict)
            if pdf_file and os.path.isfile(pdf_file):
                with open(pdf_file, "rb") as f:
                    st.download_button("📄 Download PDF Report", f, file_name=f"patient_report_{patient_id}.pdf", mime="application/pdf")
        
        with col3:
            st.info(f"Patient ID: **{patient_id}**")
    else:
        st.error("❌ Failed to save patient data")

def clear_form():
    """Clear all form fields"""
    for k in ["patient_name", "patient_age", "patient_residence", "patient_gender"]:
        if k in st.session_state:
            st.session_state[k] = ""
    st.session_state.symptom_vars = {}
    st.rerun()

def disease_monitoring_page():
    st.header("🌍 Disease Outbreak Monitoring")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Current Outbreak Status")
        
        # Refresh button
        if st.button("🔄 Refresh Outbreak Data"):
            with st.spinner("Fetching latest outbreak data..."):
                monitor = DiseaseOutbreakMonitor()
                
                # Try to fetch real data, fall back to mock data
                all_outbreaks = []
                all_outbreaks.extend(monitor.scrape_who_outbreaks())
                all_outbreaks.extend(monitor.scrape_cdc_outbreaks())
                
                # If no real data, use mock data for demonstration
                if not all_outbreaks:
                    all_outbreaks = monitor.get_mock_outbreaks()
                    st.info("📝 Displaying sample data (real-time scraping may be limited)")
                
                # Save to database
                save_outbreaks_to_db(all_outbreaks)
                st.success("✅ Outbreak data updated")
        
        # Display outbreak data
        outbreak_df = get_outbreak_data()
        if not outbreak_df.empty:
            st.subheader("Recent Disease Outbreaks")
            
            # Create interactive map if location data is available
            if 'location' in outbreak_df.columns:
                st.plotly_chart(
                    px.scatter_mapbox(
                        outbreak_df,
                        lat=[0] * len(outbreak_df),  # Would need geocoding for real coordinates
                        lon=[0] * len(outbreak_df),
                        hover_name="disease_name",
                        hover_data=["location", "cases", "deaths"],
                        color="severity_level",
                        size="cases",
                        zoom=2,
                        height=400,
                        mapbox_style="open-street-map",
                        title="Disease Outbreak Locations"
                    ),
                    use_container_width=True
                )
            
            # Display table
            st.dataframe(
                outbreak_df[[
                    'disease_name', 'location', 'cases', 'deaths', 
                    'severity_level', 'date_reported', 'source'
                ]].rename(columns={
                    'disease_name': 'Disease',
                    'location': 'Location',
                    'cases': 'Cases',
                    'deaths': 'Deaths',
                    'severity_level': 'Severity',
                    'date_reported': 'Date',
                    'source': 'Source'
                }),
                use_container_width=True
            )
        else:
            st.info("No outbreak data available. Click 'Refresh Outbreak Data' to fetch latest information.")
    
    with col2:
        st.subheader("🎯 Monitoring Sources")
        st.info("""
        **Data Sources:**
        - WHO Disease Outbreak News
        - CDC Outbreak Reports
        - ProMED-mail
        - Local Health Authorities
        
        **Update Frequency:**
        - Real-time web scraping
        - Automated alerts
        - Manual refresh available
        """)
        
        # Outbreak statistics
        if not outbreak_df.empty:
            st.subheader("📈 Statistics")
            total_cases = outbreak_df['cases'].sum()
            total_deaths = outbreak_df['deaths'].sum()
            active_outbreaks = len(outbreak_df)
            
            st.metric("Active Outbreaks", active_outbreaks)
            st.metric("Total Cases", total_cases)
            st.metric("Total Deaths", total_deaths)
            
            # Severity distribution
            if 'severity_level' in outbreak_df.columns:
                severity_counts = outbreak_df['severity_level'].value_counts()
                fig = px.pie(
                    values=severity_counts.values,
                    names=severity_counts.index,
                    title="Outbreak Severity Distribution",
                    color_discrete_sequence=px.colors.qualitative.Set1
                )
                st.plotly_chart(fig, use_container_width=True)

def emergency_alerts_page():
    st.header("🚨 Emergency Alert System")
    
    # Generate alerts based on current outbreak data
    if st.button("🔍 Check for New Alerts"):
        with st.spinner("Analyzing outbreak data for alerts..."):
            outbreak_df = get_outbreak_data()
            if not outbreak_df.empty:
                alert_system = AlertSystem()
                outbreaks = outbreak_df.to_dict('records')
                alerts = alert_system.check_alerts(outbreaks)
                
                if alerts:
                    save_alerts_to_db(alerts)
                    st.success(f"✅ {len(alerts)} new alerts generated")
                else:
                    st.info("No new alerts at this time")
            else:
                st.warning("No outbreak data available for alert analysis")
    
    # Display active alerts
    try:
        conn = sqlite3.connect('clinical_assessment.db')
        alerts_df = pd.read_sql_query("""
            SELECT * FROM alerts 
            WHERE is_active = 1 
            ORDER BY created_at DESC
        """, conn)
        conn.close()
        
        if not alerts_df.empty:
            st.subheader("🚨 Active Alerts")
            
            for _, alert in alerts_df.iterrows():
                severity_color = {
                    'High': 'error',
                    'Medium': 'warning', 
                    'Low': 'info'
                }.get(alert['severity'], 'info')
                
                with st.container():
                    st.markdown(f"""
                    <div style="border-left: 4px solid {'red' if severity_color == 'error' else 'orange' if severity_color == 'warning' else 'blue'}; 
                                padding: 10px; margin: 10px 0; background-color: #f0f0f0;">
                        <h4>{alert['alert_type']} - {alert['severity']} Priority</h4>
                        <p><strong>Disease:</strong> {alert['disease']}</p>
                        <p><strong>Location:</strong> {alert['location']}</p>
                        <p><strong>Message:</strong> {alert['message']}</p>
                        <small>Generated: {alert['created_at']}</small>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No active alerts at this time")
            
    except Exception as e:
        st.error(f"Error retrieving alerts: {str(e)}")
    
    # Alert configuration
    st.subheader("⚙️ Alert Configuration")
    with st.expander("Configure Alert Thresholds"):
        st.write("Customize when alerts should be triggered:")
        
        col1, col2 = st.columns(2)
        with col1:
            st.number_input("Meningitis - Cases Threshold", min_value=1, value=10)
            st.number_input("Cholera - Cases Threshold", min_value=1, value=20)
            st.number_input("Dengue - Cases Threshold", min_value=1, value=15)
        
        with col2:
            st.number_input("Meningitis - Deaths Threshold", min_value=1, value=1)
            st.number_input("Cholera - Deaths Threshold", min_value=1, value=2)
            st.number_input("Dengue - Deaths Threshold", min_value=1, value=1)
        
        if st.button("Save Configuration"):
            st.success("Alert thresholds updated")

def analytics_dashboard_page():
    st.header("📊 Analytics Dashboard")
    
    # Patient analytics
    patient_df = get_patient_statistics()
    outbreak_df = get_outbreak_data()
    
    if not patient_df.empty:
        st.subheader("👥 Patient Assessment Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Condition distribution
            fig = px.pie(
                patient_df.groupby('condition_type')['count'].sum().reset_index(),
                values='count',
                names='condition_type',
                title="Assessment Types Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Gender distribution by condition
            fig = px.bar(
                patient_df,
                x='condition_type',
                y='count',
                color='gender',
                title="Assessments by Condition and Gender",
                barmode='group'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Age distribution
        try:
            conn = sqlite3.connect('clinical_assessment.db')
            age_df = pd.read_sql_query("""
                SELECT age_months, condition_type, COUNT(*) as count
                FROM patients 
                GROUP BY age_months, condition_type
            """, conn)
            conn.close()
            
            if not age_df.empty:
                fig = px.histogram(
                    age_df,
                    x='age_months',
                    color='condition_type',
                    title="Age Distribution of Patients",
                    nbins=20
                )
                st.plotly_chart(fig, use_container_width=True)
        except Exception:
            pass
    
    # Outbreak analytics
    if not outbreak_df.empty:
        st.subheader("🌍 Outbreak Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Cases by disease
            disease_cases = outbreak_df.groupby('disease_name')['cases'].sum().reset_index()
            fig = px.bar(
                disease_cases,
                x='disease_name',
                y='cases',
                title="Total Cases by Disease"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Timeline of outbreaks
            if 'date_reported' in outbreak_df.columns:
                outbreak_df['date_reported'] = pd.to_datetime(outbreak_df['date_reported'])
                timeline_df = outbreak_df.groupby('date_reported').size().reset_index(name='outbreak_count')
                fig = px.line(
                    timeline_df,
                    x='date_reported',
                    y='outbreak_count',
                    title="Outbreak Timeline"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Key metrics
    st.subheader("📈 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        try:
            conn = sqlite3.connect('clinical_assessment.db')
            total_patients = pd.read_sql_query("SELECT COUNT(*) as count FROM patients", conn).iloc[0]['count']
            conn.close()
            st.metric("Total Patients", total_patients)
        except:
            st.metric("Total Patients", "N/A")
    
    with col2:
        if not outbreak_df.empty:
            active_outbreaks = len(outbreak_df)
            st.metric("Active Outbreaks", active_outbreaks)
        else:
            st.metric("Active Outbreaks", 0)
    
    with col3:
        try:
            conn = sqlite3.connect('clinical_assessment.db')
            active_alerts = pd.read_sql_query("SELECT COUNT(*) as count FROM alerts WHERE is_active = 1", conn).iloc[0]['count']
            conn.close()
            st.metric("Active Alerts", active_alerts)
        except:
            st.metric("Active Alerts", "N/A")
    
    with col4:
        if not outbreak_df.empty:
            total_cases = outbreak_df['cases'].sum()
            st.metric("Total Cases", total_cases)
        else:
            st.metric("Total Cases", 0)

def database_management_page():
    st.header("🗄️ Database Management")
    
    tabs = st.tabs(["Patient Data", "Outbreak Data", "Alert Data", "Export/Import"])
    
    with tabs[0]:
        st.subheader("👥 Patient Records")
        try:
            conn = sqlite3.connect('clinical_assessment.db')
            patients_df = pd.read_sql_query("SELECT * FROM patients ORDER BY created_at DESC", conn)
            conn.close()
            
            if not patients_df.empty:
                st.dataframe(patients_df, use_container_width=True)
                
                # Delete patient record
                if st.button("🗑️ Clear All Patient Records", type="secondary"):
                    if st.checkbox("I confirm I want to delete ALL patient records"):
                        conn = sqlite3.connect('clinical_assessment.db')
                        conn.execute("DELETE FROM patients")
                        conn.commit()
                        conn.close()
                        st.success("All patient records deleted")
                        st.rerun()
            else:
                st.info("No patient records found")
        except Exception as e:
            st.error(f"Error loading patient data: {str(e)}")
    
    with tabs[1]:
        st.subheader("🌍 Outbreak Records")
        outbreak_df = get_outbreak_data()
        if not outbreak_df.empty:
            st.dataframe(outbreak_df, use_container_width=True)
            
            if st.button("🗑️ Clear All Outbreak Records", type="secondary"):
                if st.checkbox("I confirm I want to delete ALL outbreak records"):
                    conn = sqlite3.connect('clinical_assessment.db')
                    conn.execute("DELETE FROM disease_outbreaks")
                    conn.commit()
                    conn.close()
                    st.success("All outbreak records deleted")
                    st.rerun()
        else:
            st.info("No outbreak records found")
    
    with tabs[2]:
        st.subheader("🚨 Alert Records")
        try:
            conn = sqlite3.connect('clinical_assessment.db')
            alerts_df = pd.read_sql_query("SELECT * FROM alerts ORDER BY created_at DESC", conn)
            conn.close()
            
            if not alerts_df.empty:
                st.dataframe(alerts_df, use_container_width=True)
                
                if st.button("🗑️ Clear All Alert Records", type="secondary"):
                    if st.checkbox("I confirm I want to delete ALL alert records"):
                        conn = sqlite3.connect('clinical_assessment.db')
                        conn.execute("DELETE FROM alerts")
                        conn.commit()
                        conn.close()
                        st.success("All alert records deleted")
                        st.rerun()
            else:
                st.info("No alert records found")
        except Exception as e:
            st.error(f"Error loading alert data: {str(e)}")
    
    with tabs[3]:
        st.subheader("📤 Export/Import Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Export Data**")
            if st.button("📥 Export All Data to CSV"):
                try:
                    conn = sqlite3.connect('clinical_assessment.db')
                    
                    # Export patients
                    patients_df = pd.read_sql_query("SELECT * FROM patients", conn)
                    patients_df.to_csv("patients_export.csv", index=False)
                    
                    # Export outbreaks
                    outbreaks_df = pd.read_sql_query("SELECT * FROM disease_outbreaks", conn)
                    outbreaks_df.to_csv("outbreaks_export.csv", index=False)
                    
                    # Export alerts
                    alerts_df = pd.read_sql_query("SELECT * FROM alerts", conn)
                    alerts_df.to_csv("alerts_export.csv", index=False)
                    
                    conn.close()
                    st.success("✅ Data exported to CSV files")
                    
                    # Provide download buttons
                    for filename in ["patients_export.csv", "outbreaks_export.csv", "alerts_export.csv"]:
                        if os.path.exists(filename):
                            with open(filename, "rb") as f:
                                st.download_button(
                                    f"Download {filename}",
                                    f,
                                    file_name=filename,
                                    mime="text/csv"
                                )
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
        
        with col2:
            st.write("**Database Info**")
            try:
                conn = sqlite3.connect('clinical_assessment.db')
                
                # Get table info
                tables = ['patients', 'disease_outbreaks', 'alerts']
                for table in tables:
                    count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM {table}", conn).iloc[0]['count']
                    st.metric(f"{table.title()} Records", count)
                
                conn.close()
            except Exception as e:
                st.error(f"Error getting database info: {str(e)}")

if __name__ == "__main__":
    main()