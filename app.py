import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 1. Page Configuration & Setup
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

    # Dynamic Supplier Group Fallback Mapping (Master Alignment Map)
    def clean_supplier_group(row):
        group = row['Supplier Group']
        supplier = str(row['Supplier Name']).strip()
        country = str(row['Survey Country']).strip()
        
        # Check if the data cell is blank/NaN
        is_blank = pd.isna(group) or str(group).strip().lower() in ['nan', '', '(blank)']
        
        # --- FRANCE SPECIFIC ALIGNMENT ---
        if country == 'France':
            if 'Prime Insights' in supplier:
                return 'Prime Insights API'
            if 'CPX Research' in supplier or 'Prodege' in supplier:
                return 'France_group_2'
            # Force all remaining non-prime suppliers into group_3_Group MP
            return 'France_group_3_Group MP'

        # --- UNITED STATES SPECIFIC ALIGNMENT ---
        elif country == 'United States':
            if 'Prime Insights' in supplier:
                return 'Prime Insights API'
            if 'Social Loop' in supplier:
                return 'Social Loop'
            return 'US_Group_3'

        # --- INDIA SPECIFIC ALIGNMENT ---
        elif country == 'India':
            if 'Prime Insights' in supplier:
                return 'Prime Insights API'
            if is_blank or 'Group MP' in str(group) or supplier in ['Fusion', 'Prodege & Bitburst - Supplier', 'Rakuten - Supplier', 'Tap Research', 'Aspen Analytics', 'Persona.ly']:
                return 'Group MP'
            if 'India_Group_2' in str(group) or supplier in ['AttaPoll', 'CPX Research']:
                return 'India_Group_2'
            return group

        # --- UNITED KINGDOM ---
        elif country == 'United Kingdom':
            if 'Prime Insights' in supplier: 
                return 'Prime Insights API'
            if is_blank or 'UK_Group_3' in str(group) or 'CPX' in supplier or 'Prodege' in supplier or 'Tap' in supplier:
                if 'Fusion' in supplier: return 'UK_Group_2'
                return 'UK_Group_3'
            return group

        # --- IRELAND ---
        elif country == 'Ireland':
            if 'Prime Insights' in supplier: 
                return 'Prime Insights API'
            if is_blank:
                if supplier in ['AttaPoll', 'Fusion']: return 'Ireland_Group_2'
                return 'Ireland_Group_3'
            return group

        # --- OTHER MARKETS FALLBACKS (Spain, etc.) ---
        else:
            if is_blank:
                country_map = {'Spain': 'Spain'}
                c_code = country_map.get(country, country)
                if 'Prime Insights' in supplier: return f"{c_code}_Group_MP"
                return f"{c_code}_Group_3"
            return group

    # Execute custom clean mapping layer
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
    
    # 4. Market Selector Dropdown
    countries_options = ['Overall / All Markets', 'France', 'India', 'Ireland', 'Spain', 'United Kingdom', 'United States']
    selected_country = st.selectbox("🌐 Select Market Country to View Supplier Blend Splits:", countries_options)
    
    if selected_country:
        if selected_country == 'Overall / All Markets':
            country_df = completes_only_df
            st.markdown(f"## 🏛️ Global Overview - Supplier Performance Breakdown (All Markets Combined)")
        else:
            country_df = completes_only_df[completes_only_df['Survey Country'] == selected_country]
            st.markdown(f"## 🏛️ {selected_country} - Supplier Performance Breakdown (Completes Only)")
        
        if not country_df.empty:
            weeks_order = ["W1 (July 6-12)", "W2 (July 13-19)", "W3 (July 20+)"]
            
            # Build Table 1: Supplier Name Pivot
            pivot_supp = pd.crosstab(country_df['Supplier Name'], country_df['Tracking Week'])
            for w in weeks_order:
                if w not in pivot_supp.columns: pivot_supp[w] = 0
                    
            pivot_supp = pivot_supp[weeks_order].copy()
            pivot_supp.loc['Grand Total'] = pivot_supp.sum()
            pivot_supp['Total'] = pivot_supp.sum(axis=1)
            
            blend_table = pd.DataFrame(index=pivot_supp.index)
            for week in weeks_order:
                blend_table[week] = pivot_supp[week]
                tot = pivot_supp.loc['Grand Total', week]
                blend_table[f"{week} %"] = (pivot_supp[week] / tot * 100).round(2).astype(str) + "%" if tot > 0 else "0.00%"
                    
            blend_table['Total'] = pivot_supp['Total']
            tot_glob = pivot_supp.loc['Grand Total', 'Total']
            blend_table['Total %'] = (pivot_supp['Total'] / tot_glob * 100).round(2).astype(str) + "%" if tot_glob > 0 else "0.00%"
            st.dataframe(blend_table, use_container_width=True)
            
            # Build Table 2: Composite Summary Table (Clean & Simple)
            if selected_country == 'Overall / All Markets':
                st.markdown(f"## 👥 Global Overview - Supplier Group Summary (All Markets Combined)")
            else:
                st.markdown(f"## 👥 {selected_country} - Supplier Group (Composite) Summary (Completes Only)")
                
            pivot_group = pd.crosstab(country_df['Cleaned Supplier Group'], country_df['Tracking Week'])
            for w in weeks_order:
                if w not in pivot_group.columns: pivot_group[w] = 0
                    
            pivot_group = pivot_group[weeks_order].copy()
            pivot_group.loc['Grand Total'] = pivot_group.sum()
            pivot_group['Total'] = pivot_group.sum(axis=1)
            
            group_table = pd.DataFrame(index=pivot_group.index)
            for week in weeks_order:
                group_table[week] = pivot_group[week]
                tot_g = pivot_group.loc['Grand Total', week]
                group_table[f"{week} %"] = (pivot_group[week] / tot_g * 100).round(2).astype(str) + "%" if tot_g > 0 else "0.00%"
                    
            group_table['Total'] = pivot_group['Total']
            tot_gg = pivot_group.loc['Grand Total', 'Total']
            group_table['Total %'] = (pivot_group['Total'] / tot_gg * 100).round(2).astype(str) + "%" if tot_gg > 0 else "0.00%"
            st.dataframe(group_table, use_container_width=True)
            
            # --- SIMPLE HIERARCHY KEY LIST ---
            st.markdown("### 🔍 Live Group Membership Reference")
            unique_groups_list = sorted([g for g in country_df['Cleaned Supplier Group'].unique() if pd.notna(g)])
            
            for group_item in unique_groups_list:
                associated_suppliers = sorted(country_df[country_df['Cleaned Supplier Group'] == group_item]['Supplier Name'].unique())
                suppliers_str = ", ".join(associated_suppliers)
                st.markdown(f"📦 **{group_item}** contains: *{suppliers_str}*")
                
            st.markdown("---")
            
            # --- PRE-DEFINED INTERNAL MASTER EXCEL LOOKUP ---
            if selected_country == 'Overall / All Markets':
                st.markdown(f"📋 **Global Overview - All Pre-Defined Internal Allocation Reference Rules**")
            else:
                st.markdown(f"📋 **{selected_country} - Pre-Defined Internal Allocation Reference Rules**")
            
            try:
                try:
                    import openpyxl
                except ImportError:
                    import subprocess
                    import sys
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
                
                master_excel = pd.read_excel("internal_master_rules.xlsx", header=None)
                master_excel[0] = master_excel[0].ffill()
                
                if selected_country == 'Overall / All Markets':
                    matched_rows = master_excel.dropna(subset=[1, 2, 3])
                else:
                    matched_rows = master_excel[master_excel[0].astype(str).str.strip().str.lower() == selected_country.lower()]
                
                if not matched_rows.empty:
                    sub_data = []
                    headers = ["Country", "Group Assignments", "supNm", "Allocation"] if selected_country == 'Overall / All Markets' else ["Group Assignments", "supNm", "Allocation"]
                    
                    for idx, row in matched_rows.iterrows():
                        val_a = str(row[0]).strip()
                        val_b = str(row[1]).strip()
                        val_c = str(row[2]).strip()
                        val_d = str(row[3]).strip()
                        
                        if val_b.lower() == "group assignments" or (val_b == "nan" and val_c == "nan" and val_d == "nan"):
                            continue
                            
                        disp_a = "" if val_a == "nan" else val_a
                        disp_b = "" if val_b == "nan" else val_b
                        disp_c = "" if val_c == "nan" else val_c
                        
                        disp_d = ""
                        if val_d != "nan":
                            try:
                                num_val = float(val_d)
                                if num_val <= 1.0:
                                    disp_d = f"{num_val * 100:.0f}%"
                                else:
                                    disp_d = f"{num_val:.0f}%"
                            except ValueError:
                                disp_d = val_d if "%" in val_d else f"{val_d}%"
                        
                        if selected_country == 'Overall / All Markets':
                            sub_data.append([disp_a, disp_b, disp_c, disp_d])
                        else:
                            sub_data.append([disp_b, disp_c, disp_d])
                        
                    if sub_data:
                        reference_df = pd.DataFrame(sub_data, columns=headers)
                        st.dataframe(reference_df, use_container_width=True, hide_index=True)
                    else:
                        st.info(f"ℹ--------- Internal master allocation reference data is empty.")
                else:
                    st.info(f"ℹ--------- No internal target rules are currently listed in the master Excel sheet.")
                    
            except FileNotFoundError:
                st.info("💡 **Operational Note:** To display your master definitions here, name your created workbook `internal_master_rules.xlsx` and push it to your GitHub directory right next to `app.py`!")
                
        else:
            st.warning(f"No complete records currently available in the uploaded dataset.")
else:
    st.info("👋 Welcome! Please upload your tracking data CSV file in the left sidebar to generate the live supplier blend splits.")
