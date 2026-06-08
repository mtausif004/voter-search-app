import streamlit as st
import pandas as pd
import pytesseract
from pdf2image import convert_from_path
import re
import os
import tempfile

st.set_page_config(page_title="Voter Search System", layout="wide", page_icon="🗳️")

st.title("🗳️ Voter Search System")
st.subheader("PDF আপলোড করুন → OCR → সার্চ")

uploaded_files = st.file_uploader("PDF ফাইল আপলোড করুন", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_data = []
    progress_bar = st.progress(0)
    
    for file_idx, uploaded_file in enumerate(uploaded_files):
        with st.spinner(f"OCR চলছে: {uploaded_file.name} (এটা সময় নেবে)"):
            # টেম্পোরারি ফাইল
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name
            
            try:
                images = convert_from_path(tmp_path, dpi=250)
                
                full_text = ""
                for img in images:
                    text = pytesseract.image_to_string(img, lang='ben+eng')
                    full_text += text + "\n"
                
                # পার্সিং
                lines = full_text.split('\n')
                current = {}
                
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    
                    if re.search(r'০০\d{2}\.|^\d{4}\.', line) or "নাম:" in line:
                        if current.get("নাম"):
                            all_data.append(current)
                        current = {
                            "নাম": "", "ভোটার নং": "", "পিতা": "", "মাতা": "",
                            "পেশা": "", "জন্ম তারিখ": "", "ঠিকানা": ""
                        }
                        
                        name_m = re.search(r'নাম[:\s]+(.+?)(?=ভোটার|পিতা|$)', line)
                        voter_m = re.search(r'ভোটার নং[:\s]*(\d+)', line)
                        
                        if name_m: current["নাম"] = name_m.group(1).strip()
                        if voter_m: current["ভোটার নং"] = voter_m.group(1)
                    
                    elif "পিতা:" in line:
                        current["পিতা"] = line.split(":", 1)[-1].strip()
                    elif "মাতা:" in line:
                        current["মাতা"] = line.split(":", 1)[-1].strip()
                    elif "পশা:" in line or "পেশা:" in line:
                        current["পেশা"] = line.split(":", 1)[-1].strip()
                    elif "জন্ম তারিখ:" in line:
                        current["জন্ম তারিখ"] = line.split(":", 1)[-1].strip()
                    elif "ঠিকানা:" in line:
                        current["ঠিকানা"] = line.split(":", 1)[-1].strip()
                
                if current.get("নাম"):
                    all_data.append(current)
                    
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        
        progress_bar.progress((file_idx + 1) / len(uploaded_files))
    
    df = pd.DataFrame(all_data)
    
    if len(df) > 0:
        st.success(f"✅ মোট {len(df)} জনের তথ্য বের হয়েছে")
        
        # সার্চ
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input("নাম")
        with col2:
            voter = st.text_input("ভোটার নং")
        with col3:
            father = st.text_input("পিতার নাম")
        
        filtered = df.copy()
        if name:
            filtered = filtered[filtered["নাম"].astype(str).str.contains(name, case=False, na=False)]
        if voter:
            filtered = filtered[filtered["ভোটার নং"].astype(str).str.contains(voter, na=False)]
        if father:
            filtered = filtered[filtered["পিতা"].astype(str).str.contains(father, case=False, na=False)]
        
        st.dataframe(filtered, use_container_width=True)
        
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("📥 CSV ডাউনলোড", csv, "voter_list.csv", "text/csv")
    else:
        st.error("কোনো তথ্য বের করা যায়নি।")
