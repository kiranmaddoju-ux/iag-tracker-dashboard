import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 1. Page Configuration
st.set_page_config(page_title="IAG Global Tracker Blend Dashboard", layout="wide")

st.title("📊 IAG Global Tracker Operations Portal")
st.caption("Wave-over-Wave Supplier Blend & Composite Group Analytics")
st.markdown("---")

# 2. Sidebar - Secure Ingestion & Handover Instructions
st.sidebar.markdown("### 📥 Data Refresh Center")
uploaded_file = st.sidebar.file_uploader("Upload Refreshed CSV Data", type=["csv"])

st.sidebar.markdown("---")
st.sidebar.markdown("""
### 📋 Handover Operations Guide
1. Pull the refreshed data loop extract from the panel platform.
2. Drag and drop the raw `.csv` file directly into the uploader above.
3. The dashboard metrics, country stats, and cross-tabs will scale dynamically.
""")

# 3. Dynamic Calculation Pipeline
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, low_memory=False)
    
    # Identify the date column
    date_col = None
    for col in df.columns:
        if 'entry datetime' in col.lower() or 'ps entry' in col.lower():
            date_col = col
            break
            
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Define Weeks based on exact date boundaries
        def assign_tracking_week(row_date):
            if pd.isnull(row_date):
                return "Unknown"
            if row_date.month == 7 and 6 <= row_date.day <= 12:
                return "W1 (July 6-12)"
            elif row_date.month == 7 and 13 <= row_date.day <= 19:
                return "W2 (July 13-19)"
            elif row_date.month == 7 and row_date.day >= 20:
                return "W3 (July 20+)"
            else:
                return "Baseline/Pre-Field"
                
        df['Tracking Week'] = df[date_col].apply(assign_tracking_week)
    else:
        # Fallback if no date column found: use string matching on project names
        def fallback_week(proj_name):
            proj_str = str(proj_name).lower()
            if 'wave 1' in proj_str or 'w1' in proj_str:
                return "W1 (July 6-12)"
            elif 'wave 2' in proj_str or 'w2' in proj_str:
                return "W2 (July 13-19)"
            else:
                return "W3 (July 20+)"
        
        df['Tracking Week'] = df['Project Name'].apply(fallback_week)

    # Filter for Completes Only for the Blend calculations
    completes_only_df = df[df['Respondent Status Description'] == 'Complete'].copy()
    
    # 4. Market Selector Dropdown
    countries = sorted(completes_only_df['Survey Country'].dropna().unique().tolist())
    selected_country = st.selectbox("🌐 Select Market Country to View Supplier Blend:", countries)
    
    if selected_country:
        country_df = completes_only_df[completes_only_df['Survey Country'] == selected_country]
        
        st.markdown(f"## 🏛️ {selected_country} - Supplier Performance Breakdown (Completes Only)")
        
        # Build Table 1: Supplier Blend by Week
        if not country_df.empty:
            pivot_supp = pd.crosstab(
                country_df['Supplier Name'], 
                country_df['Tracking Week'], 
                margins=True, 
                margins_name='Grand Total'
            )
            
            # Calculate percentages just like Excel
            blend_table = pd.DataFrame()
            weeks_present = [c for c in pivot_supp.columns if c != 'Grand Total']
            
            for week in weeks_present:
                blend_table[week] = pivot_supp[week]
                total_week_completes = pivot_supp.loc['Grand Total', week]
                if total_week_completes > 0:
                    blend_table[f"{week} %"] = (pivot_supp[week] / total_week_completes * 100).round(2).astype(str) + "%"
                else:
                    blend_table[f"{week} %"] = "0.00%"
                    
            blend_table['Total'] = pivot_supp['Grand Total']
            total_global_completes = pivot_supp.loc['Grand Total', 'Grand Total']
            if total_global_completes > 0:
                blend_table['Total %'] = (pivot_supp['Grand Total'] / total_global_completes * 100).round(2).astype(str) + "%"
            else:
                blend_table['Total %'] = "0.00%"
                
            st.dataframe(blend_table, use_container_width=True)
            
            # Build Table 2: Composite Group Summary
            st.markdown(f"## 👥 {selected_country} - Supplier Group (Composite) Summary (Completes Only)")
            
            # Look for composite group columns dynamically
            group_col = None
            for col in df.columns:
                if 'group' in col.lower() or 'composite' in col.lower():
                    group_col = col
                    break
            
            if not group_col:
                # If no specific composite column exists, fallback to cleaning up tracking links or clone labels
                country_df['Supplier Group (Composite)'] = country_df['Project Name'].apply(lambda x: str(proj_name).split('-')[0] if '-' in str(x) else 'Main Blend')
                group_col = 'Supplier Group (Composite)'
                
            pivot_group = pd.crosstab(
                country_df[group_col].fillna('(blank)'), 
                country_df['Tracking Week'], 
                margins=True, 
                margins_name='Grand Total'
            )
            
            group_table = pd.DataFrame()
            for week in weeks_present:
                group_table[week] = pivot_group[week]
                total_week_g = pivot_group.loc['Grand Total', week]
                if total_week_g > 0:
                    group_table[f"{week} %"] = (pivot_group[week] / total_week_g * 100).round(2).astype(str) + "%"
                else:
                    group_table[f"{week} %"] = "0.00%"
                    
            group_table['Total'] = pivot_group['Grand Total']
            total_global_g = pivot_group.loc['Grand Total', 'Grand Total']
            if total_global_g > 0:
                group_table['Total %'] = (pivot_group['Grand Total'] / total_global_g * 100).round(2).astype(str) + "%"
            else:
                group_table['Total %'] = "0.00%"
                
            st.dataframe(group_table, use_container_width=True)
        else:
            st.warning(f"No complete data available for {selected_country} in the uploaded file yet.")

else:
    st.info("👋 Welcome! Please upload your latest tracking data loop CSV file in the left sidebar to generate the live supplier blend splits.")
