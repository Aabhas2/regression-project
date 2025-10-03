# Identify and analyze data quality issues
print("=== DATA QUALITY ISSUES ANALYSIS ===\n")

# 1. Price inconsistencies
print("1. PRICE ISSUES:")
price_issues = df[df['price'].notna()]

# Extremely low prices (likely data entry errors)
low_price = price_issues[price_issues['price'] < 1000]
print(f"Extremely low prices (< ₹1000): {len(low_price)}")
if len(low_price) > 0:
    print(low_price[['listing_id', 'title', 'price', 'price_text']].head())

# Extremely high prices (potential outliers)
high_price = price_issues[price_issues['price'] > 500000000]  # > 50 Cr
print(f"\nExtremely high prices (> ₹50 Cr): {len(high_price)}")
if len(high_price) > 0:
    print(high_price[['listing_id', 'title', 'price', 'price_text']].head())

print(f"\n2. AREA ISSUES:")
# Missing area data
area_missing = df['area_sqft'].isna().sum()
print(f"Missing area data: {area_missing} ({area_missing/len(df)*100:.1f}%)")

# Check price_per_sqft for unrealistic values
if 'price_per_sqft' in df.columns:
    valid_price_per_sqft = df['price_per_sqft'].dropna()
    print(f"Valid price per sqft entries: {len(valid_price_per_sqft)}")
    print(f"Price per sqft range: ₹{valid_price_per_sqft.min():.0f} to ₹{valid_price_per_sqft.max():.0f}")
    
    # Unrealistic price per sqft
    unrealistic_low = (df['price_per_sqft'] < 100).sum()
    unrealistic_high = (df['price_per_sqft'] > 100000).sum()
    print(f"Unrealistically low price/sqft (< ₹100): {unrealistic_low}")
    print(f"Unrealistically high price/sqft (> ₹100,000): {unrealistic_high}")

print(f"\n3. TEXT PARSING ISSUES:")
# Check price_text and area_text for parsing problems
print("Price text samples with issues:")
price_text_issues = df[df['price_text'].str.contains('.ft', na=False)]
print(f"Entries with '.ft' in price_text: {len(price_text_issues)}")

print("\nArea text samples:")
print(df['area_text'].value_counts().head())


# COMPREHENSIVE DATA PROCESSING PIPELINE

def clean_housing_data(df_raw):
    """
    Comprehensive data cleaning pipeline for housing dataset
    """
    df = df_raw.copy()
    print("Starting data cleaning pipeline...")
    print(f"Initial dataset shape: {df.shape}")
    
    # Step 1: Handle missing area data
    print("\n=== STEP 1: AREA DATA CLEANING ===")
    
    # Remove entries where both area_sqft and area_text are missing
    before_area_filter = len(df)
    df = df.dropna(subset=['area_sqft', 'area_text'], how='all')
    print(f"Removed {before_area_filter - len(df)} entries missing both area fields")
    
    # Try to extract area from area_text where area_sqft is missing
    missing_area_mask = df['area_sqft'].isna()
    print(f"Entries with missing area_sqft: {missing_area_mask.sum()}")
    
    # Step 2: Clean price data
    print("\n=== STEP 2: PRICE DATA CLEANING ===")
    
    # Remove entries with missing price
    before_price_filter = len(df)
    df = df.dropna(subset=['price'])
    print(f"Removed {before_price_filter - len(df)} entries with missing price")
    
    # Remove unrealistic prices
    before_price_clean = len(df)
    df = df[(df['price'] >= 100000) & (df['price'] <= 1000000000)]  # 1 Lakh to 100 Cr
    print(f"Removed {before_price_clean - len(df)} entries with unrealistic prices")
    
    # Step 3: Clean BHK data
    print("\n=== STEP 3: BHK DATA CLEANING ===")
    
    # Remove entries with missing or unrealistic BHK
    before_bhk = len(df)
    df = df[(df['bhk'].notna()) & (df['bhk'] >= 1) & (df['bhk'] <= 10)]
    print(f"Removed {before_bhk - len(df)} entries with invalid BHK")
    
    # Step 4: Calculate and validate price per sqft
    print("\n=== STEP 4: PRICE PER SQFT VALIDATION ===")
    
    # Recalculate price per sqft
    df['price_per_sqft_calculated'] = df['price'] / df['area_sqft']
    
    # Remove entries with unrealistic price per sqft
    before_psqft = len(df)
    valid_psqft_mask = (df['price_per_sqft_calculated'] >= 500) & (df['price_per_sqft_calculated'] <= 150000)
    df = df[valid_psqft_mask | df['area_sqft'].isna()]
    print(f"Removed {before_psqft - len(df)} entries with unrealistic price per sqft")
    
    # Step 5: Standardize location names
    print("\n=== STEP 5: LOCATION STANDARDIZATION ===")
    
    # Clean and standardize location names
    if 'location' in df.columns:
        df['location_clean'] = df['location'].str.strip().str.title()
        df['location_clean'] = df['location_clean'].str.replace(r'Sector\s+(\d+)', r'Sector \1', regex=True)
        
        # Group small locations together
        location_counts = df['location_clean'].value_counts()
        rare_locations = location_counts[location_counts < 5].index
        df.loc[df['location_clean'].isin(rare_locations), 'location_clean'] = 'Other'
        
        print(f"Standardized {df['location_clean'].nunique()} unique locations")
    
    print(f"\nFinal dataset shape: {df.shape}")
    print(f"Data reduction: {((len(df_raw) - len(df)) / len(df_raw) * 100):.1f}%")
    
    return df

