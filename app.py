import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 1. Page Configuration & Title Styling
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
    
    # Precise timestamp tracking mapping for W1, W2, and W3
    date_col = 'PS Entry DateTime (Pacific Time Zone)'
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
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
                return "Pre-Field / Baseline"
                
        df['Tracking Week'] = df[date_col].apply(assign_tracking_week)
    else:
        st.error(f"Required date column '{date_col}' missing from uploaded file.")
        st.stop()

    # Dynamic Supplier Group Fallback Mapping (Clears up blanks natively)
    def clean_supplier_group(row):
        group = row['Supplier Group']
        supplier = str(row['Supplier Name'])
        
        # If the group is blank, fill it directly with the name of the supplier vendor
        if pd.isna(group) or str(group).strip().lower() in ['nan', '', '(blank)']:
            return supplier
        return group

    # Apply the mapping transformation layer
    df['Cleaned Supplier Group'] = df.apply(clean_supplier_group, axis=1)

    # Filter for Completes Only for the Blend calculations
    completes_only_df = df[df['Respondent Status Description'] == 'Complete'].copy()
    
    # Global Overview Metrics
    total_completes = len(completes_only_df)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.markdown("**Total Accumulated Completes**")
            st.markdown(f"### :green[{total_completes} Cases]")
            st.caption("All weeks combined")
    with col2:
        with st.container(border=True):
            st.markdown("**Active Tracker Markets**")
            st.markdown("### 6 Countries")
            st.caption("France, India, IE, ES, UK, US")
    with col3:
        with st.container(border=True):
            w3_count = len(completes_only_df[completes_only_df['Tracking Week'] == "W3 (July 20+)"])
            st.markdown("**Week 3 Completes Progress**")
            st.markdown(f"### :blue[{w3_count} Cases]")
            st.caption("Pacing from July 20 onward")

    st.markdown("---")
    
    # 4. Market Selector Dropdown (Guarantees all 6 markets are available)
    countries = ['France', 'India', 'Ireland', 'Spain', 'United Kingdom', 'United States']
    selected_country = st.selectbox("🌐 Select Market Country to View Supplier Blend Splits:", countries)
    
    if selected_country:
        country_df = completes_only_df[completes_only_df['Survey Country'] == selected_country]
        
        st.markdown(f"## 🏛️ {selected_country} - Supplier Performance Breakdown (Completes Only)")
        
        # Build Table 1: Supplier Blend by Week
        if not country_df.empty:
            weeks_order = ["W1 (July 6-12)", "W2 (July 13-19)", "W3 (July 20+)"]
            
            pivot_supp = pd.crosstab(
                country_df['Supplier Name'], 
                country_df['Tracking Week']
            )
            
            # Keep column indexes structurally intact
            for w in weeks_order:
                if w not in pivot_supp.columns:
                    pivot_supp[w] = 0
            
            pivot_supp = pivot_supp[weeks_order].copy()
            pivot_supp.loc['Grand Total'] = pivot_supp.sum()
            pivot_supp['Total'] = pivot_supp.sum(axis=1)
            
            blend_table = pd.DataFrame(index=pivot_supp.index)
            for week in weeks_order:
                blend_table[week] = pivot_supp[week]
                total_week_completes = pivot_supp.loc['Grand Total', week]
                if total_week_completes > 0:
                    blend_table[f"{week} %"] = (pivot_supp[week] / total_week_completes * 100).round(2).astype(str) + "%"
                else:
                    blend_table[f"{week} %"] = "0.00%"
                    
            blend_table['Total'] = pivot_supp['Total']
            total_global_completes = pivot_supp.loc['Grand Total', 'Total']
            if total_global_completes > 0:
                blend_table['Total %'] = (pivot_supp['Total'] / total_global_completes * 100).round(2).astype(str) + "%"
            else:
                blend_table['Total %'] = "0.00%"
                
            st.dataframe(blend_table, use_container_width=True)
            
            # Build Table 2: Composite Group Summary (Cleaned - Blanks Replaced by Vendor Name)
            st.markdown(f"## 👥 {selected_country} - Supplier Group (Composite) Summary (Completes Only)")
            
            pivot_group = pd.crosstab(
                country_df['Cleaned Supplier Group'], 
                country_df['Tracking Week']
            )
            
            for w in weeks_order:
                if w not in pivot_group.columns:
                    pivot_group[w] = 0
                    
            pivot_group = pivot_group[weeks_order].copy()
            pivot_group.loc['Grand Total'] = pivot_group.sum()
            pivot_group['Total'] = pivot_group.sum(axis=1)
            
            group_table = pd.DataFrame(index=pivot_group.index)
            for week in weeks_order:
                group_table[week] = pivot_group[week]
                total_week_g = pivot_group.loc['Grand Total', week]
                if total_week_g > 0:
                    group_table[f"{week} %"] = (pivot_group[week] / total_week_g * 100).round(2).astype(str) + "%"
                else:
                    group_table[f"{week} %"] = "0.00%"
                    
            group_table['Total'] = pivot_group['Total']
            total_global_g = pivot_group.loc['Grand Total', 'Total']
            if total_global_g > 0:
                group_table['Total %'] = (pivot_group['Total'] / total_global_g * 100).round(2).astype(str) + "%"
            else:
                group_table['Total %'] = "0.00%"
                
            st.dataframe(group_table, use_container_width=True)
        else:
            st.warning(f"No complete records currently available for {selected_country} in the uploaded loop dataset.")

else:
    st.info("👋 Welcome! Please upload your raw refreshed 'survey_All_0.csv' file in the left sidebar to render the live tracking metrics.")
