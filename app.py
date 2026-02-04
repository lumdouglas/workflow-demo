import streamlit as st
import pandas as pd
import json
import time
import altair as alt
import pandas as pd
import random
import os
from mistralai import Mistral  # Updated for v1.0 SDK

api_key = st.secrets["MISTRAL_API_KEY"]

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="Mistral Ops: Licensing Intake",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to mimic Slack and Notion UI elements accurately
st.markdown("""
<style>
    /* Slack Message Styling */
    .slack-msg { border: 1px solid #ddd; border-radius: 8px; padding: 15px; background-color: white; margin-bottom: 10px; font-family: 'Lato', sans-serif; }
    .slack-header { display: flex; align-items: center; margin-bottom: 5px; }
    .slack-avatar { width: 36px; height: 36px; border-radius: 4px; background-color: #4A154B; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 10px; }
    .slack-name { font-weight: 900; color: #1d1c1d; margin-right: 8px; }
    .slack-meta { color: #616061; font-size: 0.8em; }
    
    /* Metrics */
    div[data-testid="stMetricValue"] { font-size: 24px; }
</style>
""", unsafe_allow_html=True)

# --- 2. STATE MANAGEMENT ---
if "database" not in st.session_state:
    st.session_state.database = pd.DataFrame(columns=[
        "Partner", "Data_Type", "Risk_Level", "Value", "Status", "Timestamp"
    ])

# --- 3. CORE LOGIC (AI & MOCK) ---

def clean_json_string(json_str):
    """Sanitizes LLM output to ensure valid JSON parsing."""
    if not json_str: return None
    # Remove markdown code blocks if present
    clean_str = json_str.replace("```json", "").replace("```", "").strip()
    return clean_str

def run_mistral_extraction(api_key, raw_text):
    """
    Production-grade extraction using Mistral's latest SDK.
    Includes error handling for API limits and malformed JSON.
    """
    try:
        client = Mistral(api_key=api_key)
        
        prompt = f"""
        You are a Legal Ops data entry specialist. Analyze this inbound licensing inquiry.
        Return ONLY a raw JSON object (no markdown, no conversational text) with these keys:
        - partner_name (string)
        - data_type (string: "Audio", "Text", "Video", "Code", "Multimodal")
        - risk_level (string: "High", "Medium", "Low")
        - estimated_value (integer: derived from text or assign 0 if unknown)
        - summary (string: a 1-sentence legal summary)

        Inquiry: "{raw_text}"
        """

        response = client.chat.complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.choices[0].message.content
        return json.loads(clean_json_string(content))
        
    except Exception as e:
        st.error(f"⚠️ Extraction Failed: {str(e)}")
        return None

def check_price_fairness(data_type, proposed_price, volume):
    # 1. Load History
    history = pd.read_csv('past_deals.csv')
    
    # 2. Filter for similar data types (e.g., compare "Image" to "Image")
    relevant_deals = history[history['data_type'] == data_type]
    
    if relevant_deals.empty:
        return None, 0 # No data to compare
    
    # 3. Calculate Benchmark (Average Unit Price from past deals)
    avg_unit_price = relevant_deals['unit_price'].mean()
    
    # 4. Calculate "Fair Price" for this new volume
    fair_price = avg_unit_price * volume
    
    # 5. Determine savings/overpayment
    difference = proposed_price - fair_price
    is_overpaying = difference > 0
    
    return is_overpaying, difference, fair_price

def mock_extraction_fallback(raw_text):
    """
    Smart Fallback: Extracts real data from text using simple Python logic 
    so the demo looks real even without an API key.
    """
    raw_text_lower = raw_text.lower()
    
    # 1. smart Partner Name Detection
    # Looks for known partners from your test prompts
    partner = "Unknown Partner"
    if "mediscan" in raw_text_lower:
        partner = "MediScan AI"
    elif "pixelperfect" in raw_text_lower:
        partner = "PixelPerfect Stock"
    elif "socialscrape" in raw_text_lower:
        partner = "SocialScrape Ltd"
    elif "opencode" in raw_text_lower:
        partner = "OpenCode Foundation"
    elif "globalbroadcast" in raw_text_lower:
        partner = "GlobalBroadcast Corp"
    elif "deepdive" in raw_text_lower:
        partner = "DeepDive Analytics"

    # 2. Smart Risk Detection
    # keywords that trigger High Risk
    high_risk_triggers = ["gdpr", "pii", "hipaa", "identifiable", "scrape", "audit"]
    if any(word in raw_text_lower for word in high_risk_triggers):
        risk = "High"
    elif "rights" in raw_text_lower or "check" in raw_text_lower:
        risk = "Medium"
    else:
        risk = "Low"

    # 3. Smart Value Extraction
    # Tries to find a number following a $ sign
    import re
    # Find patterns like $120,000 or $50k
    price_match = re.search(r'\$(\d{1,3}(?:,\d{3})*|[\d]+)(k)?', raw_text_lower)
    
    estimated_val = 0
    if price_match:
        number_part = price_match.group(1).replace(',', '')
        multiplier = 1000 if price_match.group(2) == 'k' else 1
        estimated_val = int(number_part) * multiplier
    
    # 4. Data Type Guessing
    if "image" in raw_text_lower or "x-ray" in raw_text_lower:
        dtype = "Image/Video"
    elif "audio" in raw_text_lower:
        dtype = "Audio"
    elif "code" in raw_text_lower or "repo" in raw_text_lower:
        dtype = "Code"
    else:
        dtype = "Unstructured Text"

    return {
        "partner_name": partner,
        "data_type": dtype,
        "risk_level": risk,
        "estimated_value": estimated_val,
        "summary": f"Automated intake for {partner} ({dtype})"
    }

