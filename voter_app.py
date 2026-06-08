import streamlit as st
import pandas as pd
from pdf2image import convert_from_path
import pytesseract
import re
import os
from datetime import datetime
import database as db

st.set_page_config(page_title="Voter Pro", layout="wide")
st.title("🗳️ Voter Pro - PDF OCR + Database + Search")

# Sidebar
st.sidebar.header("মেনু")
page = st.sidebar.selectbox("পেজ সিলেক্ট করুন", ["PDF আপলোড & OCR", "লাইভ সার্চ", "ডাটাবেস দেখুন"])

if page == "PDF আপলোড & OCR":
    uploaded_files = st.file_uploader("PDF আপলোড করুন", type="pdf", accept_multiple_files=True)
    
    if uploaded_files and st.button("OCR চালিয়ে ডাটাবেসে সেভ করুন"):
        for uploaded_file in uploaded_files:
            with st.spinner(f"প্রসেস হচ্ছে: {uploaded_file.name}"):
                # টেম্পোরারি সেভ
                with open("temp.pdf", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                images = convert_from_path("temp.pdf", dpi=300)
                full_text = ""
                for img in images:
                    text = pytesseract.image_to_string(img, lang='ben')
                    full_text += text + "\n"
                
                # Parsing Logic (আরও উন্নত)
                data = []
                lines = full_text.split('\n')
                current = None
                
                for line in lines:
                    line = line.strip()
                    if re.search(r'০০\d{2}\.|^\d{4}\.', line) or "নাম:" in line:
                        if current and current.get("নাম"):
                            data.append(current)
                        current = {"serial": len(data)+1, "name": "", "voter_no": "", "father": "", 
                                  "mother": "", "occupation": "", "dob": "", "address": ""}
                        
                        name = re.search(r'নাম[:\s]+(.+?)(?=ভোটার|পিতা|$)', line)
                        voter = re.search(r'ভোটার নং[:\s]*(\d+)', line)
                        if name: current["name"] = name.group(1).strip()
                        if voter: current["voter_no"] = voter.group(1)
                    
                    elif "পিতা:" in line: current["father"] = line.split(":",1)[-1].strip()
                    elif "মাতা:" in line: current["mother"] = line.split(":",1)[-1].strip()
                    elif "পশা:" in line or "পেশা:" in line: current["occupation"] = line.split(":",1)[-1].strip()
                    elif "জন্ম তারিখ:" in line: current["dob"] = line.split(":",1)[-1].strip()
                    elif "ঠিকানা:" in line: current["address"] = line.split(":",1)[-1].strip()
                
                if current and current.get("name"):
                    data.append(current)
                
                df = pd.DataFrame(data)
                db.save_to_db(df, uploaded_file.name)
                st.success(f"{uploaded_file.name} → {len(df)} জন সেভ হয়েছে")
                
                os.remove("temp.pdf")

elif page == "লাইভ সার্চ":
    query = st.text_input("নাম / ভোটার নং / পিতা লিখুন")
    if query:
        result = db.search_voters(query)
        st.dataframe(result, use_container_width=True)

elif page == "ডাটাবেস দেখুন":
    conn = sqlite3.connect('voters.db')
    df = pd.read_sql_query("SELECT * FROM voters ORDER BY pdf_name, serial", conn)
    st.dataframe(df, use_container_width=True)
    conn.close()
