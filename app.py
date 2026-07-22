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

    # Master Core Rule Alignment Map
    def clean_supplier_group(row):
        group = row['Supplier Group']
        supplier = str(row['Supplier Name']).strip()
        country = str(row['Survey Country']).strip()
        
        # Check if the data cell is blank/NaN
        is_blank = pd.isna(group) or str(group).strip().lower() in ['nan', '', '(blank)']
        
        # --- FRANCE ---
        if country == 'France':
            if is_blank:
                if 'Prime Insights' in supplier: return 'France_group_3'
                if 'CPX Research' in supplier: return 'France_group_2'
                if 'Tap Research' in supplier: return 'France_group_3'
            return group

        # --- UNITED KINGDOM ---
        elif country == 'United Kingdom':
            if 'Prime Insights' in supplier: 
                return 'Prime Insights API' # Explicitly isolated separate entity rule
            if is_blank or 'UK_Group_3' in str(group) or 'CPX' in supplier or 'Prodege' in supplier or 'Tap' in supplier:
                if 'Fusion' in supplier: return 'UK_Group_2'
                return 'UK_Group_3'
            return group

        # --- IRELAND ---
        elif country == 'Ireland':
            if 'Prime Insights' in supplier: 
                return 'Prime Insights API' # Match your excel screenshot mapping
            if is_blank:
                if supplier in ['AttaPoll', 'Fusion']: return 'Ireland_Group_2'
                return 'Ireland_Group_3'
            return group

        # --- ALL OTHER GLOBAL MARKETS DEFAULT AUTOMATION ---
        else:
            if is_blank:
                country_map = {'United States': 'US', 'Spain': 'Spain', 'India': 'India'}
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
    countries = ['France', 'India', 'Ireland', 'Spain', 'United Kingdom', 'United States']
    selected_country = st.selectbox("🌐 Select Market Country to View Supplier Blend Splits:", countries)
    
    if selected_country:
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
            
            # Build Table 2: Hierarchical Composite Group Summary
            st.markdown(f"## 👥 {selected_country} - Supplier Group (Composite) Summary (Completes Only)")
            st.caption("Click any group header row below to expand and view the underlying supplier breakdown.")

            # Calculate total cross-tabs for the group level
            pivot_group = pd.crosstab(country_df['Cleaned Supplier Group'], country_df['Tracking Week'])
            for w in weeks_order:
                if w not in pivot_group.columns: pivot_group[w] = 0
            pivot_group = pivot_group[weeks_order].copy()
            
            # Extract unique groups sorted cleanly, excluding the Grand Total for individual calculation loops
            unique_groups = sorted([g for g in pivot_group.index if g != 'Grand Total'])
            
            # Calculate column totals for global referencing
            grand_total_w1 = country_df[country_df['Tracking Week'] == "W1 (July 6-12)"].shape[0]
            grand_total_w2 = country_df[country_df['Tracking Week'] == "W2 (July 13-19)"].shape[0]
            grand_total_w3 = country_df[country_df['Tracking Week'] == "W3 (July 20+)"].shape[0]
            overall_total = country_df.shape[0]

            # Render each group as an expandable section panel
            for group_name in unique_groups:
                # 1. Gather group-specific volumes
                g_df = country_df[country_df['Cleaned Supplier Group'] == group_name]
                g_w1 = g_df[g_df['Tracking Week'] == "W1 (July 6-12)"].shape[0]
                g_w2 = g_df[g_df['Tracking Week'] == "W2 (July 13-19)"].shape[0]
                g_w3 = g_df[g_df['Tracking Week'] == "W3 (July 20+)"].shape[0]
                g_tot = g_df.shape[0]
                
                # Compute exact share percentages relative to the week's total market completions
                p_w1 = f"{(g_w1 / grand_total_w1 * 100):.2f}%" if grand_total_w1 > 0 else "0.00%"
                p_w2 = f"{(g_w2 / grand_total_w2 * 100):.2f}%" if grand_total_w2 > 0 else "0.00%"
                p_w3 = f"{(g_w3 / grand_total_w3 * 100):.2f}%" if grand_total_w3 > 0 else "0.00%"
                p_tot = f"{(g_tot / overall_total * 100):.2f}%" if overall_total > 0 else "0.00%"

                # 2. Render an elegant summary header block that simulates a pivot row
                header_label = f"➕ **{group_name}** ｜ W1: {g_w1} ({p_w1}) ｜ W2: {g_w2} ({p_w2}) ｜ W3: {g_w3} ({p_w3}) ｜ Total: {g_tot} ({p_tot})"
                
                with st.expander(header_label, expanded=False):
                    # 3. Inside the expander, construct the detailed nested matrix view
                    pivot_sub = pd.crosstab(g_df['Supplier Name'], g_df['Tracking Week'])
                    for w in weeks_order:
                        if w not in pivot_sub.columns: pivot_sub[w] = 0
                    pivot_sub = pivot_sub[weeks_order].copy()
                    
                    sub_table = pd.DataFrame(index=pivot_sub.index)
                    for week in weeks_order:
                        sub_table[week] = pivot_sub[week]
                        # Percentage contribution of this specific supplier relative to the WHOLE week's total
                        sub_table[f"{week} %"] = (pivot_sub[week] / (grand_total_w1 if "W1" in week else grand_total_w2 if "W2" in week else grand_total_w3) * 100).round(2).astype(str) + "%"
                    
                    sub_table['Total'] = pivot_sub.sum(axis=1)
                    sub_table['Total %'] = (sub_table['Total'] / overall_total * 100).round(2).astype(str) + "%"
                    
                    st.markdown("*Underlying Member Details:*")
                    st.dataframe(sub_table, use_container_width=True)
            
            # 4. Global Grand Summary Footer
            st.markdown("---")
            st.markdown(f"📊 **Market Grand Total Summary** ｜ **W1:** {grand_total_w1} (100%) ｜ **W2:** {grand_total_w2} (100%) ｜ **W3:** {grand_total_w3} (100%) ｜ **Overall Total:** {overall_total} (100%)")
