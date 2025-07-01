"""
Integration Example: Enhancing pcat.py with MOH Risk Scraper
============================================================

This script demonstrates how to integrate the enhanced MOH risk scraper
with the existing pcat.py clinical assessment tool.
"""

import streamlit as st
import sys
import os

# Add the current directory to the path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from moh_risk_scraper import EnhancedMOHScraper, AgeConstraintManager, RiskAreaDatabase, create_streamlit_app
from typing import Dict, List

# Enhanced Disease Outbreak Monitor to replace the original
class EnhancedDiseaseOutbreakMonitor:
    """Enhanced version of the DiseaseOutbreakMonitor class from pcat.py"""
    
    def __init__(self):
        self.enhanced_scraper = EnhancedMOHScraper()
        self.age_manager = AgeConstraintManager()
        self.risk_db = RiskAreaDatabase()
        
        # Keep compatibility with original sources
        self.sources = {
            'WHO': 'https://www.who.int/emergencies/disease-outbreak-news',
            'CDC': 'https://www.cdc.gov/outbreaks/',
            'ProMED': 'https://promedmail.org/',
            'MOH_Kenya': 'https://www.health.go.ke',
            'WHO_AFRO': 'https://www.afro.who.int'
        }
    
    def get_enhanced_outbreaks(self) -> List[Dict]:
        """Get enhanced outbreak data with risk classification"""
        risk_areas = self.enhanced_scraper.get_all_risk_areas()
        
        # Convert RiskArea objects to dictionary format compatible with pcat.py
        outbreaks = []
        for area in risk_areas:
            outbreaks.append({
                'disease_name': area.disease,
                'location': area.location,
                'source': area.source_url,
                'description': area.additional_info,
                'date_reported': area.date_reported.date(),
                'severity_level': area.risk_level,
                'cases': area.cases,
                'deaths': area.deaths
            })
        
        # Save to risk database
        self.risk_db.save_risk_areas(risk_areas)
        
        return outbreaks
    
    def scrape_who_outbreaks(self) -> List[Dict]:
        """Enhanced WHO scraping with risk classification"""
        outbreaks = self.get_enhanced_outbreaks()
        return [o for o in outbreaks if 'WHO' in o['source']]
    
    def scrape_cdc_outbreaks(self) -> List[Dict]:
        """Enhanced CDC scraping with risk classification"""
        outbreaks = self.get_enhanced_outbreaks()
        return [o for o in outbreaks if 'CDC' in o['source']]
    
    def get_mock_outbreaks(self) -> List[Dict]:
        """Enhanced mock data with risk classification"""
        return self.get_enhanced_outbreaks()

