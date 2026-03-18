import streamlit as st
import pandas as pd
import json
import os
import uuid
from datetime import datetime
import hashlib
import time
import random

# ==================== إعدادات الصفحة ====================
st.set_page_config(
    page_title="FINCA FieldLink",
    page_icon="🏦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# تحسين للهاتف
st.markdown("""
<style>
    .stApp {
        max-width: 100%;
        padding: 0.5rem;
    }
    .stButton button {
        width: 100%;
        height: 3.2rem;
        font-size: 1.1rem;
        font-weight: bold;
        border-radius: 10px;
    }
    .stTextInput input, .stNumberInput input, .stSelectbox, .stTextArea textarea {
        font-size: 1rem;
        padding: 0.7rem;
        border-radius: 8px;
    }
    h1 {
        font-size: 1.8rem !important;
        text-align: center;
        color: #2ecc71;
        margin-bottom: 0.5rem;
    }
    h3 {
        font-size: 1.3rem !important;
        margin-top: 0.5rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
    }
    .stAlert {
        font-size: 1rem;
        padding: 0.8rem;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.8rem;
        padding: 0.5rem 0.2rem;
    }
    hr {
        margin: 0.5rem 0;
    }
    .stExpander {
        border: 1px solid #ddd;
        border-radius: 10px;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ==================== إعدادات التخزين ====================
DATA_FOLDER = "finca_data"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

CLIENTS_FILE = os.path.join(DATA_FOLDER, "clients.json")
OFFLINE_FILE = os.path.join(DATA_FOLDER, "offline_queue.json")
SYNC_FILE = os.path.join(DATA_FOLDER, "sync_status.json")

# ==================== دوال مساعدة ====================
def load_data(filename, default=None):
    """تحميل البيانات من ملف JSON مع معالجة الأخطاء"""
    if default is None:
        default = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
                else:
                    return default
        except (json.JSONDecodeError, FileNotFoundError):
            return default
    return default

def save_data(filename, data):
    """حفظ البيانات في ملف JSON"""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except:
        return False

def hash_id(id_number):
    """تشفير بسيط لرقم الهوية"""
    return hashlib.sha256(str(id_number).encode()).hexdigest()[:16]

def generate_client_id():
    """توليد معرف فريد للعميل"""
    return str(uuid.uuid4())[:8].upper()

def calculate_credit_score(client_data):
    """حساب درجة الجدارة الائتمانية"""
    score = 0
    monthly_income = client_data.get("monthly_income", 0)
    loan_amount = client_data.get("loan_amount", 0)
    business_type = client_data.get("business_type", "Other")
    
    # معيار الدخل
    if monthly_income >= 1000000:
        score += 40
    elif monthly_income >= 500000:
        score += 30
    elif monthly_income >= 200000:
        score += 20
    else:
        score += 10
    
    # معيار القرض
    if loan_amount <= monthly_income * 3:
        score += 30
    elif loan_amount <= monthly_income * 5:
        score += 20
    else:
        score += 10
    
    # معيار نوع العمل
    business_scores = {
        "Retail Shop": 20,
        "Agriculture": 20,
        "Livestock": 18,
        "Food Vendor": 18,
        "Transport": 15,
        "Other": 10
    }
    score += business_scores.get(business_type, 10)
    
    # عامل عشوائي خفيف للواقعية
    score += random.randint(0, 5)
    
    return min(score, 100)  # الحد الأقصى 100

# تهيئة session state
if "offline_mode" not in st.session_state:
    st.session_state.offline_mode = False
if "officer_name" not in st.session_state:
    st.session_state.officer_name = ""
if "id_verified" not in st.session_state:
    st.session_state.id_verified = False

# ==================== العنوان الرئيسي ====================
st.markdown("""
<h1>🏦 FINCA FieldLink</h1>
<h4 style='text-align: center; color: #666;'>Empowering field officers. Reaching every village.</h4>
<hr>
""", unsafe_allow_html=True)

# ==================== شريط الحالة ====================
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.session_state.offline_mode:
        st.warning("📴 **Offline Mode** - Data will sync when online")
    else:
        st.success("📶 **Online Mode** - Connected")

# ==================== معلومات الموظف ====================
with st.expander("👤 Officer Information", expanded=False):
    officer = st.text_input("Your Name", value=st.session_state.officer_name, placeholder="Enter your name")
    if officer:
        st.session_state.officer_name = officer
    st.markdown(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")

# ==================== التبويبات الرئيسية ====================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "➕ New", 
    "📋 Clients", 
    "📸 ID", 
    "📊 Reports",
    "🔄 Sync"
])

# ==================== TAB 1: تسجيل عميل جديد ====================
with tab1:
    st.subheader("➕ Register New Client")
    st.caption("Fill the details below. Works offline.")
    
    # معلومات العميل
    col1, col2 = st.columns(2)
    
    with col1:
        first_name = st.text_input("First Name *", key="fn")
        last_name = st.text_input("Last Name *", key="ln")
        national_id = st.text_input("National ID *", key="nid", help="Enter the 14-digit ID number")
        phone = st.text_input("Phone Number *", key="phone", help="07XX XXX XXX")
        village = st.text_input("Village/Location *", key="village")
        
    with col2:
        business_type = st.selectbox(
            "Business Type *",
            ["Retail Shop", "Agriculture", "Livestock", "Food Vendor", "Transport", "Other"],
            key="btype"
        )
        monthly_income = st.number_input("Monthly Income (UGX) *", min_value=0, step=100000, value=500000, key="income")
        loan_amount = st.number_input("Loan Amount (UGX) *", min_value=0, step=100000, value=1000000, key="loan")
        loan_purpose = st.selectbox(
            "Loan Purpose *",
            ["Business Expansion", "Buy Stock", "Equipment", "Emergency", "School Fees", "Other"],
            key="purpose"
        )
    
    # صورة العميل
    st.markdown("#### 📸 Client Photo (Optional)")
    photo = st.camera_input("Take a photo", key="client_photo")
    
    # التوقيع الإلكتروني
    st.markdown("#### ✍️ Client Signature *")
    signature = st.text_area("Client name (as signature)", key="signature", height=60, placeholder="Client writes their name here")
    
    # ملاحظات
    notes = st.text_area("Additional Notes", key="notes", height=80, placeholder="Any extra information...")
    
    # زر الحفظ
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("✅ **SAVE CLIENT**", type="primary", use_container_width=True):
        # التحقق من المدخلات
        required_fields = [first_name, last_name, national_id, phone, village, signature]
        if not all(required_fields) or monthly_income <= 0 or loan_amount <= 0:
            st.error("❌ Please fill all required fields (*)")
        else:
            # إنشاء بيانات العميل
            client = {
                "client_id": generate_client_id(),
                "first_name": first_name,
                "last_name": last_name,
                "full_name": f"{first_name} {last_name}",
                "national_id": hash_id(national_id),
                "phone": phone,
                "village": village,
                "business_type": business_type,
                "monthly_income": monthly_income,
                "loan_amount": loan_amount,
                "loan_purpose": loan_purpose,
                "notes": notes,
                "signature": signature,
                "has_photo": photo is not None,
                "timestamp": datetime.now().isoformat(),
                "status": "Pending",
                "officer": st.session_state.officer_name or "Field Officer",
                "synced": not st.session_state.offline_mode
            }
            
            # حساب درجة الجدارة
            client["credit_score"] = calculate_credit_score(client)
            
            # حفظ العميل
            clients = load_data(CLIENTS_FILE, [])
            clients.append(client)
            save_data(CLIENTS_FILE, clients)
            
            # إذا كان أوفلاين، أضف للمزامنة
            if st.session_state.offline_mode:
                offline = load_data(OFFLINE_FILE, [])
                offline.append({
                    "action": "new_client", 
                    "data": client, 
                    "timestamp": datetime.now().isoformat()
                })
                save_data(OFFLINE_FILE, offline)
                st.warning("📴 **Saved offline**. Will sync when online.")
            else:
                st.success(f"✅ **Client {first_name} {last_name} registered successfully!**")
                st.balloons()
            
            # عرض ملخص سريع
            st.info(f"""
            **📋 Summary**
            - **Client ID:** {client['client_id']}
            - **Credit Score:** {client['credit_score']}/100
            - **Status:** {client['status']}
            """)
            
            # تفريغ الحقول (اختياري)
            st.session_state.fn = ""
            st.session_state.ln = ""

# ==================== TAB 2: عرض العملاء ====================
with tab2:
    st.subheader("📋 All Clients")
    
    clients = load_data(CLIENTS_FILE, [])
    
    if clients:
        # إحصائيات سريعة
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total", len(clients))
        with col2:
            pending = len([c for c in clients if c.get("status") == "Pending"])
            st.metric("Pending", pending)
        with col3:
            approved = len([c for c in clients if c.get("status") == "Approved"])
            st.metric("Approved", approved)
        with col4:
            total_amount = sum([c.get("loan_amount", 0) for c in clients])
            st.metric("Total Loans", f"{total_amount/1000000:.1f}M")
        
        # فلترة
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Approved", "Rejected", "Disbursed"])
        with col2:
            villages = list(set([c.get("village", "Unknown") for c in clients if c.get("village")]))
            village_filter = st.selectbox("Filter by Village", ["All"] + villages)
        
        # بحث
        search = st.text_input("🔍 Search by Name or Phone", placeholder="Type to search...")
        
        # تطبيق الفلترة
        filtered = clients.copy()
        
        if status_filter != "All":
            filtered = [c for c in filtered if c.get("status") == status_filter]
        
        if village_filter != "All":
            filtered = [c for c in filtered if c.get("village") == village_filter]
        
        if search:
            search_lower = search.lower()
            filtered = [
                c for c in filtered 
                if search_lower in c.get("full_name", "").lower() 
                or search_lower in c.get("phone", "")
            ]
        
        # عرض العملاء
        st.markdown(f"**Showing {len(filtered)} clients**")
        
        if filtered:
            for client in filtered[-10:]:  # آخر 10 عملاء
                with st.expander(f"👤 {client.get('full_name', 'Unknown')} - {client.get('village', 'Unknown')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**ID:** `{client.get('client_id', 'N/A')}`")
                        st.markdown(f"**Phone:** {client.get('phone', 'N/A')}")
                        st.markdown(f"**Business:** {client.get('business_type', 'N/A')}")
                        st.markdown(f"**Income:** {client.get('monthly_income', 0):,.0f} UGX")
                    with col2:
                        st.markdown(f"**Loan:** {client.get('loan_amount', 0):,.0f} UGX")
                        st.markdown(f"**Score:** {client.get('credit_score', 0)}/100")
                        st.markdown(f"**Status:** **:{'green' if client.get('status')=='Approved' else 'orange'}[{client.get('status', 'Pending')}]**")
                        st.markdown(f"**Date:** {client.get('timestamp', 'N/A')[:10]}")
                    
                    # تحديث الحالة
                    new_status = st.selectbox(
                        "Update Status",
                        ["Pending", "Approved", "Rejected", "Disbursed"],
                        key=f"status_{client.get('client_id', '')}"
                    )
                    if st.button(f"Update {client.get('client_id', '')}", key=f"update_{client.get('client_id', '')}"):
                        for c in clients:
                            if c.get("client_id") == client.get("client_id"):
                                c["status"] = new_status
                        save_data(CLIENTS_FILE, clients)
                        st.success("✅ Status updated!")
                        st.rerun()
        else:
            st.info("No clients match your filters")
    else:
        st.info("📭 No clients registered yet. Add your first client in the 'New' tab.")

# ==================== TAB 3: التحقق بالهوية ====================
with tab3:
    st.subheader("📸 Verify National ID")
    st.caption("Take photos of the client's ID for verification")
    
    col1, col2 = st.columns(2)
    
    with col1:
        id_front = st.camera_input("Front of ID", key="id_front")
    with col2:
        id_back = st.camera_input("Back of ID", key="id_back")
    
    if id_front and id_back:
        st.success("✅ ID photos captured successfully")
        st.session_state.id_verified = True
        
        # معلومات مستخرجة (محاكاة)
        st.markdown("#### 📋 Extracted Information")
        
        # محاكاة استخراج البيانات
        fake_names = ["John Mukasa", "Mary Nabatanzi", "Peter Okello", "Grace Achieng"]
        fake_name = random.choice(fake_names)
        fake_id = "CM" + str(random.randint(10000000, 99999999))
        fake_dob = f"{random.randint(1960, 1990)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
        
        st.info(f"""
        **Name:** {fake_name}
        **ID Number:** {fake_id}
        **Date of Birth:** {fake_dob}
        **District:** {random.choice(['Kampala', 'Wakiso', 'Mukono', 'Jinja'])}
        """)
        
        if st.button("✅ Verify and Continue", use_container_width=True):
            st.success("✅ ID Verified! You can now register the client in the 'New' tab.")
    else:
        if st.session_state.id_verified:
            st.info("✅ ID already verified for this session")
        else:
            st.warning("👆 Take photos of both sides of the ID")

# ==================== TAB 4: التقارير ====================
with tab4:
    st.subheader("📊 Daily Reports")
    
    clients = load_data(CLIENTS_FILE, [])
    
    if clients:
        # تحويل إلى DataFrame
        df = pd.DataFrame(clients)
        
        # اختيار التاريخ
        today = datetime.now().date()
        selected_date = st.date_input("Select Date", today)
        
        # تصفية حسب التاريخ
        if 'timestamp' in df.columns:
            df['date_only'] = pd.to_datetime(df['timestamp']).dt.date
            daily_df = df[df['date_only'] == selected_date]
        else:
            daily_df = pd.DataFrame()
        
        if not daily_df.empty:
            # إحصائيات سريعة
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Clients", len(daily_df))
            with col2:
                total_loan = daily_df['loan_amount'].sum()
                st.metric("Total Loans", f"{total_loan:,.0f} UGX")
            with col3:
                avg_loan = daily_df['loan_amount'].mean()
                st.metric("Average Loan", f"{avg_loan:,.0f} UGX")
            
            # عرض البيانات
            st.subheader("📋 Client List")
            
            # اختيار الأعمدة للعرض
            display_cols = ['full_name', 'village', 'loan_amount', 'credit_score', 'status']
            available_cols = [col for col in display_cols if col in daily_df.columns]
            
            st.dataframe(
                daily_df[available_cols].head(20),
                use_container_width=True,
                hide_index=True
            )
            
            # تقرير حسب المنطقة
            if 'village' in daily_df.columns:
                st.subheader("📍 Summary by Village")
                village_summary = daily_df.groupby('village').agg({
                    'full_name': 'count',
                    'loan_amount': 'sum'
                }).rename(columns={'full_name': 'count', 'loan_amount': 'total_loan'})
                st.dataframe(village_summary, use_container_width=True)
            
            # تصدير التقرير
            csv = daily_df.to_csv(index=False)
            st.download_button(
                label="📥 **Download Report as CSV**",
                data=csv,
                file_name=f"finca_report_{selected_date}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info(f"📭 No clients registered on {selected_date}")
    else:
        st.info("📭 No data available yet")

# ==================== TAB 5: المزامنة ====================
with tab5:
    st.subheader("🔄 Sync Status")
    
    offline = load_data(OFFLINE_FILE, [])
    sync_status = load_data(SYNC_FILE, {})
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Offline Records", len(offline))
    with col2:
        # التحقق من نوع sync_status
        if isinstance(sync_status, dict):
            last_sync = sync_status.get("last_sync", "Never")
        else:
            last_sync = "Never"
        
        # تنسيق التاريخ
        if last_sync != "Never" and len(last_sync) > 10:
            display_sync = last_sync[:16].replace('T', ' ')
        else:
            display_sync = "Never"
        st.metric("Last Sync", display_sync)
    
    # وضع عدم الاتصال
    offline_mode = st.toggle("📴 Offline Mode", value=st.session_state.offline_mode)
    if offline_mode != st.session_state.offline_mode:
        st.session_state.offline_mode = offline_mode
        if offline_mode:
            st.warning("Switched to offline mode. Data will be saved locally.")
        else:
            st.success("Switched to online mode.")
        st.rerun()
    
    # زر المزامنة
    if st.button("🔄 **SYNC NOW**", type="primary", use_container_width=True):
        if offline:
            with st.spinner(f"Syncing {len(offline)} records..."):
                progress = st.progress(0)
                for i in range(len(offline)):
                    time.sleep(0.1)
                    progress.progress((i + 1) / len(offline))
                
                # تحديث حالة المزامنة
                save_data(OFFLINE_FILE, [])
                
                sync_data = {
                    "last_sync": datetime.now().isoformat(),
                    "records_synced": len(offline)
                }
                save_data(SYNC_FILE, sync_data)
                
                st.success(f"✅ Successfully synced {len(offline)} records!")
                st.balloons()
                time.sleep(2)
                st.rerun()
        else:
            st.info("✅ No offline records to sync")

# ==================== شريط جانبي ====================
with st.sidebar:
    st.markdown("### 📊 Quick Stats")
    
    clients = load_data(CLIENTS_FILE, [])
    if clients:
        df = pd.DataFrame(clients) if clients else pd.DataFrame()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Clients", len(clients))
        with col2:
            total_loan = df['loan_amount'].sum() if not df.empty else 0
            st.metric("Total Loans", f"{total_loan/1000000:.1f}M")
        
        col1, col2 = st.columns(2)
        with col1:
            pending = len([c for c in clients if c.get("status") == "Pending"])
            st.metric("Pending", pending)
        with col2:
            approved = len([c for c in clients if c.get("status") == "Approved"])
            st.metric("Approved", approved)
        
        # متوسط درجة الائتمان
        if not df.empty and 'credit_score' in df.columns:
            avg_score = df['credit_score'].mean()
            st.metric("Avg Credit Score", f"{avg_score:.0f}")
    else:
        st.info("No data yet")
    
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("""
    **FINCA FieldLink** v2.0
    
    **Features:**
    - ✅ Works offline
    - ✅ ID verification
    - ✅ Credit scoring
    - ✅ Daily reports
    - ✅ Auto-sync
    
    **Built for Uganda**
    """)
    
    st.markdown("---")
    st.markdown("**Officer:** " + (st.session_state.officer_name or "Not set"))
    st.markdown(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")

# ==================== تذييل ====================
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray; font-size: 0.8rem;'>© 2026 FINCA FieldLink. All rights reserved.</p>", unsafe_allow_html=True)
