import streamlit as st
import pandas as pd
import time
import re
import random

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Mistral Asset Scout (RAG)", layout="wide", page_icon="🔍")

st.markdown("""
<style>
    .match-card { background-color: #f0f2f6; border-left: 5px solid #ff4b4b; padding: 15px; border-radius: 5px; margin-bottom: 10px; }
    .safe-card { background-color: #e8f5e9; border-left: 5px solid #28a745; padding: 15px; border-radius: 5px; }
    .metric-box { text-align: center; padding: 10px; background: white; border-radius: 8px; border: 1px solid #ddd; }
</style>
""", unsafe_allow_html=True)

# --- 1. THE "KNOWLEDGE BASE" (Simulated Vector DB) ---
# In a real app, this would be thousands of PDF contracts indexed in a Vector DB.
knowledge_base = [
    {
        "id": "CTR-2023-001",
        "title": "Global News Corp - Archive",
        "description": "20TB of text data covering global journalism, news articles, and editorials from 2010-2023. Includes metadata and author info.",
        "tags": ["text", "news", "journalism", "english"]
    },
    {
        "id": "CTR-2024-045",
        "title": "CodeNet Pro",
        "description": "Python, Java, and C++ repositories with permissive licenses. 5TB of source code for LLM training.",
        "tags": ["code", "programming", "github"]
    },
    {
        "id": "CTR-2023-089",
        "title": "French Literature Corpus",
        "description": "Digitized books and manuscripts from the 19th century. 500GB of French text.",
        "tags": ["text", "books", "french", "literature"]
    }
]

# --- 2. RAG RETRIEVAL LOGIC (Smart Simulation) ---
def perform_rag_search(query):
    """
    Simulates: Query Embedding -> Vector Search -> Top-K Retrieval
    """
    query_lower = query.lower()
    results = []
    
    # Simple keyword overlap to simulate "Semantic Similarity"
    for doc in knowledge_base:
        score = 0
        # Basic scoring logic for the demo
        if any(tag in query_lower for tag in doc['tags']):
            score += 0.3
        
        # Specific overlap scenarios for your prompts
        if "news" in query_lower and "journalism" in doc['tags']:
            score = 0.92 # High match simulation
        elif "python" in query_lower and "code" in doc['tags']:
            score = 0.85
        elif "french" in query_lower and "book" in query_lower:
             score = 0.75
            
        if score > 0:
            results.append({**doc, "score": score})
    
    # Sort by score descending
    results.sort(key=lambda x: x['score'], reverse=True)
    return results

# --- 3. SOURCE VERIFICATION ---
def verify_source(domain, license_type):
    """
    Simulates a check against a 'Trusted Domain' whitelist and License Compatibility.
    """
    # 1. Source Credibility
    trusted_domains = ["reuters.com", "arxiv.org", "github.com", "wikimedia.org", "stackexchange.com"]
    is_trusted = any(d in domain.lower() for d in trusted_domains)
    
    # 2. License Compatibility Check
    # Mistral (Commercial) cannot use Non-Commercial (CC-BY-NC) or Copyleft (GPL) easily.
    incompatible_licenses = ["CC-BY-NC", "GPL v3", "AGPL", "Unknown"]
    license_warning = license_type in incompatible_licenses
    
    # 3. KYB / Sanctions Check (Simulated)
    sanctioned_entities = ["kaspersky", "huawei-subsidiary", "darknet-data-broker", "scrape-bot.io"]
    is_sanctioned = any(s in domain.lower() for s in sanctioned_entities)
    
    return is_trusted, license_warning, is_sanctioned

# --- 4. PII Redaction ---
def redact_pii(text):
    """
    Simulates PII anonymization (e.g., swapping emails/phones for placeholders)
    before indexing, complying with GDPR/HIPAA.
    """
    # Simple Regex for demo purposes
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    
    redacted_text = re.sub(email_pattern, "[EMAIL_REDACTED]", text)
    redacted_text = re.sub(phone_pattern, "[PHONE_REDACTED]", redacted_text)
    
    return redacted_text