# Enhanced page for pcat.py integration
def enhanced_disease_monitoring_page():
    """Enhanced disease monitoring page with MOH risk areas"""
    st.header("🌍 Enhanced Disease Outbreak Monitoring")
    
    # Initialize enhanced monitor
    monitor = EnhancedDiseaseOutbreakMonitor()
    
    # Age constraints configuration
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader("⚙️ Age Constraints")
        min_age = st.number_input("Min age (months)", min_value=0, max_value=120, value=1)
        max_age = st.number_input("Max age (months)", min_value=min_age, max_value=120, value=60)
        
        if st.button("Update Age Range"):
            if monitor.age_manager.set_age_range(min_age, max_age):
                st.success("Age range updated!")
            else:
                st.error("Invalid age range!")
        
        current_min, current_max = monitor.age_manager.get_age_range()
        st.info(f"Current: {current_min}-{current_max} months")
    
    with col1:
        st.subheader("📊 Risk Areas Status")
        
        # Enhanced refresh button
        if st.button("🔄 Refresh Enhanced Outbreak Data"):
            with st.spinner("Fetching enhanced outbreak data with risk classification..."):
                try:
                    enhanced_outbreaks = monitor.get_enhanced_outbreaks()
                    st.success(f"✅ Updated with {len(enhanced_outbreaks)} risk-classified areas")
                    
                    # Display summary
                    if enhanced_outbreaks:
                        risk_summary = {}
                        for outbreak in enhanced_outbreaks:
                            risk_level = outbreak['severity_level']
                            risk_summary[risk_level] = risk_summary.get(risk_level, 0) + 1
                        
                        st.write("**Risk Level Summary:**")
                        for level, count in risk_summary.items():
                            color = "🔴" if level == "High" else "🟡" if level == "Medium" else "🟢"
                            st.write(f"{color} {level}: {count} areas")
                            
                except Exception as e:
                    st.error(f"Error updating data: {e}")
        
        # Display enhanced outbreak data with risk levels
        outbreak_df = monitor.risk_db.get_risk_areas()
        
        if not outbreak_df.empty:
            # Risk level filtering
            risk_filter = st.selectbox("Filter by Risk Level", 
                                     ["All", "High", "Medium", "Low"])
            
            if risk_filter != "All":
                outbreak_df = outbreak_df[outbreak_df['risk_level'] == risk_filter]
            
            # Enhanced display with risk color coding
            st.subheader("🎯 Risk-Classified Disease Areas")
            
            for _, row in outbreak_df.iterrows():
                risk_color = {
                    'High': '🔴',
                    'Medium': '🟡', 
                    'Low': '🟢'
                }.get(row['risk_level'], '⚪')
                
                with st.expander(f"{risk_color} {row['location']} - {row['disease'].title()} ({row['risk_level']} Risk)"):
                    col_info1, col_info2 = st.columns(2)
                    
                    with col_info1:
                        st.write(f"**Cases:** {row['cases']}")
                        st.write(f"**Deaths:** {row['deaths']}")
                        st.write(f"**Population at Risk:** {row['population_at_risk']:,}")
                    
                    with col_info2:
                        st.write(f"**Date Reported:** {row['date_reported']}")
                        st.write(f"**Source:** {row['source_url']}")
                    
                    if row['additional_info']:
                        st.write(f"**Details:** {row['additional_info']}")
        else:
            st.info("No outbreak data available. Click 'Refresh Enhanced Outbreak Data' to fetch information.")

# Enhanced alert system with age constraints
class EnhancedAlertSystem:
    """Enhanced alert system with age-specific thresholds"""
    
    def __init__(self):
        self.age_manager = AgeConstraintManager()
        
        # Age-specific alert thresholds
        self.age_specific_thresholds = {
            'meningitis': {
                '1-12_months': {'cases': 5, 'deaths': 1},   # Infants
                '13-60_months': {'cases': 8, 'deaths': 1},  # Toddlers
            },
            'diarrhoea': {
                '1-12_months': {'cases': 15, 'deaths': 2},  # Infants more vulnerable
                '13-60_months': {'cases': 20, 'deaths': 2}, # Toddlers
            }
        }
    
    def check_age_specific_alerts(self, outbreaks: List[Dict]) -> List[Dict]:
        """Check alerts with age-specific considerations"""
        alerts = []
        min_age, max_age = self.age_manager.get_age_range()
        
        for outbreak in outbreaks:
            disease = outbreak['disease_name'].lower()
            cases = outbreak.get('cases', 0)
            deaths = outbreak.get('deaths', 0)
            
            if disease in self.age_specific_thresholds:
                # Determine age group
                if min_age <= 12:
                    age_group = '1-12_months'
                else:
                    age_group = '13-60_months'
                
                thresholds = self.age_specific_thresholds[disease][age_group]
                
                if cases >= thresholds['cases'] or deaths >= thresholds['deaths']:
                    alert = {
                        'alert_type': 'Age-Specific Disease Outbreak',
                        'disease': outbreak['disease_name'],
                        'location': outbreak['location'],
                        'severity': outbreak['severity_level'],
                        'age_group': f"{min_age}-{max_age} months",
                        'message': f"ALERT: {outbreak['disease_name']} outbreak in {outbreak['location']} - {cases} cases, {deaths} deaths (Age group: {min_age}-{max_age} months)"
                    }
                    alerts.append(alert)
        
        return alerts

