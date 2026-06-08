import streamlit as st
import pdfplumber
import pandas as pd
import re

st.set_page_config(page_title="Voter Search System", layout="centered", page_icon="🗳️")

st.title("🗳️ Voter Search System")
st.markdown("**মধ্য এওচিয়া ভোটার তথ্য অনুসন্ধান**")

uploaded_files = st.file_uploader("PDF আপলোড করুন (একাধিক সমর্থিত)", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_data = []
    progress = st.progress(0)
    
    for idx, uploaded_file in enumerate(uploaded_files):
        with st.spinner(f"প্রসেস হচ্ছে: {uploaded_file.name}"):
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text: continue
                    
                    lines = text.split('\n')
                    i = 0
                    while i < len(lines):
                        line = lines[i].strip()
                        if re.search(r'০০\d{2}\.', line) or "নাম:" in line:
                            try:
                                name = re.search(r'নাম:\s*(.+?)(?=\s*ভোটার নং|$)', line)
                                voter = re.search(r'ভোটার নং:\s*(\d+)', line)
                                
                                father = mother = occ = dob = addr = ""
                                i += 1
                                while i < len(lines) and not re.search(r'০০\d{2}\.', lines[i]):
                                    nl = lines[i].strip()
                                    if 'পিতা:' in nl: father = nl.split('পিতা:')[-1].strip()
                                    elif 'মাতা:' in nl: mother = nl.split('মাতা:')[-1].strip()
                                    elif 'পশা:' in nl or 'পেশা:' in nl:
                                        occ = nl.split('পশা:')[-1].strip() if 'পশা:' in nl else nl.split('পেশা:')[-1].strip()
                                    elif 'জন্ম তারিখ:' in nl: dob = nl.split('জন্ম তারিখ:')[-1].strip()
                                    elif 'ঠিকানা:' in nl: addr = nl.split('ঠিকানা:')[-1].strip()
                                    i += 1
                                
                                all_data.append({
                                    "নাম": name.group(1).strip() if name else "",
                                    "ভোটার নং": voter.group(1) if voter else "",
                                    "পিতা": father,
                                    "মাতা": mother,
                                    "পেশা": occ,
                                    "জন্ম তারিখ": dob,
                                    "ঠিকানা": addr
                                })
                            except:
                                i += 1
                                continue
                        i += 1
        progress.progress((idx+1) / len(uploaded_files))
    
    df = pd.DataFrame(all_data)
    
    st.success(f"✅ মোট {len(df)} জন ভোটার লোড হয়েছে")
    
    # Search UI
    col1, col2 = st.columns(2)
    with col1:
        name_search = st.text_input("নাম")
    with col2:
        voter_search = st.text_input("ভোটার নং")
    
    father_search = st.text_input("পিতার নাম")
    
    # Filter
    mask = pd.Series([True]*len(df))
    if name_search: mask &= df["নাম"].str.contains(name_search, case=False, na=False)
    if voter_search: mask &= df["ভোটার নং"].str.contains(voter_search, na=False)
    if father_search: mask &= df["পিতা"].str.contains(father_search, case=False, na=False)
    
    result = df[mask]
    
    st.info(f"ফলাফল: {len(result)} জন")
    
    for _, row in result.iterrows():
        st.markdown(f"""
        **নাম:** {row['নাম']}  
        **ভোটার নং:** {row['ভোটার নং']}  
        **পিতা:** {row['পিতা']}  
        **মাতা:** {row['মাতা']}  
        **পেশা:** {row['পেশা']}  
        **ঠিকানা:** {row['ঠিকানা']}
        ---
        """)
    
    # Download
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button("📥 CSV ডাউনলোড", csv, "voter_list.csv", "text/csv")