# Apply the cleaning pipeline
df_cleaned = clean_housing_data(df)


# FEATURE ENGINEERING PIPELINE

def engineer_features(df):
    """
    Create new features for better model performance
    """
    df = df.copy()
    print("=== FEATURE ENGINEERING ===")
    
    # 1. Price-based features
    df['price_in_crores'] = df['price'] / 10000000
    df['price_category'] = pd.cut(df['price'], 
                                 bins=[0, 2500000, 5000000, 10000000, 25000000, float('inf')],
                                 labels=['Budget', 'Mid-Range', 'Premium', 'Luxury', 'Ultra-Luxury'])
    
    # 2. Area-based features
    df['area_category'] = pd.cut(df['area_sqft'], 
                                bins=[0, 800, 1200, 1800, 2500, float('inf')],
                                labels=['Compact', 'Medium', 'Large', 'Very Large', 'Mansion'])
    
    # 3. Location-based features
    if 'location_clean' in df.columns:
        # Create location type based on sector patterns
        df['is_sector'] = df['location_clean'].str.contains('Sector', na=False)
        df['location_type'] = df['location_clean'].apply(lambda x: 
            'Sector' if pd.notna(x) and 'Sector' in str(x) else 
            'Named Area' if pd.notna(x) else 'Unknown')
    
    # 4. Derived ratios
    df['price_per_bhk'] = df['price'] / df['bhk']
    
    # 5. Property type indicators
    df['has_parking'] = (df['parking'] > 0).astype(int)
    df['is_new_property'] = (df['age_years'] <= 1).astype(int)
    
    # 6. Interaction features
    df['bhk_area_ratio'] = df['bhk'] / df['area_sqft'] * 1000  # BHK per 1000 sqft
    
    print(f"Added {len([col for col in df.columns if col not in ['listing_id', 'title', 'price_text', 'area_text']])} engineered features")
    
    return df

# Apply feature engineering
df_engineered = engineer_features(df_cleaned)

# FINAL DATA QUALITY CHECK AND CORRELATION ANALYSIS

print("=== FINAL DATASET SUMMARY ===")
print(f"Final dataset shape: {df_engineered.shape}")
print(f"\nNumerical features summary:")
numerical_cols = df_engineered.select_dtypes(include=[np.number]).columns
print(df_engineered[numerical_cols].describe())

print(f"\nCategorical features summary:")
categorical_cols = df_engineered.select_dtypes(include=['object', 'category']).columns
for col in categorical_cols:
    if col not in ['listing_id', 'title', 'price_text', 'area_text']:
        print(f"\n{col}: {df_engineered[col].nunique()} unique values")
        print(df_engineered[col].value_counts().head(3))

# Correlation analysis
plt.figure(figsize=(12, 10))
correlation_matrix = df_engineered[numerical_cols].corr()
mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
sns.heatmap(correlation_matrix, mask=mask, annot=True, cmap='coolwarm', center=0,
            square=True, linewidths=0.5, cbar_kws={"shrink": .8})
plt.title('Feature Correlation Matrix')
plt.tight_layout()
plt.show()

