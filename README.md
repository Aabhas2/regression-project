# 🏠 Housing Price Regression Project

**An end-to-end ML product for automated regression analysis and price prediction**

## 📋 Project Overview

This project is building a comprehensive regression playground/simulator that accepts datasets, runs automated EDA and preprocessing, trains multiple regression models, and provides an interactive UI for model comparison and predictions.

### 🎯 Current Focus
**Housing Price Prediction** using Delhi/NCR real estate data with automated feature engineering and model comparison.

---

## 🚀 Project Phases

### ✅ **MVP**
- [x] **Project Structure**: Clean organization with data, notebooks, and source directories
- [x] **Data Collection**: Web scraping pipeline for housing.com (12K+ properties)
- [x] **EDA & Analysis**: Comprehensive exploratory data analysis in Jupyter notebooks
- [x] **Data Preprocessing**: Missing value handling, outlier detection, feature engineering
- [ ] **Model Training**: Multiple regression algorithms with hyperparameter tuning
- [ ] **Model Comparison**: Metrics comparison (MAE, RMSE, R²) and visualization
- [ ] **Basic UI**: Streamlit interface for predictions
---

## 📊 Current Status

### **Data Pipeline**
- **Dataset Size**: 12,000+ housing properties
- **Features**: Price, BHK, Area, Location, Parking, Age
- **Data Quality**: ~85% clean data after preprocessing
- **Source**: Real-time scraping from housing.com

### **Features Implemented**
- ✅ Web scraping with Selenium + BeautifulSoup
- ✅ Data cleaning and validation
- ✅ Missing value imputation
- ✅ Outlier detection and removal
- ✅ Feature engineering (price categories, efficiency metrics)
- ✅ Correlation analysis and visualization

### **Models to Implement**
- [ ] Linear Regression
- [ ] Ridge Regression  
- [ ] Lasso Regression
- [ ] ElasticNet
- [ ] K-Nearest Neighbors
- [ ] Polynomial Regression
- [ ] Random Forest (stretch)

---

## 🗂️ Project Structure

```
regression-project/
├── 📁 data/
│   ├── raw.csv                 # Raw scraped data
│   ├── housing_cleaned.csv     # Cleaned dataset
│   └── housing_processed.csv   # Feature engineered data
├── 📁 notebooks/
│   └── EDA.ipynb              # Exploratory Data Analysis
├── 📁 src/
│   └── regression-project/
│       └── data/
│           └── scrape_housing.py  # Web scraping pipeline
├── 📁 interface/              # UI components (planned)
├── 📁 reports/               # Analysis reports (planned)
├── 📄 requirements.txt       # Python dependencies
├── 📄 environment.yml        # Conda environment
└── 📄 README.md              # This file
```

---

## 🛠️ Technologies Used

### **Data Collection & Processing**
- **Selenium** - Web scraping automation
- **BeautifulSoup** - HTML parsing
- **Pandas** - Data manipulation
- **NumPy** - Numerical computing

### **Analysis & Visualization**
- **Matplotlib** - Static plotting
- **Seaborn** - Statistical visualization
- **Jupyter** - Interactive analysis

### **Machine Learning**
- **Scikit-learn** - ML algorithms and preprocessing
- **GridSearchCV** - Hyperparameter tuning

---

## 📈 Key Findings (So Far)

### **Data Insights**
- **Price Range**: ₹10 Lakh - ₹50 Crore
- **Most Common**: 2-3 BHK properties
- **Average Area**: ~1,200 sq ft
- **Price/Sqft**: ₹2,000 - ₹40,000 (Delhi/NCR)

### **Feature Correlations**
- **Area ↔ Price**: Strong positive correlation (0.7+)
- **BHK ↔ Price**: Moderate correlation (0.5+)
- **Parking ↔ Price**: Weak positive correlation

### **Data Quality**
- **Missing Values**: Successfully handled using median/mode imputation
- **Outliers**: Identified and filtered using domain knowledge
- **Consistency**: Price format standardized (lakhs vs crores)

---

## 🚀 Quick Start

### **Environment Setup**
```bash
# Clone repository
git clone <repository-url>
cd regression-project

# Create conda environment
conda env create -f environment.yml
conda activate regression-env

# Install additional dependencies
pip install -r requirements.txt
```

### **Run Analysis**
```bash
# Start Jupyter notebook
jupyter notebook notebooks/EDA.ipynb

# Run data scraping (optional)
python src/regression-project/data/scrape_housing.py
```

---

## 📝 Notes

- **Dataset Updates**: Scraper can be run periodically for fresh data
- **Model Performance Target**: R² > 0.85 for housing price prediction
- **Reproducibility**: All preprocessing steps documented and automated

---

**Status**: Active Development  
**Last Updated**: October 2025

---

*This README will be updated as the project progresses through different phases.*