# --- UI LAYOUT ---

st.title("🔍 Mistral Asset Scout (RAG Prototype)")
st.caption("Retrieval-Augmented Generation for Data Redundancy Checks")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Vendor Proposal")
    st.info("Paste the dataset description from the new vendor here.")
    
    # Input Area
    input_text = st.text_area(
        "New Data Description",
        height=150,
        value="We are offering a 'Global Daily News' dataset. It contains English news articles and editorials from major publishers spanning 2015 to 2024. Cleaned and tokenized."
    )
    
    check_btn = st.button("🚀 Run Redundancy Check")

with col2:
    st.subheader("2. Knowledge Base Retrieval")
    
    if check_btn:
        with st.spinner("Embedding query & searching Vector DB..."):
            time.sleep(1.5) # Simulate RAG latency
            
            # Run the search
            matches = perform_rag_search(input_text)
            
            if not matches or matches[0]['score'] < 0.5:
                # NO CONFLICT FOUND
                st.success("✅ **Green Light:** No significant overlap found in our Asset Library.")
                st.metric("Redundancy Risk", "Low", delta="Safe to Buy")
                
            else:
                # CONFLICT FOUND
                top_match = matches[0]
                similarity_percent = int(top_match['score'] * 100)
                
                st.error(f"⚠️ **Stop! Potential Redundancy Detected**")
                
                # Visualizing the RAG Result
                st.markdown(f"""
                <div class="match-card">
                    <h4>Top Match Found: {similarity_percent}% Similarity</h4>
                    <p><b>Existing Asset:</b> {top_match['title']} ({top_match['id']})</p>
                    <p><b>Our Content:</b> <i>"{top_match['description']}"</i></p>
                    <hr>
                    <p><b>AI Analysis:</b> The vendor's proposal overlaps significantly with data we already licensed in 2023. Verify before purchasing.</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Metrics
                m1, m2 = st.columns(2)
                m1.metric("Semantic Overlap", f"{similarity_percent}%")
                m2.metric("Potential Savings", "$50k+")

# --- DEBUG VIEW (Optional) ---
with st.expander("Step 3: Quality & Compliance Verification", expanded=True):
    c1, c2 = st.columns(2)
    vendor_domain = c1.text_input("Source Domain", value="random-scraper.xyz")
    license_type = c2.selectbox("Proposed License", ["Commercial-Safe", "CC-BY-4.0", "CC-BY-NC", "GPL v3"])
    
    if st.button("🛡️ Run Compliance Audit"):
        trusted, bad_license = verify_source(vendor_domain, license_type)
        
        # 1. Domain Check Result
        if trusted:
            st.success(f"✅ **Source Verified:** '{vendor_domain}' is in our Trusted Partner Network.")
        else:
            st.warning(f"⚠️ **Unverified Source:** '{vendor_domain}' has no prior contract history. Enhanced due diligence required.")
            
        # 2. License Check Result
        if bad_license:
            st.error(f"🚫 **STOP:** '{license_type}' is incompatible with our commercial models (Viral/Copyleft Risk).")
        else:
            st.info(f"✅ **License Clear:** '{license_type}' is safe for commercial training.")

            st.markdown("---")
        st.subheader("Partner Legitimacy (KYB)")
        
        if sanctioned:
            st.error(f"🚨 **CRITICAL ALERT:** '{vendor_domain}' is flagged on the OFAC/Sanctions Watchlist. **DO NOT ENGAGE.**")
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/b/bc/Stop_hand.svg/200px-Stop_hand.svg.png", width=50) # Visual Stop
        else:
            st.success(f"✅ **Clear:** Entity passed Global Sanctions & Corporate Registry checks.")
            st.caption("Verification ID: KYB-2026-X992 | Source: Dun & Bradstreet API (Mock)")