# Identify highly correlated features
high_corr_pairs = []
for i in range(len(correlation_matrix.columns)):
    for j in range(i+1, len(correlation_matrix.columns)):
        if abs(correlation_matrix.iloc[i, j]) > 0.8:
            high_corr_pairs.append((correlation_matrix.columns[i], 
                                  correlation_matrix.columns[j], 
                                  correlation_matrix.iloc[i, j]))

print(f"\nHighly correlated feature pairs (|r| > 0.8):")
for pair in high_corr_pairs:
    print(f"{pair[0]} <-> {pair[1]}: {pair[2]:.3f}")


# 5. DATA QUALITY ISSUES AND RECOMMENDATIONS
print("\n5. DATA QUALITY ASSESSMENT:")

# Price per sqft calculation and validation
df['price_per_sqft'] = df['price'] / df['area_sqft']
print(f"\nPrice per sq ft analysis:")
print(df['price_per_sqft'].describe())

# Identify unrealistic price per sqft
unrealistic_low = df[df['price_per_sqft'] < 1000]  # Less than ₹1000/sqft
unrealistic_high = df[df['price_per_sqft'] > 50000]  # More than ₹50000/sqft
print(f"Unrealistically low price/sqft (<₹1000): {len(unrealistic_low)} ({len(unrealistic_low)/len(df)*100:.1f}%)")
print(f"Unrealistically high price/sqft (>₹50000): {len(unrealistic_high)} ({len(unrealistic_high)/len(df)*100:.1f}%)")

# Area vs BHK relationship check
print(f"\nArea vs BHK Analysis:")
area_per_bhk = df.groupby('bhk')['area_sqft'].agg(['mean', 'median', 'std'])
print(area_per_bhk)

# Identify potential data issues
area_bhk_issues = []
for bhk in df['bhk'].unique():
    if not pd.isna(bhk):
        bhk_data = df[df['bhk'] == bhk]['area_sqft']
        mean_area = bhk_data.mean()
        # Flag properties that are too small for their BHK count
        too_small = bhk_data[bhk_data < (bhk * 200)]  # Less than 200 sqft per room
        if len(too_small) > 0:
            area_bhk_issues.extend(too_small.index.tolist())

print(f"Properties with area-BHK mismatch: {len(area_bhk_issues)} ({len(area_bhk_issues)/len(df)*100:.1f}%)")

# PRACTICAL DATA PROCESSING IMPLEMENTATION

def advanced_data_cleaning(df):
    """
    Advanced data cleaning pipeline specifically for housing data
    """
    df_clean = df.copy()
    initial_count = len(df_clean)
    
    print("🔧 ADVANCED DATA CLEANING PIPELINE")
    print("="*50)
    
    # 1. Remove price outliers using domain knowledge
    print("\n1. PRICE OUTLIER REMOVAL:")
    # Reasonable price range for Delhi/NCR: 10 Lakh to 50 Crore
    price_mask = (df_clean['price'] >= 1000000) & (df_clean['price'] <= 500000000)
    removed_price = len(df_clean) - len(df_clean[price_mask])
    df_clean = df_clean[price_mask]
    print(f"   Removed {removed_price} properties with unrealistic prices")
    
    # 2. Remove area outliers
    print("\n2. AREA OUTLIER REMOVAL:")
    # Reasonable area range: 200 to 10000 sq ft
    area_mask = (df_clean['area_sqft'] >= 200) & (df_clean['area_sqft'] <= 10000)
    removed_area = len(df_clean) - len(df_clean[area_mask])
    df_clean = df_clean[area_mask]
    print(f"   Removed {removed_area} properties with unrealistic areas")
    
    # 3. Area-BHK consistency check
    print("\n3. AREA-BHK CONSISTENCY CHECK:")
    # Minimum 150 sq ft per BHK (very conservative)
    consistency_mask = df_clean['area_sqft'] >= (df_clean['bhk'] * 150)
    removed_consistency = len(df_clean) - len(df_clean[consistency_mask])
    df_clean = df_clean[consistency_mask]
    print(f"   Removed {removed_consistency} properties with area-BHK mismatch")
    
    # 4. Price per sqft validation
    print("\n4. PRICE PER SQFT VALIDATION:")
    df_clean['price_per_sqft'] = df_clean['price'] / df_clean['area_sqft']
    # Reasonable price per sqft for Delhi/NCR: ₹2000 to ₹40000
    psqft_mask = (df_clean['price_per_sqft'] >= 2000) & (df_clean['price_per_sqft'] <= 40000)
    removed_psqft = len(df_clean) - len(df_clean[psqft_mask])
    df_clean = df_clean[psqft_mask]
    print(f"   Removed {removed_psqft} properties with unrealistic price per sqft")
    
    # 5. BHK validation
    print("\n5. BHK VALIDATION:")
    # Reasonable BHK range: 1 to 6
    bhk_mask = (df_clean['bhk'] >= 1) & (df_clean['bhk'] <= 6)
    removed_bhk = len(df_clean) - len(df_clean[bhk_mask])
    df_clean = df_clean[bhk_mask]
    print(f"   Removed {removed_bhk} properties with invalid BHK")
    
    # Summary
    final_count = len(df_clean)
    total_removed = initial_count - final_count
    retention_rate = (final_count / initial_count) * 100
    
    print(f"\n📊 CLEANING SUMMARY:")
    print(f"   Initial records: {initial_count:,}")
    print(f"   Final records: {final_count:,}")
    print(f"   Removed: {total_removed:,} ({100-retention_rate:.1f}%)")
    print(f"   Retention rate: {retention_rate:.1f}%")
    
    return df_clean

