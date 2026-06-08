import streamlit as st
import pdfplumber
import pandas as pd
import re

st.set_page_config(page_title="Voter Search System", layout="centered", page_icon="🗳️")

st.title("🗳️ Voter Search System")
st.markdown("**মধ্য এওচিয়া — ভোটার তথ্য অনুসন্ধান**")

uploaded_files = st.file_uploader("PDF আপলোড করুন", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_data = []
    progress_bar = st.progress(0)
    
    for file_idx, uploaded_file in enumerate(uploaded_files):
        with st.spinner(f"প্রসেস হচ্ছে: {uploaded_file.name}"):
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    
                    i = 0
                    while i < len(lines):
                        line = lines[i]
                        # আরও ফ্লেক্সিবল ডিটেকশন
                        if re.search(r'০০\d{2}\.', line) or "নাম:" in line or re.search(r'^\d{4}\.', line):
                            try:
                                # নাম বের করার চেষ্টা
                                name_match = re.search(r'নাম[:\s]+(.+?)(?=ভোটার নং|পিতা|মাতা|$)', line)
                                voter_match = re.search(r'ভোটার নং[:\s]*(\d+)', line)
                                
                                father = mother = occ = dob = addr = ""
                                i += 1
                                while i < len(lines) and not re.search(r'০০\d{2}\.', lines[i]):
                                    nl = lines[i]
                                    if 'পিতা:' in nl or 'পিতা :' in nl:
                                        father = re.split(r'পিতা[:\s]+', nl)[-1].strip()
                                    elif 'মাতা:' in nl or 'মাতা :' in nl:
                                        mother = re.split(r'মাতা[:\s]+', nl)[-1].strip()
                                    elif 'পশা:' in nl or 'পেশা:' in nl:
                                        occ = re.split(r'পশা[:\s]+|পেশা[:\s]+', nl)[-1].strip()
                                    elif 'জন্ম তারিখ:' in nl:
                                        dob = re.split(r'জন্ম তারিখ[:\s]+', nl)[-1].strip()
                                    elif 'ঠিকানা:' in nl:
                                        addr = re.split(r'ঠিকানা[:\s]+', nl)[-1].strip()
                                    i += 1
                                
                                name = name_match.group(1).strip() if name_match else ""
                                voter_no = voter_match.group(1) if voter_match else ""
                                
                                if name or voter_no:
                                    all_data.append({
                                        "নাম": name,
                                        "ভোটার নং": voter_no,
                                        "পিতা": father,
                                        "মাতা": mother,
                                        "পেশা": occ,
                                        "জন্ম তারিখ": dob,
                                        "ঠিকানা": addr
                                    })
                                continue
                            except:
                                pass
                        i += 1
        progress_bar.progress((file_idx + 1) / len(uploaded_files))
    
    df = pd.DataFrame(all_data)
    
    if len(df) > 0:
        st.success(f"✅ মোট {len(df)} জন ভোটার লোড হয়েছে")
        
        # ছবির মতো সুন্দর UI
        col1, col2 = st.columns(2)
        with col1:
            name_search = st.text_input("নাম")
        with col2:
            voter_search = st.text_input("ভোটার নং")
        
        father_search = st.text_input("পিতার নাম")
        
        # ফিল্টার
        mask = pd.Series([True] * len(df))
        if name_search:
            mask &= df["নাম"].str.contains(name_search, case=False, na=False)
        if voter_search:
            mask &= df["ভোটার নং"].astype(str).str.contains(voter_search, na=False)
        if father_search:
            mask &= df["পিতা"].str.contains(father_search, case=False, na=False)
        
        filtered = df[mask].copy()
        
        st.info(f"প্রদর্শিত: {len(filtered)} জন | মোট: {len(df)} জন")
        
        # কার্ড স্টাইল রেজাল্ট
        for _, row in filtered.iterrows():
            st.markdown(f"""
            <div style="background:white; padding:15px; border-radius:10px; margin:10px 0; box-shadow:0 2px 5px rgba(0,0,0,0.1);">
                <b>নাম:</b> {row['নাম']}<br>
                <b>ভোটার নং:</b> {row['ভোটার নং']}<br>
                <b>পিতা:</b> {row['পিতা']}<br>
                <b>মাতা:</b> {row['মাতা']}<br>
                <b>পেশা:</b> {row['পেশা']}<br>
                <b>ঠিকানা:</b> {row['ঠিকানা']}
            </div>
            """, unsafe_allow_html=True)
        
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("📥 সম্পূর্ণ তালিকা CSV ডাউনলোড করুন", csv, "full_voter_list.csv", "text/csv")
    else:
        st.error("কোনো তথ্য বের করা যায়নি। PDF আবার চেষ্টা করুন বা আমাকে বলুন।")
