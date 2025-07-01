#!/usr/bin/env python3
"""
Demo Script for MOH Risk Scraper
================================

This script demonstrates the functionality of the enhanced MOH risk scraper
without requiring Streamlit, useful for testing and validation.
"""

import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from moh_risk_scraper import EnhancedMOHScraper, AgeConstraintManager, RiskAreaDatabase

def demo_basic_functionality():
    """Demonstrate basic scraper functionality"""
    print("🏥 MOH Risk Scraper Demo")
    print("=" * 50)
    
    # Initialize components
    print("Initializing Enhanced MOH Scraper...")
    scraper = EnhancedMOHScraper()
    age_manager = AgeConstraintManager()
    db = RiskAreaDatabase()
    
    print(f"✅ Scraper initialized with {len(scraper.base_urls)} data sources")
    print(f"✅ Age constraints: {age_manager.get_age_range()[0]}-{age_manager.get_age_range()[1]} months")
    
    return scraper, age_manager, db

def demo_age_constraints():
    """Demonstrate age constraint functionality"""
    print("\n🎯 Age Constraint Management Demo")
    print("-" * 40)
    
    age_manager = AgeConstraintManager()
    
    # Show default range
    min_age, max_age = age_manager.get_age_range()
    print(f"Default age range: {min_age}-{max_age} months")
    
    # Test age range modification
    print("Setting age range to 6-24 months...")
    success = age_manager.set_age_range(6, 24)
    if success:
        print("✅ Age range updated successfully")
        min_age, max_age = age_manager.get_age_range()
        print(f"New age range: {min_age}-{max_age} months")
    else:
        print("❌ Failed to update age range")
    
    # Test age validation
    test_ages = [3, 12, 18, 30, 66]
    print("\nTesting age validation:")
    for age in test_ages:
        is_valid = age_manager.is_age_in_range(age)
        status = "✅" if is_valid else "❌"
        print(f"{status} {age} months: {'In range' if is_valid else 'Out of range'}")

def demo_data_scraping():
    """Demonstrate data scraping functionality"""
    print("\n🌍 Data Scraping Demo")
    print("-" * 30)
    
    scraper = EnhancedMOHScraper()
    
    print("Fetching risk areas from all sources...")
    try:
        risk_areas = scraper.get_all_risk_areas()
        print(f"✅ Retrieved {len(risk_areas)} risk areas")
        
        # Display summary
        if risk_areas:
            diseases = {}
            risk_levels = {}
            
            for area in risk_areas:
                diseases[area.disease] = diseases.get(area.disease, 0) + 1
                risk_levels[area.risk_level] = risk_levels.get(area.risk_level, 0) + 1
            
            print("\nDisease breakdown:")
            for disease, count in diseases.items():
                print(f"  📋 {disease.title()}: {count} areas")
            
            print("\nRisk level breakdown:")
            for level, count in risk_levels.items():
                emoji = "🔴" if level == "High" else "🟡" if level == "Medium" else "🟢"
                print(f"  {emoji} {level}: {count} areas")
            
            # Show detailed information for first few areas
            print("\nDetailed information for first 3 areas:")
            for i, area in enumerate(risk_areas[:3]):
                print(f"\n  Area {i+1}:")
                print(f"    Location: {area.location}")
                print(f"    Disease: {area.disease}")
                print(f"    Risk Level: {area.risk_level}")
                print(f"    Cases: {area.cases}")
                print(f"    Deaths: {area.deaths}")
                print(f"    Population at Risk: {area.population_at_risk:,}")
                print(f"    Source: {area.source_url}")
        else:
            print("❌ No risk areas retrieved")
            
    except Exception as e:
        print(f"❌ Error during scraping: {e}")

def demo_database_operations():
    """Demonstrate database operations"""
    print("\n🗄️ Database Operations Demo")
    print("-" * 35)
    
    scraper = EnhancedMOHScraper()
    db = RiskAreaDatabase()
    
    # Get and save risk areas
    print("Fetching and saving risk areas to database...")
    try:
        risk_areas = scraper.get_all_risk_areas()
        db.save_risk_areas(risk_areas)
        print(f"✅ Saved {len(risk_areas)} risk areas to database")
        
        # Retrieve and display data
        print("\nRetrieving data from database:")
        df = db.get_risk_areas()
        if not df.empty:
            print(f"✅ Retrieved {len(df)} records from database")
            print(f"Columns: {', '.join(df.columns.tolist())}")
            
            # Show statistics
            if 'risk_level' in df.columns:
                risk_counts = df['risk_level'].value_counts()
                print("\nRisk level distribution:")
                for level, count in risk_counts.items():
                    emoji = "🔴" if level == "High" else "🟡" if level == "Medium" else "🟢"
                    print(f"  {emoji} {level}: {count}")
        else:
            print("❌ No data retrieved from database")
            
    except Exception as e:
        print(f"❌ Database error: {e}")

def demo_risk_classification():
    """Demonstrate risk classification logic"""
    print("\n⚖️ Risk Classification Demo")
    print("-" * 35)
    
    scraper = EnhancedMOHScraper()
    
    # Test risk classification with different scenarios
    test_scenarios = [
        {'disease': 'meningitis', 'cases': 25, 'deaths': 3, 'expected': 'High'},
        {'disease': 'meningitis', 'cases': 8, 'deaths': 1, 'expected': 'Medium'},
        {'disease': 'meningitis', 'cases': 2, 'deaths': 0, 'expected': 'Low'},
        {'disease': 'diarrhoea', 'cases': 100, 'deaths': 6, 'expected': 'High'},
        {'disease': 'diarrhoea', 'cases': 35, 'deaths': 2, 'expected': 'Medium'},
        {'disease': 'diarrhoea', 'cases': 8, 'deaths': 0, 'expected': 'Low'},
    ]
    
    print("Testing risk classification scenarios:")
    for i, scenario in enumerate(test_scenarios, 1):
        risk_level = scraper._calculate_risk_level(
            scenario['disease'], 
            scenario['cases'], 
            scenario['deaths']
        )
        
        status = "✅" if risk_level == scenario['expected'] else "❌"
        print(f"  {status} Scenario {i}: {scenario['disease']} - "
              f"{scenario['cases']} cases, {scenario['deaths']} deaths "
              f"→ {risk_level} (expected: {scenario['expected']})")

def main():
    """Run all demo functions"""
    print(f"Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Run all demo functions
        demo_basic_functionality()
        demo_age_constraints()
        demo_data_scraping()
        demo_database_operations()
        demo_risk_classification()
        
        print("\n🎉 Demo completed successfully!")
        print("\nNext steps:")
        print("1. Run 'streamlit run moh_risk_scraper.py' for the full interface")
        print("2. Run 'streamlit run integration_example.py' for integration demo")
        print("3. See 'moh_analysis_report.md' for detailed documentation")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()