# Apply advanced cleaning
df_cleaned_advanced = advanced_data_cleaning(df)


# FEATURE ENGINEERING FOR HOUSING REGRESSION

def create_housing_features(df):
    """
    Create comprehensive features for housing price prediction
    """
    df_features = df.copy()
    
    print("🏗️ FEATURE ENGINEERING PIPELINE")
    print("="*50)
    
    # 1. Price-based features
    print("\n1. PRICE-BASED FEATURES:")
    df_features['price_in_crores'] = df_features['price'] / 10000000
    df_features['price_category'] = pd.cut(df_features['price'], 
                                         bins=[0, 2500000, 5000000, 10000000, 25000000, float('inf')],
                                         labels=['Budget', 'Mid-Range', 'Premium', 'Luxury', 'Ultra-Luxury'])
    print(f"   ✓ Created price_in_crores and price_category")
    
    # 2. Area-based features
    print("\n2. AREA-BASED FEATURES:")
    df_features['area_category'] = pd.cut(df_features['area_sqft'], 
                                        bins=[0, 800, 1200, 1800, 2500, float('inf')],
                                        labels=['Compact', 'Medium', 'Large', 'Very Large', 'Mansion'])
    df_features['area_per_bhk'] = df_features['area_sqft'] / df_features['bhk']
    print(f"   ✓ Created area_category and area_per_bhk")
    
    # 3. Efficiency metrics
    print("\n3. EFFICIENCY METRICS:")
    df_features['price_per_bhk'] = df_features['price'] / df_features['bhk']
    df_features['price_efficiency'] = df_features['price'] / (df_features['area_sqft'] * df_features['bhk'])
    print(f"   ✓ Created price_per_bhk and price_efficiency")
    
    # 4. Property characteristics
    print("\n4. PROPERTY CHARACTERISTICS:")
    df_features['has_parking'] = (df_features['parking'] > 0).astype(int)
    df_features['parking_ratio'] = df_features['parking'] / df_features['bhk']
    df_features['luxury_score'] = (
        (df_features['area_sqft'] > 1500).astype(int) +
        (df_features['bhk'] >= 3).astype(int) +
        (df_features['parking'] > 0).astype(int) +
        (df_features['price_per_sqft'] > 8000).astype(int)
    )
    print(f"   ✓ Created has_parking, parking_ratio, and luxury_score")
    
    # 5. Market segments
    print("\n5. MARKET SEGMENTATION:")
    # Create market segments based on price and area
    df_features['market_segment'] = 'Standard'
    
    # High-end: High price OR large area
    high_end_mask = (df_features['price'] > df_features['price'].quantile(0.8)) | \
                    (df_features['area_sqft'] > df_features['area_sqft'].quantile(0.8))
    df_features.loc[high_end_mask, 'market_segment'] = 'High-End'
    
    # Budget: Low price AND small area
    budget_mask = (df_features['price'] < df_features['price'].quantile(0.3)) & \
                  (df_features['area_sqft'] < df_features['area_sqft'].quantile(0.4))
    df_features.loc[budget_mask, 'market_segment'] = 'Budget'
    
    print(f"   ✓ Created market_segment classification")
    
    # Summary
    new_features = [col for col in df_features.columns if col not in df.columns]
    print(f"\n📊 FEATURE ENGINEERING SUMMARY:")
    print(f"   Original features: {len(df.columns)}")
    print(f"   New features: {len(new_features)}")
    print(f"   Total features: {len(df_features.columns)}")
    print(f"   New features created: {new_features}")
    
    return df_features