# Main integration function
def run_enhanced_pcat():
    """Run the enhanced version of pcat.py with MOH risk scraper integration"""
    
    st.set_page_config(
        page_title="Enhanced Clinical Assessment Tool with MOH Risk Monitoring", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🩺 Enhanced Clinical Assessment Tool")
    st.markdown("Advanced clinical assessment with comprehensive MOH risk area monitoring")
    
    # Enhanced sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", [
        "Patient Assessment", 
        "Enhanced Disease Monitoring",  # Enhanced version
        "MOH Risk Areas",              # New dedicated page
        "Enhanced Emergency Alerts",   # Enhanced version
        "Analytics Dashboard",
        "Database Management"
    ])
    
    if page == "Enhanced Disease Monitoring":
        enhanced_disease_monitoring_page()
    elif page == "MOH Risk Areas":
        # Use the standalone Streamlit app
        create_streamlit_app()
    elif page == "Enhanced Emergency Alerts":
        enhanced_emergency_alerts_page()
    else:
        st.info(f"Page '{page}' would show the original pcat.py functionality")
        st.write("This is a demonstration of how to integrate the MOH risk scraper.")
        st.write("Replace the corresponding functions in pcat.py with the enhanced versions.")

def enhanced_emergency_alerts_page():
    """Enhanced emergency alerts with age-specific considerations"""
    st.header("🚨 Enhanced Emergency Alert System")
    
    enhanced_alert_system = EnhancedAlertSystem()
    enhanced_monitor = EnhancedDiseaseOutbreakMonitor()
    
    # Age constraint display
    min_age, max_age = enhanced_alert_system.age_manager.get_age_range()
    st.info(f"**Current Age Focus:** {min_age} - {max_age} months")
    
    # Generate enhanced alerts
    if st.button("🔍 Check for Age-Specific Alerts"):
        with st.spinner("Analyzing outbreak data for age-specific alerts..."):
            try:
                outbreak_data = enhanced_monitor.get_enhanced_outbreaks()
                
                if outbreak_data:
                    alerts = enhanced_alert_system.check_age_specific_alerts(outbreak_data)
                    
                    if alerts:
                        st.success(f"✅ {len(alerts)} age-specific alerts generated")
                        
                        for alert in alerts:
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
                                    <p><strong>Age Group:</strong> {alert['age_group']}</p>
                                    <p><strong>Message:</strong> {alert['message']}</p>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.info("No age-specific alerts at this time")
                else:
                    st.warning("No outbreak data available for alert analysis")
            except Exception as e:
                st.error(f"Error generating alerts: {e}")

# Usage instructions display
def show_integration_instructions():
    """Show instructions for integrating with existing pcat.py"""
    
    st.header("🔧 Integration Instructions")
    
    st.markdown("""
    ## How to Enhance Your Existing pcat.py
    
    ### Option 1: Replace Existing Classes
    
    1. **Replace DiseaseOutbreakMonitor class** (lines 134-293 in pcat.py):
    ```python
    from moh_risk_scraper import EnhancedMOHScraper, AgeConstraintManager
    from integration_example import EnhancedDiseaseOutbreakMonitor
    
    # Replace the existing class with:
    class DiseaseOutbreakMonitor(EnhancedDiseaseOutbreakMonitor):
        pass
    ```
    
    2. **Enhance the disease_monitoring_page function**:
    ```python
    from integration_example import enhanced_disease_monitoring_page
    
    # Replace the existing function with the enhanced version
    ```
    
    ### Option 2: Add New Pages
    
    Add new pages to your existing Streamlit app:
    ```python
    # In main() function, modify the page selection:
    page = st.sidebar.selectbox("Choose a page", [
        "Patient Assessment", 
        "Disease Monitoring",
        "MOH Risk Areas",           # New page
        "Enhanced Monitoring",      # Enhanced page
        "Emergency Alerts", 
        "Analytics Dashboard",
        "Database Management"
    ])
    
    if page == "MOH Risk Areas":
        from moh_risk_scraper import create_streamlit_app
        create_streamlit_app()
    elif page == "Enhanced Monitoring":
        from integration_example import enhanced_disease_monitoring_page
        enhanced_disease_monitoring_page()
    ```
    
    ### Option 3: Standalone Integration
    
    Run the enhanced version separately:
    ```bash
    # Run the MOH risk scraper
    streamlit run moh_risk_scraper.py
    
    # Run the integration example
    streamlit run integration_example.py
    ```
    """)

if __name__ == "__main__":
    # Show integration instructions by default
    show_integration_instructions()
    
    st.markdown("---")
    
    # Option to run the enhanced version
    if st.button("🚀 Run Enhanced Version"):
        run_enhanced_pcat()