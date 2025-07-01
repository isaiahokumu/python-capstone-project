# MOH Risk Area Scraper 🏥

Enhanced Ministry of Health (MOH) risk area monitoring system for diarrhea and meningitis outbreaks with age-specific constraints and comprehensive Streamlit visualization.

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the repository files
# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Applications

#### Option A: Standalone MOH Risk Scraper
```bash
streamlit run moh_risk_scraper.py
```

#### Option B: Integration Example
```bash
streamlit run integration_example.py
```

#### Option C: Command Line Demo
```bash
python demo_script.py
```

## 📋 Project Overview

This project enhances the existing `pcat.py` clinical assessment tool with advanced MOH risk area monitoring capabilities:

### Key Features
- **Multi-Source Data Scraping** - MOH Kenya, Uganda, Tanzania, WHO AFRO
- **Risk Classification** - High, Medium, Low risk areas
- **Age Constraints** - Configurable 1-60 months target population
- **Interactive Visualization** - Streamlit dashboard with maps and charts
- **Database Integration** - SQLite storage for risk area data
- **Real-time Updates** - Manual and automated data refresh

### Enhanced Capabilities
- 🎯 **Age-Specific Monitoring** - Target children 1-60 months
- 🌍 **Geographic Mapping** - Interactive risk area visualization
- 📊 **Advanced Analytics** - Risk distribution and trend analysis
- 🚨 **Enhanced Alerts** - Age-specific alert thresholds
- 📱 **Responsive Interface** - Mobile-friendly Streamlit design

## 📁 File Structure

```
├── pcat.py                    # Original clinical assessment tool
├── moh_risk_scraper.py        # Enhanced MOH risk scraper
├── integration_example.py     # Integration demonstration
├── demo_script.py            # Command line demo
├── requirements.txt          # Python dependencies
├── moh_analysis_report.md    # Comprehensive analysis
└── README.md                 # This file
```

## 🔧 Integration with Existing `pcat.py`

### Method 1: Direct Integration
Replace the `DiseaseOutbreakMonitor` class in `pcat.py`:

```python
from moh_risk_scraper import EnhancedMOHScraper, AgeConstraintManager
from integration_example import EnhancedDiseaseOutbreakMonitor

class DiseaseOutbreakMonitor(EnhancedDiseaseOutbreakMonitor):
    pass
```

### Method 2: Add New Pages
Add enhanced pages to your existing Streamlit app:

```python
# In main() function
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
```

## 🎯 Age Constraint Configuration

Set target population age range:

```python
from moh_risk_scraper import AgeConstraintManager

age_manager = AgeConstraintManager()

# Set minimum age to 1 month, maximum to 60 months
age_manager.set_age_range(1, 60)

# Check if specific age is in range
is_valid = age_manager.is_age_in_range(24)  # 24 months
```

## 🌍 Risk Classification System

### Meningitis Risk Levels
- **High Risk**: ≥10 cases per 100k population OR ≥2 deaths
- **Medium Risk**: ≥5 cases per 100k population OR ≥1 death  
- **Low Risk**: <5 cases per 100k population AND <1 death

### Diarrhea Risk Levels
- **High Risk**: ≥50 cases per 100k population OR ≥5 deaths
- **Medium Risk**: ≥20 cases per 100k population OR ≥2 deaths
- **Low Risk**: <20 cases per 100k population AND <2 deaths

## 📊 Streamlit Interface Features

### Main Dashboard
- 🔄 **Real-time Data Refresh** - Manual and automatic updates
- 🔍 **Interactive Filtering** - By disease type and risk level
- 🗺️ **Geographic Mapping** - Visual risk area representation
- 📈 **Statistical Charts** - Risk distribution analysis

### Age Constraint Controls
- ⚙️ **Sidebar Configuration** - Easy age range adjustment
- ✅ **Real-time Validation** - Input validation and error handling
- 📋 **Visual Indicators** - Current age range display

### Data Visualization
1. **Risk Level Distribution** - Pie chart (High/Medium/Low)
2. **Geographic Map** - Interactive markers with risk levels
3. **Cases by Location** - Bar chart of outbreak intensity
4. **Trend Analysis** - Time-series data visualization

## 🗄️ Database Schema

Enhanced database structure for risk areas:

```sql
CREATE TABLE risk_areas (
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
);
```

## 🌐 Data Sources

### Primary Sources
- **MOH Kenya** - Official health ministry data
- **MOH Uganda** - Cross-border surveillance
- **MOH Tanzania** - Regional outbreak monitoring
- **WHO AFRO** - Regional WHO office reports

### Data Quality Features
- **Source Verification** - Multiple source cross-referencing
- **Temporal Validation** - Date-based filtering
- **Geographic Validation** - Location coordinate verification
- **Fallback Mechanisms** - Mock data when sources unavailable

## 🔒 Security & Compliance

- **Local Storage** - SQLite database for sensitive data
- **Input Validation** - Protection against injection attacks
- **Error Sanitization** - Safe error message handling
- **Web Scraping Ethics** - Respectful scraping practices

## ⚡ Performance Optimization

- **Database Caching** - Efficient data storage and retrieval
- **Rate Limiting** - Respectful web scraping
- **Memory Management** - Optimized data processing
- **Modular Architecture** - Easy scaling and maintenance

## 🧪 Testing and Validation

Run the demo script to test functionality:

```bash
python demo_script.py
```

Expected output:
- ✅ Scraper initialization
- ✅ Age constraint management
- ✅ Data scraping from multiple sources
- ✅ Database operations
- ✅ Risk classification logic

## 📚 Documentation

- **`moh_analysis_report.md`** - Comprehensive analysis and technical details
- **Code Comments** - Detailed inline documentation
- **Type Hints** - Python type annotations for clarity
- **Docstrings** - Function and class documentation

## 🚀 Future Enhancements

### Planned Features
1. **Machine Learning** - Predictive risk modeling
2. **API Integration** - RESTful API for data access
3. **Mobile App** - Native mobile application
4. **Real-time Alerts** - Push notifications

### Extension Possibilities
1. **Additional Diseases** - Expand beyond diarrhea/meningitis
2. **Advanced Analytics** - Epidemiological modeling
3. **Multi-language Support** - Localization features
4. **Export Capabilities** - PDF/Excel reporting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For questions and support:
- Review the comprehensive analysis in `moh_analysis_report.md`
- Run `python demo_script.py` for functionality testing
- Check the integration examples in `integration_example.py`

## 🎉 Acknowledgments

- Built as an enhancement to the existing `pcat.py` clinical assessment tool
- Designed for healthcare professionals in East Africa
- Focuses on children 1-60 months age group for diarrhea and meningitis monitoring

---

**Made with ❤️ for improving healthcare outcomes in East Africa**