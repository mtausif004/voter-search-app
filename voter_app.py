import streamlit as st
import pdfplumber
import pandas as pd
import re

st.set_page_config(page_title="Voter Search System", layout="wide", page_icon="🗳️")

st.title("🗳️ Voter Search System")
st.subheader("বাংলাদেশ নির্বাচন কমিশন — যেকোনো এলাকার ভোটার লিস্ট")

uploaded_files = st.file_uploader("PDF আপলোড করুন (একাধিক)", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_data = []
    progress_bar = st.progress(0)
    
    for file_idx, uploaded_file in enumerate(uploaded_files):
        with st.spinner(f"প্রসেস হচ্ছে: {uploaded_file.name}"):
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    # ভালো টেক্সট এক্সট্রাকশন সেটিং
                    text = page.extract_text(x_tolerance=3, y_tolerance=5, layout=True) or ""
                    lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 5]
                    
                    i = 0
                    while i < len(lines):
                        line = lines[i]
                        
                        # ভোটার এন্ট্রি শুরু ডিটেক্ট
                        if re.search(r'০০\d{2}\.|নাম:', line) or re.search(r'^\d{4}\.', line):
                            entry = {
                                "সিরিয়াল": len(all_data) + 1,
                                "নাম": "",
                                "ভোটার নং": "",
                                "পিতা": "",
                                "মাতা": "",
                                "পেশা": "",
                                "জন্ম তারিখ": "",
                                "ঠিকানা": ""
                            }
                            
                            # নাম ও ভোটার নং
                            name_match = re.search(r'নাম[:\s]+(.+?)(?=ভোটার নং|পিতা|মাতা|পেশা|$)', line, re.DOTALL)
                            voter_match = re.search(r'ভোটার নং[:\s]*(\d+)', line)
                            
                            if name_match:
                                entry["নাম"] = name_match.group(1).strip()
                            if voter_match:
                                entry["ভোটার নং"] = voter_match.group(1)
                            
                            # পরবর্তী লাইন থেকে তথ্য সংগ্রহ
                            i += 1
                            buffer = ""
                            while i < len(lines) and not re.search(r'০০\d{2}\.|^\d{4}\.', lines[i]):
                                nl = lines[i]
                                buffer += " " + nl
                                
                                if 'পিতা:' in nl:
                                    entry["পিতা"] = re.split(r'পিতা[:\s]+', nl, 1)[-1].strip()
                                elif 'মাতা:' in nl:
                                    entry["মাতা"] = re.split(r'মাতা[:\s]+', nl, 1)[-1].strip()
                                elif 'পশা:' in nl or 'পেশা:' in nl:
                                    entry["পেশা"] = re.split(r'পশা[:\s]+|পেশা[:\s]+', nl, 1)[-1].strip()
                                elif 'জন্ম তারিখ:' in nl or 'জন্ম তািরখ:' in nl:
                                    entry["জন্ম তারিখ"] = re.split(r'জন্ম তারিখ[:\s]+', nl, 1)[-1].strip()
                                elif 'ঠিকানা:' in nl:
                                    entry["ঠিকানা"] = re.split(r'ঠিকানা[:\s]+', nl, 1)[-1].strip()
                                i += 1
                            
                            # ঠিকানা যদি খালি থাকে তাহলে বাকি টেক্সট নাও
                            if not entry["ঠিকানা"] and buffer:
                                entry["ঠিকানা"] = buffer.strip()[:200]
                            
                            if entry["নাম"] or entry["ভোটার নং"]:
                                all_data.append(entry)
                            continue
                        i += 1
                    
        progress_bar.progress((file_idx + 1) / len(uploaded_files))
    
    df = pd.DataFrame(all_data)
    
    if len(df) > 0:
        st.success(f"✅ **{len(df)}** জন ভোটারের তথ্য সফলভাবে লোড হয়েছে")
        
        # সার্চ বক্স
        st.markdown("### 🔍 অনুসন্ধান করুন")
        col1, col2 = st.columns(2)
        with col1:
            name_search = st.text_input("নাম")
            father_search = st.text_input("পিতার নাম")
        with col2:
            voter_search = st.text_input("ভোটার নং")
        
        # ফিল্টার
        mask = pd.Series([True] * len(df))
        if name_search: mask &= df["নাম"].str.contains(name_search, case=False, na=False)
        if voter_search: mask &= df["ভোটার নং"].astype(str).str.contains(voter_search, na=False)
        if father_search: mask &= df["পিতা"].str.contains(father_search, case=False, na=False)
        
        filtered = df[mask].copy()
        
        st.info(f"**ফলাফল:** {len(filtered)} জন")
        
        # সুন্দর কার্ড
        for _, row in filtered.iterrows():
            st.markdown(f"""
            <div style="background:white; padding:20px; border-radius:12px; margin:12px 0; box-shadow:0 4px 15px rgba(0,0,0,0.1);">
                <h4>{row['নাম']}</h4>
                <b>ভোটার নং:</b> {row['ভোটার নং']}<br>
                <b>পিতা:</b> {row['পিতা']}<br>
                <b>মাতা:</b> {row['মাতা']}<br>
                <b>পেশা:</b> {row['পেশা']}<br>
                <b>জন্ম তারিখ:</b> {row['জন্ম তারিখ']}<br>
                <b>ঠিকানা:</b> {row['ঠিকানা']}
            </div>
            """, unsafe_allow_html=True)
        
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("📥 সম্পূর্ণ লিস্ট CSV ডাউনলোড", csv, "voter_list.csv", "text/csv")
    else:
        st.warning("কোনো তথ্য পাওয়া যায়নি। অন্য PDF চেষ্টা করুন।")
