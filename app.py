import streamlit as st
import requests
import pandas as pd

# --- Configuration ---
# This points to your local FastAPI server. 
# (If you deploy the API to a cloud service later, you just change this URL)
API_URL = "http://127.0.0.1:8000/recommend"

st.set_page_config(
    page_title="SHL Assessment Recommender",
    page_icon="🎯",
    layout="wide"
)

# --- UI Header ---
st.title("🎯 SHL Assessment Recommendation Engine")
st.markdown("""
Welcome to the intelligent HR assessment routing tool. 
Enter a natural language query or paste a full Job Description below, and the AI will analyze the required **Technical** and **Behavioral** skills to recommend the perfect suite of tests.
""")

# --- Input Section ---
query = st.text_area(
    "Job Description / Requirements Query:",
    height=150,
    placeholder="e.g., I am hiring for Java developers who can also collaborate effectively with my business teams. Looking for an assessment(s) that can be completed in 40 minutes."
)

# --- Action Button & API Call ---
if st.button("Get Recommendations", type="primary"):
    if not query.strip():
        st.warning("⚠️ Please enter a job description or query first.")
    else:
        with st.spinner("🤖 AI is analyzing requirements and searching the SHL catalog..."):
            try:
                # Send the POST request to your FastAPI backend
                response = requests.post(API_URL, json={"query": query})
                
                if response.status_code == 200:
                    results = response.json()
                    
                    if results:
                        st.success(f"✅ Found {len(results)} highly relevant recommendations!")
                        
                        # Convert the JSON list of dictionaries into a Pandas DataFrame
                        df = pd.DataFrame(results)
                        
                        # Display the data in a clean, interactive tabular format
                        st.dataframe(
                            df,
                            column_config={
                                "name": "Assessment Name",
                                "url": st.column_config.LinkColumn("SHL Catalog URL"),
                                "test_types": "Category",
                                "duration": "Duration (Mins)",
                                "remote_support": "Remote",
                                "adaptive_support": "Adaptive"
                            },
                            hide_index=True,
                            use_container_width=True
                        )
                    else:
                        st.info("No assessments found matching those exact strict criteria. Try broadening your search.")
                        
                else:
                    st.error(f"❌ API Error {response.status_code}: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("🚨 Failed to connect to the backend. Please ensure your FastAPI server is running (`python api.py`).")

# --- Footer ---
st.markdown("---")
st.caption("Powered by LangChain, Groq (Llama 3), ChromaDB, and FastAPI.")