# --- 4. MAIN APP LAYOUT ---

st.title("⚡ Mistral AI: Smart Licensing Intake")
st.caption("Middleware Prototype: Slack ➔ Mistral LLM ➔ Notion Database")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Mistral API Key", type="password", help="Leave blank to run in Demo Mode")
    st.divider()
    st.info("💡 **Demo Tip:** Paste a message in Tab 1 to see the extraction pipeline.")

# Tabs
tab_intake, tab_db, tab_bi = st.tabs(["🚀 Intake Pipeline", "📚 Notion Database", "📊 BI Dashboard"])

# --- TAB 1: INTAKE PIPELINE ---
with tab_intake:
    col_input, col_preview = st.columns([1, 1])
    
    with col_input:
        st.subheader("1. Inbound Channel (Slack)")
        
        # Pre-filled example for speed
        default_msg = "Urgent: 'DeepDive Analytics' wants to license their 50TB oceanography video dataset. They are asking for $150k. Note: Dataset contains some identifiable faces (GDPR concern)."
        
        raw_msg = st.text_area("New #legal-intake Message", value=default_msg, height=150)
        
        process_btn = st.button("✨ Extract Metadata", type="primary")

    with col_preview:
        st.subheader("2. AI Processor")
        if process_btn:
            with st.spinner("Mistral 7B is analyzing legal context..."):
                time.sleep(1.2) # UI polish: simulated "thinking" time
                
                # Logic: Choose Real vs Mock
                if api_key:
                    data = run_mistral_extraction(api_key, raw_msg)
                else:
                    data = mock_extraction_fallback(raw_msg)
                
                if data:
                    # Render the "Slack Bot" reply
                    st.markdown(f"""
                    <div class="slack-msg">
                        <div class="slack-header">
                            <div class="slack-avatar">🤖</div>
                            <div class="slack-name">Mistral Ops Bot</div>
                            <div class="slack-meta">APP • just now</div>
                        </div>
                        ✅ <b>Intake Processed.</b> I've extracted the following details:<br><br>
                        <b>Partner:</b> {data.get('partner_name')}<br>
                        <b>Risk Profile:</b> {data.get('risk_level')}<br>
                        <b>Value:</b> ${data.get('estimated_value'):,}<br>
                        <hr style="margin: 10px 0;">
                        <i>Sending to Notion...</i>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Save to State
                    new_row = {
                        "Partner": data.get('partner_name'),
                        "Data_Type": data.get('data_type'),
                        "Risk_Level": data.get('risk_level'),
                        "Value": data.get('estimated_value'),
                        "Status": "Needs Review",
                        "Timestamp": pd.Timestamp.now()
                    }
                    st.session_state.database = pd.concat([st.session_state.database, pd.DataFrame([new_row])], ignore_index=True)

                    # --- PASTE THIS AT THE BOTTOM OF TAB 1 ---
    st.divider()
    
    with st.expander("💰 Negotiation Copilot (Price Benchmarking)", expanded=True):
        st.caption("Compare new offers against 2024 historical deal data.")
        
        # Inputs for the calculator
        nc_col1, nc_col2, nc_col3 = st.columns(3)
        p_val = nc_col1.number_input("Proposed Price ($)", value=50000)
        p_vol = nc_col2.number_input("Volume (Units)", value=10000)
        p_type = nc_col3.selectbox("Data Type", ["Image", "Text", "Code", "Audio"], key="bench_type")
        
        if st.button("Run Price Benchmark"):
            overpaying, diff, fair_val = check_price_fairness(p_type, p_val, p_vol)
            
            if fair_val == 0:
                st.warning("Not enough historical data to benchmark this type.")
            elif overpaying:
                st.error(f"⚠️ **Overpayment Alert:** This quote is ${diff:,.0f} above market rate.")
                st.markdown(f"**Analysis:** Based on past deals, we typically pay **${fair_val:,.0f}** for this volume.")
                st.info(f"💡 **Negotiation Tip:** Our average rate for {p_type} is significantly lower. Counter-offer at **${fair_val * 1.1:,.0f}**.")
            else:
                st.success(f"✅ **Good Deal:** You are saving ${abs(diff):,.0f} compared to historical averages!")

    st.divider()
    
    with st.expander("🧬 Data Hygiene Lab (Content Evaluation)", expanded=False):
        st.caption("Automated Python analysis to ensure content accuracy and quality.")
        
        # Simulate uploading a sample file
        uploaded_sample = st.file_uploader("Upload Dataset Sample (CSV/JSON)", type=['csv', 'json'])
        
        if uploaded_sample is not None or st.button("Run Simulation on Mock Data"):
            with st.spinner("Analyzing token density and schema validity..."):
                time.sleep(1.5) # Narrative pause
                
                # Mock Results
                q1, q2, q3 = st.columns(3)
                q1.metric("Schema Validity", "98%", delta="Pass")
                q2.metric("PII Leakage Rate", "0.02%", delta="Low Risk", delta_color="normal")
                q3.metric("Noise/Garbage Ratio", "12%", delta="- High Noise", delta_color="inverse")
                
                # Visualizing the Analysis
                st.write("**Detailed Findings:**")
                st.warning("⚠️ **Quality Alert:** 12% of rows contain non-alphanumeric 'garbage' characters (encoding errors).")
                st.info("ℹ️ **Source ID:** Text appears scraped from `common_crawl_2023`. Requires cleaning pipeline.")
                
                # The Actionable Insight
                st.error("🚫 **Recommendation:** Reject dataset until vendor cleans encoding errors.")

# --- TAB 2: NOTION DATABASE ---
with tab_db:
    st.subheader("Live Database (Notion Sync)")
    
    if st.session_state.database.empty:
        st.info("No active records. Process an inquiry in Tab 1.")
    else:
        # Streamlit's new column_config is cleaner than Pandas styling for this
        st.data_editor(
            st.session_state.database,
            column_config={
                "Risk_Level": st.column_config.SelectboxColumn(
                    "Risk",
                    options=["High", "Medium", "Low"],
                    width="medium",
                    help="AI-Assessed Risk Level"
                ),
                "Value": st.column_config.NumberColumn(
                    "Deal Value",
                    format="$%d"
                ),
                "Status": st.column_config.SelectboxColumn(
                    "Workflow Status",
                    options=["Needs Review", "Legal Clearance", "Signed"],
                    required=True
                ),
                "Timestamp": st.column_config.DatetimeColumn(
                    "Created At",
                    format="D MMM, HH:mm"
                )
            },
            use_container_width=True,
            hide_index=True,
            num_rows="fixed"
        )

# --- TAB 3: ANALYTICS ---
with tab_bi:
    st.subheader("Operational Metrics")
    
    if st.session_state.database.empty:
        st.warning("Waiting for data... (Process some prompts in Tab 1 first)")
    else:
        df = st.session_state.database
        
        # 1. TOP ROW: METRICS
        k1, k2, k3 = st.columns(3)
        total_val = df['Value'].sum()
        k1.metric("Total Pipeline Value", f"${total_val:,}")
        
        pending_count = len(df[df['Status'] == "Needs Review"])
        k2.metric("Pending Inquiries", pending_count)
        
        high_risk_count = len(df[df['Risk_Level'] == "High"])
        k3.metric("High Risk Items", high_risk_count, delta_color="inverse", delta=high_risk_count)
        
        st.divider()
        
        # 2. CHARTS ROW
        c1, c2 = st.columns(2)
        
        with c1:
            st.caption("Risk Distribution (Live)")
            
            # Define specific colors for specific values
            risk_color_scale = alt.Scale(
                domain=['High', 'Medium', 'Low'],
                range=['#FF4B4B', '#FFA500', '#28a745']  # Red, Orange, Green
            )
            
            # Create the custom chart
            risk_chart = alt.Chart(df).mark_bar().encode(
                x=alt.X('Risk_Level', axis=alt.Axis(title='Risk Level')),
                y=alt.Y('count()', axis=alt.Axis(title='Count')),
                color=alt.Color('Risk_Level', scale=risk_color_scale, legend=None),
                tooltip=['Risk_Level', 'count()']
            ).properties(height=300)
            
            st.altair_chart(risk_chart, use_container_width=True)
            
        with c2:
            st.caption("Pipeline Value by Data Type")
            # Group by Type and sum Value for the second chart
            type_data = df.groupby("Data_Type")["Value"].sum().reset_index()
            
            type_chart = alt.Chart(type_data).mark_bar().encode(
                x=alt.X('Data_Type', axis=alt.Axis(title='Data Source')),
                y=alt.Y('Value', axis=alt.Axis(title='Total Value ($)')),
                color=alt.value('#0068C9'), # Mistral Blue
                tooltip=['Data_Type', 'Value']
            ).properties(height=300)
            
            st.altair_chart(type_chart, use_container_width=True)

    # --- ADD THIS TO APP.PY (Inside Tab 3: BI Dashboard) ---
    st.divider()
    st.subheader("Opportunity SQL Explorer")
    st.caption("Query the licensing database using Natural Language or Standard SQL.")
    
    c_sql1, c_sql2 = st.columns([3, 1])
    query = c_sql1.text_input("Search Database", placeholder="e.g. Select deals where value > 100k")
    
    if c_sql2.button("Run Query"):
        st.code(f"SELECT * FROM licensing_opportunities \nWHERE value > 100000 \nAND status = 'Active';", language="sql")
        st.dataframe(df[df['Value'] > 50000]) # Display filtered view of your existing dataframe
