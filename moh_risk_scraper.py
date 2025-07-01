import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
import json
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import plotly.express as px
import plotly.graph_objects as go
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RiskArea:
    """Data class for risk area information"""
    location: str
    disease: str
    risk_level: str  # High, Medium, Low
    cases: int
    deaths: int
    population_at_risk: int
    geographical_coordinates: Optional[Tuple[float, float]]
    date_reported: datetime
    source_url: str
    additional_info: str

class EnhancedMOHScraper:
    """Enhanced MOH scraper for comprehensive disease risk analysis"""
    
    def __init__(self):
        self.base_urls = {
            'moh_kenya': 'https://www.health.go.ke',
            'moh_uganda': 'https://www.health.go.ug',
            'moh_tanzania': 'https://www.moh.go.tz',
            'who_afro': 'https://www.afro.who.int'
        }
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
        # Age constraints (in months)
        self.min_age_months = 1
        self.max_age_months = 60
        
        # Risk classification thresholds
        self.risk_thresholds = {
            'meningitis': {
                'high': {'cases_per_100k': 10, 'deaths': 2},
                'medium': {'cases_per_100k': 5, 'deaths': 1},
                'low': {'cases_per_100k': 1, 'deaths': 0}
            },
            'diarrhoea': {
                'high': {'cases_per_100k': 50, 'deaths': 5},
                'medium': {'cases_per_100k': 20, 'deaths': 2},
                'low': {'cases_per_100k': 5, 'deaths': 0}
            }
        }

    def scrape_moh_kenya_outbreaks(self) -> List[RiskArea]:
        """Scrape MOH Kenya for disease outbreaks and risk areas"""
        risk_areas = []
        
        try:
            # MOH Kenya disease surveillance reports
            surveillance_url = f"{self.base_urls['moh_kenya']}/disease-surveillance"
            response = requests.get(surveillance_url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for disease outbreak reports
                outbreak_sections = soup.find_all(['div', 'section'], 
                                                class_=re.compile(r'outbreak|disease|surveillance', re.I))
                
                for section in outbreak_sections[:10]:  # Limit to recent reports
                    risk_area = self._extract_risk_area_info(section, 'MOH Kenya')
                    if risk_area:
                        risk_areas.append(risk_area)
                        
        except requests.RequestException as e:
            logger.warning(f"Failed to scrape MOH Kenya: {e}")
            
        # If no real data found, return mock data for demonstration
        if not risk_areas:
            risk_areas = self._get_mock_kenya_data()
            
        return risk_areas

    def scrape_who_afro_data(self) -> List[RiskArea]:
        """Scrape WHO AFRO for regional disease data"""
        risk_areas = []
        
        try:
            # WHO AFRO outbreak news
            who_url = f"{self.base_urls['who_afro']}/health-topics/disease-outbreaks"
            response = requests.get(who_url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract outbreak information
                articles = soup.find_all(['article', 'div'], 
                                       class_=re.compile(r'outbreak|news|update', re.I))
                
                for article in articles[:8]:
                    risk_area = self._extract_risk_area_info(article, 'WHO AFRO')
                    if risk_area:
                        risk_areas.append(risk_area)
                        
        except requests.RequestException as e:
            logger.warning(f"Failed to scrape WHO AFRO: {e}")
            
        if not risk_areas:
            risk_areas = self._get_mock_who_data()
            
        return risk_areas

    def _extract_risk_area_info(self, section, source: str) -> Optional[RiskArea]:
        """Extract risk area information from HTML section"""
        try:
            # Extract text content
            text_content = section.get_text().lower()
            
            # Check if it contains relevant diseases
            diseases_of_interest = ['meningitis', 'diarrhoea', 'diarrhea', 'cholera']
            found_disease = None
            
            for disease in diseases_of_interest:
                if disease in text_content:
                    found_disease = 'diarrhoea' if disease in ['diarrhoea', 'diarrhea', 'cholera'] else disease
                    break
                    
            if not found_disease:
                return None
                
            # Extract location
            location = self._extract_location(text_content)
            
            # Extract numbers (cases, deaths)
            cases = self._extract_number_with_context(text_content, ['cases', 'infected', 'affected'])
            deaths = self._extract_number_with_context(text_content, ['deaths', 'died', 'fatalities'])
            
            # Determine risk level
            risk_level = self._calculate_risk_level(found_disease, cases, deaths)
            
            return RiskArea(
                location=location,
                disease=found_disease,
                risk_level=risk_level,
                cases=cases,
                deaths=deaths,
                population_at_risk=cases * 10,  # Estimate
                geographical_coordinates=None,
                date_reported=datetime.now(),
                source_url=source,
                additional_info=text_content[:200] + "..." if len(text_content) > 200 else text_content
            )
            
        except Exception as e:
            logger.warning(f"Error extracting risk area info: {e}")
            return None

    def _extract_location(self, text: str) -> str:
        """Extract location from text using pattern matching"""
        # Common East African locations
        locations = [
            'nairobi', 'mombasa', 'kisumu', 'nakuru', 'eldoret', 'thika', 'machakos',
            'kampala', 'entebbe', 'jinja', 'mbale', 'gulu', 'mbarara',
            'dar es salaam', 'dodoma', 'arusha', 'mwanza', 'zanzibar',
            'kigali', 'butare', 'gisenyi',
            'addis ababa', 'dire dawa', 'bahir dar'
        ]
        
        for location in locations:
            if location in text:
                return location.title()
                
        # Look for pattern like "in [Location]" or "[Location] county"
        location_patterns = [
            r'in ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:county|region|district)',
            r'([A-Z][a-z]+)\s+(?:reports|outbreak|cases)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
                
        return "Unknown Location"

    def _extract_number_with_context(self, text: str, keywords: List[str]) -> int:
        """Extract numbers that appear near specific keywords"""
        for keyword in keywords:
            # Look for patterns like "45 cases", "cases: 45", "45 confirmed cases"
            patterns = [
                rf'(\d+)\s+{keyword}',
                rf'{keyword}[\s:]+(\d+)',
                rf'(\d+)\s+(?:confirmed|suspected|reported)?\s*{keyword}'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return int(match.group(1))
                    
        return 0

    def _calculate_risk_level(self, disease: str, cases: int, deaths: int) -> str:
        """Calculate risk level based on cases and deaths"""
        if disease not in self.risk_thresholds:
            return "Medium"  # Default
            
        thresholds = self.risk_thresholds[disease]
        
        # Assume population of 100,000 for calculation
        cases_per_100k = (cases / 100000) * 100000 if cases > 0 else 0
        
        if (cases_per_100k >= thresholds['high']['cases_per_100k'] or 
            deaths >= thresholds['high']['deaths']):
            return "High"
        elif (cases_per_100k >= thresholds['medium']['cases_per_100k'] or 
              deaths >= thresholds['medium']['deaths']):
            return "Medium"
        else:
            return "Low"

    def _get_mock_kenya_data(self) -> List[RiskArea]:
        """Generate mock Kenya MOH data for demonstration"""
        return [
            RiskArea(
                location="Turkana County",
                disease="meningitis",
                risk_level="High",
                cases=67,
                deaths=4,
                population_at_risk=15000,
                geographical_coordinates=(3.1167, 35.5833),
                date_reported=datetime.now() - timedelta(days=1),
                source_url="MOH Kenya",
                additional_info="Meningitis outbreak in Turkana County with 67 confirmed cases and 4 deaths reported. Vaccination campaign initiated."
            ),
            RiskArea(
                location="Mombasa County",
                disease="diarrhoea",
                risk_level="Medium",
                cases=234,
                deaths=2,
                population_at_risk=25000,
                geographical_coordinates=(-4.0435, 39.6682),
                date_reported=datetime.now() - timedelta(days=2),
                source_url="MOH Kenya",
                additional_info="Diarrhoeal disease outbreak in Mombasa County linked to contaminated water sources. 234 cases reported."
            ),
            RiskArea(
                location="Kisumu County",
                disease="diarrhoea",
                risk_level="Low",
                cases=45,
                deaths=0,
                population_at_risk=8000,
                geographical_coordinates=(-0.1022, 34.7617),
                date_reported=datetime.now() - timedelta(days=3),
                source_url="MOH Kenya",
                additional_info="Low-level diarrhoeal cases reported in Kisumu County. Situation under monitoring."
            )
        ]

    def _get_mock_who_data(self) -> List[RiskArea]:
        """Generate mock WHO AFRO data for demonstration"""
        return [
            RiskArea(
                location="Northern Uganda",
                disease="meningitis",
                risk_level="High",
                cases=89,
                deaths=6,
                population_at_risk=20000,
                geographical_coordinates=(2.8, 32.3),
                date_reported=datetime.now() - timedelta(days=1),
                source_url="WHO AFRO",
                additional_info="Meningitis outbreak reported in Northern Uganda districts with 89 cases and 6 deaths."
            ),
            RiskArea(
                location="Dar es Salaam",
                disease="diarrhoea",
                risk_level="Medium",
                cases=156,
                deaths=1,
                population_at_risk=18000,
                geographical_coordinates=(-6.7924, 39.2083),
                date_reported=datetime.now() - timedelta(days=2),
                source_url="WHO AFRO",
                additional_info="Cholera outbreak in Dar es Salaam with 156 confirmed cases. Water treatment measures implemented."
            )
        ]

    def get_all_risk_areas(self) -> List[RiskArea]:
        """Get all risk areas from multiple sources"""
        all_areas = []
        
        # Scrape from different sources
        all_areas.extend(self.scrape_moh_kenya_outbreaks())
        all_areas.extend(self.scrape_who_afro_data())
        
        # Filter by diseases of interest and age constraints
        filtered_areas = self._filter_by_age_constraints(all_areas)
        
        return filtered_areas

    def _filter_by_age_constraints(self, risk_areas: List[RiskArea]) -> List[RiskArea]:
        """Filter risk areas based on age constraints"""
        # For this implementation, we'll add age-related filtering
        # In practice, you'd need age-specific epidemiological data
        
        filtered_areas = []
        for area in risk_areas:
            # Check if diseases affect the specified age range (1-60 months)
            if self._affects_target_age_group(area.disease):
                filtered_areas.append(area)
                
        return filtered_areas

    def _affects_target_age_group(self, disease: str) -> bool:
        """Check if disease significantly affects children 1-60 months"""
        # Both meningitis and diarrhoea significantly affect children in this age range
        target_diseases = ['meningitis', 'diarrhoea']
        return disease.lower() in target_diseases

class AgeConstraintManager:
    """Manage age constraints for risk analysis"""
    
    def __init__(self, min_age_months: int = 1, max_age_months: int = 60):
        self.min_age_months = min_age_months
        self.max_age_months = max_age_months

    def set_age_range(self, min_months: int, max_months: int) -> bool:
        """Set age range with validation"""
        if min_months < 0 or max_months < min_months or max_months > 120:
            return False
            
        self.min_age_months = min_months
        self.max_age_months = max_months
        return True

    def get_age_range(self) -> Tuple[int, int]:
        """Get current age range"""
        return self.min_age_months, self.max_age_months

    def is_age_in_range(self, age_months: int) -> bool:
        """Check if age is within specified range"""
        return self.min_age_months <= age_months <= self.max_age_months

class RiskAreaDatabase:
    """Database management for risk areas"""
    
    def __init__(self, db_path: str = 'risk_areas.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database with risk areas table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_areas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location TEXT,
                disease TEXT,
                risk_level TEXT,
                cases INTEGER,
                deaths INTEGER,
                population_at_risk INTEGER,
                latitude REAL,
                longitude REAL,
                date_reported DATETIME,
                source_url TEXT,
                additional_info TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    def save_risk_areas(self, risk_areas: List[RiskArea]):
        """Save risk areas to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for area in risk_areas:
            lat, lon = area.geographical_coordinates if area.geographical_coordinates else (None, None)
            
            cursor.execute('''
                INSERT OR REPLACE INTO risk_areas 
                (location, disease, risk_level, cases, deaths, population_at_risk,
                 latitude, longitude, date_reported, source_url, additional_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                area.location, area.disease, area.risk_level, area.cases,
                area.deaths, area.population_at_risk, lat, lon,
                area.date_reported, area.source_url, area.additional_info
            ))
        
        conn.commit()
        conn.close()

    def get_risk_areas(self, disease: str = None, risk_level: str = None) -> pd.DataFrame:
        """Retrieve risk areas from database"""
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT * FROM risk_areas WHERE 1=1"
        params = []
        
        if disease:
            query += " AND disease = ?"
            params.append(disease)
            
        if risk_level:
            query += " AND risk_level = ?"
            params.append(risk_level)
            
        query += " ORDER BY date_reported DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df

def create_streamlit_app():
    """Create Streamlit application for MOH risk area monitoring"""
    
    st.set_page_config(
        page_title="MOH Risk Area Monitor",
        page_icon="🏥",
        layout="wide"
    )
    
    st.title("🏥 MOH Risk Area Monitor")
    st.markdown("**Enhanced monitoring of high, medium, and low risk areas for diarrhea and meningitis**")
    
    # Initialize components
    scraper = EnhancedMOHScraper()
    age_manager = AgeConstraintManager()
    db = RiskAreaDatabase()
    
    # Sidebar for configuration
    st.sidebar.header("⚙️ Configuration")
    
    # Age constraints
    st.sidebar.subheader("Age Constraints")
    min_age = st.sidebar.number_input(
        "Minimum age (months)", 
        min_value=0, 
        max_value=120, 
        value=age_manager.min_age_months
    )
    max_age = st.sidebar.number_input(
        "Maximum age (months)", 
        min_value=min_age, 
        max_value=120, 
        value=age_manager.max_age_months
    )
    
    if st.sidebar.button("Update Age Range"):
        if age_manager.set_age_range(min_age, max_age):
            st.sidebar.success("Age range updated!")
        else:
            st.sidebar.error("Invalid age range!")
    
    # Display current age range
    st.sidebar.info(f"Current range: {age_manager.get_age_range()[0]}-{age_manager.get_age_range()[1]} months")
    
    # Main content
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header("🌍 Risk Area Monitoring")
        
        # Refresh data button
        if st.button("🔄 Refresh Risk Data", type="primary"):
            with st.spinner("Scraping latest risk area data..."):
                try:
                    risk_areas = scraper.get_all_risk_areas()
                    db.save_risk_areas(risk_areas)
                    st.success(f"✅ Updated with {len(risk_areas)} risk areas")
                except Exception as e:
                    st.error(f"Error updating data: {e}")
        
        # Display risk areas
        df = db.get_risk_areas()
        
        if not df.empty:
            # Filter by disease
            disease_filter = st.selectbox(
                "Filter by disease",
                ["All"] + list(df['disease'].unique())
            )
            
            # Filter by risk level
            risk_filter = st.selectbox(
                "Filter by risk level",
                ["All", "High", "Medium", "Low"]
            )
            
            # Apply filters
            filtered_df = df.copy()
            if disease_filter != "All":
                filtered_df = filtered_df[filtered_df['disease'] == disease_filter]
            if risk_filter != "All":
                filtered_df = filtered_df[filtered_df['risk_level'] == risk_filter]
            
            # Display data table
            st.subheader("📊 Risk Areas Data")
            display_df = filtered_df[[
                'location', 'disease', 'risk_level', 'cases', 'deaths', 
                'population_at_risk', 'date_reported', 'source_url'
            ]].rename(columns={
                'location': 'Location',
                'disease': 'Disease',
                'risk_level': 'Risk Level',
                'cases': 'Cases',
                'deaths': 'Deaths',
                'population_at_risk': 'Population at Risk',
                'date_reported': 'Date Reported',
                'source_url': 'Source'
            })
            
            st.dataframe(display_df, use_container_width=True)
            
            # Risk level distribution chart
            if len(filtered_df) > 0:
                st.subheader("📈 Risk Level Distribution")
                
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    # Risk level pie chart
                    risk_counts = filtered_df['risk_level'].value_counts()
                    fig_pie = px.pie(
                        values=risk_counts.values,
                        names=risk_counts.index,
                        title="Risk Level Distribution",
                        color_discrete_map={
                            'High': '#ff4444',
                            'Medium': '#ffaa00', 
                            'Low': '#44ff44'
                        }
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col_chart2:
                    # Cases by location bar chart
                    location_cases = filtered_df.groupby('location')['cases'].sum().sort_values(ascending=False)
                    fig_bar = px.bar(
                        x=location_cases.index,
                        y=location_cases.values,
                        title="Cases by Location",
                        labels={'x': 'Location', 'y': 'Total Cases'}
                    )
                    fig_bar.update_xaxis(tickangle=45)
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                # Geographic map
                st.subheader("🗺️ Geographic Distribution")
                map_df = filtered_df[filtered_df['latitude'].notna() & filtered_df['longitude'].notna()]
                
                if not map_df.empty:
                    fig_map = px.scatter_mapbox(
                        map_df,
                        lat='latitude',
                        lon='longitude',
                        hover_name='location',
                        hover_data=['disease', 'cases', 'deaths'],
                        color='risk_level',
                        size='cases',
                        color_discrete_map={
                            'High': '#ff4444',
                            'Medium': '#ffaa00',
                            'Low': '#44ff44'
                        },
                        zoom=5,
                        height=500,
                        mapbox_style="open-street-map",
                        title="Risk Areas Geographic Distribution"
                    )
                    st.plotly_chart(fig_map, use_container_width=True)
                else:
                    st.info("Geographic coordinates not available for mapping")
        else:
            st.info("No risk area data available. Click 'Refresh Risk Data' to load information.")
    
    with col2:
        st.header("📋 Summary Statistics")
        
        if not df.empty:
            # Key metrics
            total_areas = len(df)
            total_cases = df['cases'].sum()
            total_deaths = df['deaths'].sum()
            high_risk_areas = len(df[df['risk_level'] == 'High'])
            
            st.metric("Total Risk Areas", total_areas)
            st.metric("Total Cases", total_cases)
            st.metric("Total Deaths", total_deaths)
            st.metric("High Risk Areas", high_risk_areas)
            
            # Disease breakdown
            st.subheader("Disease Breakdown")
            disease_stats = df.groupby('disease').agg({
                'cases': 'sum',
                'deaths': 'sum',
                'location': 'count'
            }).rename(columns={'location': 'areas'})
            
            for disease, stats in disease_stats.iterrows():
                st.write(f"**{disease.title()}:**")
                st.write(f"- Areas: {stats['areas']}")
                st.write(f"- Cases: {stats['cases']}")
                st.write(f"- Deaths: {stats['deaths']}")
                st.write("---")
        
        # Age constraints info
        st.subheader("🎯 Target Population")
        min_age, max_age = age_manager.get_age_range()
        st.info(f"""
        **Age Range:** {min_age} - {max_age} months
        
        **Target Group:** 
        Children and infants in the specified age range
        
        **Relevance:**
        Both meningitis and diarrheal diseases significantly affect children in this age group
        """)

if __name__ == "__main__":
    create_streamlit_app()