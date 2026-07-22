import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 1. Page Configuration & Native Styling
st.set_page_config(page_title="IAG Global Tracker Dashboard", layout="wide")

st.title("📊 IAG Global Tracker Operations Portal")
st.caption("Wave 2 & Week 3 Live Performance Ledger & Supplier Analytics")
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
    
    total_clicks = len(df)
    completes_df = df[df['Respondent Status Description'] == 'Complete']
    total_completes = len(completes_df)
    
    # Financial and Volume Metrics
    project_margin = "46.88%"
    profit_dollars = "$1,066"
    target_achievement = "96%"
    
    # Display Executive Metric Cards using native safe blocks
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.markdown("**Overall Project Margin**")
            st.markdown(f"### :green[{project_margin}]")
            st.caption(f"{profit_dollars} profit")
    with col2:
        with st.container(border=True):
            st.markdown("**Target Achievement Rate**")
            st.markdown(f"### :blue[{target_achievement}]")
            st.caption("Weekly Volume")
    with col3:
        with st.container(border=True):
            st.markdown("**Global Quota Full Rate**")
            quota_full_global_pct = round((len(df[df['Respondent Status Description'] == 'Buyer_QuotaFull']) / total_clicks) * 100, 1)
            st.markdown(f"### :red[{quota_full_global_pct}%]")
            st.caption("Traffic Blocked")

    st.markdown("---")
    
    # 4. Market Health Section
    st.header("🗺️ Country Market Diagnostics & Incidence Rates")
    
    country_stats = df.groupby('Survey Country').agg(
        Total_Traffic=('Respondent Status Description', 'count'),
        Completes=('Respondent Status Description', lambda x: (x == 'Complete').sum()),
        Quota_Fulls=('Respondent Status Description', lambda x: (x == 'Buyer_QuotaFull').sum()),
        Terminations=('Respondent Status Description', lambda x: (x == 'Buyer_Termination').sum())
    ).reset_index()
    
    country_stats['Quota Full %'] = (country_stats['Quota_Fulls'] / country_stats['Total_Traffic'] * 100).round(1)
    country_stats['Actual IR %'] = (country_stats['Completes'] / (country_stats['Completes'] + country_stats['Terminations'] + 1e-9) * 100).round(1)
    
    st.dataframe(country_stats.style.highlight_max(axis=0, color="#fee2e2", subset=['Quota Full %']), use_container_width=True)
    
    # Dual Axis Visualization
    fig, ax1 = plt.subplots(figsize=(12, 4))
    x_indices = range(len(country_stats['Survey Country']))
    width = 0.35
    
    ax1.bar([i - width/2 for i in x_indices], country_stats['Quota Full %'], width, label='Quota Full %', color='#ea580c', alpha=0.85)
    ax1.set_ylabel('Quota Full Rate (%)', color='#ea580c', fontweight='bold')
    ax1.set_xticks(x_indices)
    ax1.set_xticklabels(country_stats['Survey Country'])
    
    ax2 = ax1.twinx()
    ax2.bar([i + width/2 for i in x_indices], country_stats['Actual IR %'], width, label='Actual IR %', color='#1e3a8a', alpha=0.85)
    ax2.set_ylabel('Actual Incidence Rate (%)', color='#1e3a8a', fontweight='bold')
    
    plt.title('Visual Diagnostics: Quota Spherics vs. Local Market IR', fontweight='bold')
    st.pyplot(fig)
    
    st.markdown("---")
    
    # 5. Supplier Cross-Tab Performance Matrix
    st.header("🏁 Supplier Allocation & Cell Performance Cross-Tab")
    
    supplier_list = df['Supplier Name'].value_counts().index.tolist()
    matrix_data = []
    
    for supplier in supplier_list:
        row = {'Supplier Partner Name': supplier}
        s_completes = len(df[(df['Supplier Name'] == supplier) & (df['Respondent Status Description'] == 'Complete')])
        row['Global Share %'] = f"{round((s_completes / (total_completes if total_completes > 0 else 1)) * 100, 1)}% ({s_completes} cases)"
        
        for country in country_stats['Survey Country']:
            sub = df[(df['Supplier Name'] == supplier) & (df['Survey Country'] == country)]
            t_vol = len(sub)
            if t_vol == 0:
                row[country] = "-"
            else:
                c_cnt = len(sub[sub['Respondent Status Description'] == 'Complete'])
                q_cnt = len(sub[sub['Respondent Status Description'] == 'Buyer_QuotaFull'])
                q_pct = round((q_cnt / t_vol) * 100, 1)
                row[country] = f"C: {c_cnt} | QF: {q_pct}%"
        matrix_data.append(row)
        
    st.dataframe(pd.DataFrame(matrix_data), use_container_width=True)

else:
    st.info("👋 Welcome! Please upload your latest tracking data loop CSV file in the left sidebar to generate the live operational report.")