# Apply feature engineering
df_with_features = create_housing_features(df_cleaned_advanced)


# FINAL ANALYSIS AND MODEL PREPARATION

print("📈 FINAL DATASET ANALYSIS")
print("="*50)

# Display final dataset info
print(f"\n🎯 FINAL DATASET OVERVIEW:")
print(f"   Shape: {df_with_features.shape}")
print(f"   Features: {df_with_features.columns.tolist()}")

# Correlation analysis of key features
key_numerical_features = ['price', 'bhk', 'area_sqft', 'parking', 'price_per_sqft', 
                         'area_per_bhk', 'price_per_bhk', 'luxury_score']

print(f"\n🔗 FEATURE CORRELATIONS WITH PRICE:")
price_correlations = df_with_features[key_numerical_features].corr()['price'].sort_values(key=abs, ascending=False)
print(price_correlations)

# Visualization of correlations
plt.figure(figsize=(12, 8))
correlation_matrix = df_with_features[key_numerical_features].corr()
mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
sns.heatmap(correlation_matrix, mask=mask, annot=True, cmap='RdYlBu_r', center=0,
            square=True, linewidths=0.5, cbar_kws={"shrink": .8})
plt.title('Feature Correlation Matrix (Key Features)')
plt.tight_layout()
plt.show()

# Feature distributions for final dataset
print(f"\n📊 FINAL FEATURE DISTRIBUTIONS:")

# Price distribution
print(f"\nPrice Statistics (Cleaned):")
print(df_with_features['price'].describe())

# Market segment distribution
print(f"\nMarket Segment Distribution:")
print(df_with_features['market_segment'].value_counts())

# Price category distribution
print(f"\nPrice Category Distribution:")
print(df_with_features['price_category'].value_counts())

# Final visualizations
fig, axes = plt.subplots(2, 3, figsize=(18, 12))

# Price distribution
axes[0,0].hist(df_with_features['price'], bins=50, alpha=0.7, color='skyblue', edgecolor='black')
axes[0,0].set_title('Price Distribution (Cleaned)')
axes[0,0].set_xlabel('Price (₹)')
axes[0,0].set_ylabel('Frequency')

# Area distribution  
axes[0,1].hist(df_with_features['area_sqft'], bins=50, alpha=0.7, color='lightgreen', edgecolor='black')
axes[0,1].set_title('Area Distribution (Cleaned)')
axes[0,1].set_xlabel('Area (sq ft)')
axes[0,1].set_ylabel('Frequency')

# Price per sqft distribution
axes[0,2].hist(df_with_features['price_per_sqft'], bins=50, alpha=0.7, color='salmon', edgecolor='black')
axes[0,2].set_title('Price per Sq Ft Distribution')
axes[0,2].set_xlabel('Price per Sq Ft (₹)')
axes[0,2].set_ylabel('Frequency')

# BHK distribution
df_with_features['bhk'].value_counts().sort_index().plot(kind='bar', ax=axes[1,0], color='orange', alpha=0.7)
axes[1,0].set_title('BHK Distribution')
axes[1,0].set_xlabel('BHK')
axes[1,0].set_ylabel('Count')

# Market segment distribution
df_with_features['market_segment'].value_counts().plot(kind='bar', ax=axes[1,1], color='purple', alpha=0.7)
axes[1,1].set_title('Market Segment Distribution')
axes[1,1].set_xlabel('Market Segment')
axes[1,1].set_ylabel('Count')

# Luxury score distribution
df_with_features['luxury_score'].value_counts().sort_index().plot(kind='bar', ax=axes[1,2], color='gold', alpha=0.7)
axes[1,2].set_title('Luxury Score Distribution')
axes[1,2].set_xlabel('Luxury Score')
axes[1,2].set_ylabel('Count')

plt.tight_layout()
plt.show()

# Save the processed dataset
df_with_features.to_csv('../data/housing_processed.csv', index=False)
print(f"\n💾 PROCESSED DATASET SAVED:")
print(f"   File: housing_processed.csv")
print(f"   Records: {len(df_with_features):,}")
print(f"   Features: {len(df_with_features.columns)}")
print(f"\n✅ DATA PROCESSING COMPLETE - READY FOR MODEL TRAINING!")