import streamlit as st
import pandas as pd
import json
import os
import uuid
from datetime import datetime
import hashlib
import base64
from PIL import Image
import io

# إعدادات الصفحة - محسنة للهاتف
st.set_page_config(
    page_title="FINCA FieldLink",
    page_icon="🏦",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# تحسين للهاتف (تكبير الخط)
st.markdown("""
<style>
    .stApp {
        max-width: 100%;
        padding: 1rem;
    }
    .stButton button {
        width: 100%;
        height: 3.5rem;
        font-size: 1.2rem;
    }
    .stTextInput input, .stNumberInput input {
        font-size: 1.1rem;
        padding: 0.8rem;
    }
    h1 {
        font-size: 2rem !important;
        text-align: center;
    }
    h3 {
        font-size: 1.5rem !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
    }
    .stAlert {
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

# ملفات التخزين (محاكاة قاعدة بيانات)
DATA_FOLDER = "finca_data"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

CLIENTS_FILE = os.path.join(DATA_FOLDER, "clients.json")
OFFLINE_FILE = os.path.join(DATA_FOLDER, "offline_queue.json")
SYNC_FILE = os.path.join(DATA_FOLDER, "sync_status.json")

# دوال مساعدة للتعامل مع الملفات
def load_data(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def save_data(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

# دوال التشفير البسيط
def hash_id(id_number):
    return hashlib.sha256(str(id_number).encode()).hexdigest()[:16]

def generate_client_id():
    return str(uuid.uuid4())[:8].upper()

# ==================== الصفحة الرئيسية ====================
st.markdown("""
<h1 style='color: #2ecc71;'>🏦 FINCA FieldLink</h1>
<h4 style='text-align: center;'>Empowering field officers. Reaching every village.</h4>
<hr>
""", unsafe_allow_html=True)

# شريط حالة الإنترنت
if "offline_mode" not in st.session_state:
    st.session_state.offline_mode = False

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.session_state.offline_mode:
        st.warning("📴 Offline Mode - Data will sync when online")
    else:
        st.success("📶 Online Mode - Connected")

# التبويبات الرئيسية
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "➕ New Client", 
    "📋 All Clients", 
    "📸 Verify ID", 
    "📊 Reports",
    "🔄 Sync"
])

# ==================== TAB 1: تسجيل عميل جديد ====================
with tab1:
    st.subheader("➕ Register New Client")
    st.markdown("Fill the details below. Works offline.")
    
    # معلومات العميل
    col1, col2 = st.columns(2)
    
    with col1:
        first_name = st.text_input("First Name *")
        last_name = st.text_input("Last Name *")
        national_id = st.text_input("National ID *", help="Enter the 14-digit ID number")
        phone = st.text_input("Phone Number *", help="07XX XXX XXX")
        village = st.text_input("Village/Location *")
        
    with col2:
        business_type = st.selectbox(
            "Business Type",
            ["Retail Shop", "Agriculture", "Livestock", "Food Vendor", "Transport", "Other"]
        )
        monthly_income = st.number_input("Monthly Income (UGX) *", min_value=0, step=100000, value=500000)
        loan_amount = st.number_input("Loan Amount Requested (UGX) *", min_value=0, step=100000, value=1000000)
        loan_purpose = st.selectbox(
            "Loan Purpose",
            ["Business Expansion", "Buy Stock", "Equipment", "Emergency", "School Fees", "Other"]
        )
    
    # صورة العميل (محاكاة)
    st.markdown("#### 📸 Take Client Photo")
    photo = st.camera_input("Take a photo", key="client_photo")
    
    # التوقيع الإلكتروني
    st.markdown("#### ✍️ Client Signature")
    signature = st.text_area("Client name (as signature)", key="signature", height=50)
    
    # ملاحظات
    notes = st.text_area("Additional Notes", height=80)
    
    # زر الحفظ
    if st.button("✅ SAVE CLIENT", type="primary", use_container_width=True):
        # التحقق من المدخلات
        if not (first_name and last_name and national_id and phone and village and monthly_income > 0 and loan_amount > 0 and signature):
            st.error("❌ Please fill all required fields (*)")
        else:
            # إنشاء بيانات العميل
            client = {
                "client_id": generate_client_id(),
                "first_name": first_name,
                "last_name": last_name,
                "full_name": f"{first_name} {last_name}",
                "national_id": hash_id(national_id),  # تخزين مشفر
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
                "credit_score": 0,
                "officer": st.session_state.get("officer_name", "Field Officer"),
                "synced": not st.session_state.offline_mode  # إذا كان أوفلاين، لن يتم المزامنة
            }
            
            # حساب درجة الجدارة الائتمانية (بسيط)
            score = 0
            if monthly_income >= 1000000:
                score += 40
            elif monthly_income >= 500000:
                score += 30
            else:
                score += 20
                
            if loan_amount <= monthly_income * 3:
                score += 30
            else:
                score += 10
                
            if business_type in ["Retail Shop", "Agriculture"]:
                score += 20
            elif business_type in ["Livestock", "Food Vendor"]:
                score += 15
            else:
                score += 10
                
            client["credit_score"] = score
            
            # حفظ العميل
            clients = load_data(CLIENTS_FILE)
            clients.append(client)
            save_data(CLIENTS_FILE, clients)
            
            # إذا كان أوفلاين، أضف للمزامنة
            if st.session_state.offline_mode:
                offline = load_data(OFFLINE_FILE)
                offline.append({"action": "new_client", "data": client, "timestamp": datetime.now().isoformat()})
                save_data(OFFLINE_FILE, offline)
                st.warning("📴 Client saved offline. Will sync when online.")
            else:
                st.success(f"✅ Client {first_name} {last_name} registered successfully!")
                st.balloons()
            
            # عرض ملخص
            st.info(f"""
            **Client ID:** {client['client_id']}
            **Credit Score:** {score}/100
            **Status:** {client['status']}
            """)

# ==================== TAB 2: عرض العملاء ====================
with tab2:
    st.subheader("📋 All Registered Clients")
    
    clients = load_data(CLIENTS_FILE)
    
    if clients:
        # فلترة حسب الحالة
        status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Approved", "Rejected", "Disbursed"])
        
        # فلترة حسب المنطقة
        villages = list(set([c.get("village", "Unknown") for c in clients]))
        village_filter = st.selectbox("Filter by Village", ["All"] + villages)
        
        # بحث
        search = st.text_input("🔍 Search by Name or Phone")
        
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
        
        # عرض الإحصائيات
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Clients", len(filtered))
        with col2:
            total_amount = sum([c.get("loan_amount", 0) for c in filtered])
            st.metric("Total Loans", f"{total_amount:,.0f} UGX")
        with col3:
            avg_score = sum([c.get("credit_score", 0) for c in filtered]) / len(filtered) if filtered else 0
            st.metric("Avg Credit Score", f"{avg_score:.0f}")
        
        # عرض العملاء في جدول مناسب للهاتف
        for client in filtered[-20:]:  # آخر 20 عميل
            with st.expander(f"{client.get('full_name', 'Unknown')} - {client.get('village', 'Unknown')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**ID:** {client.get('client_id', 'N/A')}")
                    st.markdown(f"**Phone:** {client.get('phone', 'N/A')}")
                    st.markdown(f"**Business:** {client.get('business_type', 'N/A')}")
                    st.markdown(f"**Income:** {client.get('monthly_income', 0):,.0f} UGX")
                with col2:
                    st.markdown(f"**Loan:** {client.get('loan_amount', 0):,.0f} UGX")
                    st.markdown(f"**Score:** {client.get('credit_score', 0)}/100")
                    st.markdown(f"**Status:** {client.get('status', 'Pending')}")
                    st.markdown(f"**Date:** {client.get('timestamp', 'N/A')[:10]}")
                
                # تحديث الحالة
                new_status = st.selectbox(
                    "Update Status",
                    ["Pending", "Approved", "Rejected", "Disbursed"],
                    key=f"status_{client.get('client_id', '')}"
                )
                if st.button(f"Update {client.get('client_id', '')}", key=f"update_{client.get('client_id', '')}"):
                    # تحديث الحالة
                    for c in clients:
                        if c.get("client_id") == client.get("client_id"):
                            c["status"] = new_status
                    save_data(CLIENTS_FILE, clients)
                    st.success("Status updated!")
                    st.rerun()
    else:
        st.info("No clients registered yet. Add your first client in the 'New Client' tab.")

# ==================== TAB 3: التحقق بالهوية ====================
with tab3:
    st.subheader("📸 Verify National ID")
    st.markdown("Take a photo of the client's ID for verification")
    
    col1, col2 = st.columns(2)
    
    with col1:
        id_front = st.camera_input("Front of ID", key="id_front")
    with col2:
        id_back = st.camera_input("Back of ID", key="id_back")
    
    if id_front and id_back:
        st.success("✅ ID photos captured successfully")
        
        # استخراج الرقم (محاكاة)
        st.markdown("#### 📋 Extracted Information")
        st.info("""
        **Name:** [Extracted from ID]
        **ID Number:** [Extracted]
        **Date of Birth:** [Extracted]
        **District:** [Extracted]
        
        *This is a demo. Real extraction requires OCR integration.*
        """)
        
        if st.button("Verify and Continue"):
            st.session_state.id_verified = True
            st.success("ID Verified! You can now register the client.")

# ==================== TAB 4: التقارير ====================
with tab4:
    st.subheader("📊 Daily Reports")
    
    clients = load_data(CLIENTS_FILE)
    
    if clients:
        # تحويل إلى DataFrame
        df = pd.DataFrame(clients)
        
        # اختيار التاريخ
        today = datetime.now().date()
        selected_date = st.date_input("Select Date", today)
        
        # تصفية حسب التاريخ
        df['date_only'] = pd.to_datetime(df['timestamp']).dt.date
        daily_df = df[df['date_only'] == selected_date]
        
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
            st.subheader("Client List")
            st.dataframe(
                daily_df[['full_name', 'phone', 'village', 'loan_amount', 'credit_score', 'status']],
                use_container_width=True,
                hide_index=True
            )
            
            # تقرير حسب المنطقة
            st.subheader("Summary by Village")
            village_summary = daily_df.groupby('village').agg({
                'full_name': 'count',
                'loan_amount': 'sum'
            }).rename(columns={'full_name': 'count', 'loan_amount': 'total_loan'})
            st.dataframe(village_summary, use_container_width=True)
            
            # تصدير التقرير
            csv = daily_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Report as CSV",
                data=csv,
                file_name=f"finca_report_{selected_date}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info(f"No clients registered on {selected_date}")
    else:
        st.info("No data available yet")

# ==================== TAB 5: المزامنة ====================
with tab5:
    st.subheader("🔄 Sync Status")
    
    offline = load_data(OFFLINE_FILE)
    sync_status = load_data(SYNC_FILE)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Offline Records", len(offline))
    with col2:
        last_sync = sync_status.get("last_sync", "Never")
        st.metric("Last Sync", last_sync[:16] if last_sync != "Never" else "Never")
    
    # وضع عدم الاتصال
    offline_mode = st.toggle("Offline Mode", value=st.session_state.offline_mode)
    if offline_mode != st.session_state.offline_mode:
        st.session_state.offline_mode = offline_mode
        st.rerun()
    
    # زر المزامنة
    if st.button("🔄 SYNC NOW", type="primary", use_container_width=True):
        if offline:
            # محاكاة المزامنة
            with st.spinner("Syncing..."):
                import time
                progress = st.progress(0)
                for i in range(len(offline)):
                    time.sleep(0.1)
                    progress.progress((i + 1) / len(offline))
                
                # تحديث حالة المزامنة
                save_data(OFFLINE_FILE, [])
                sync_status = {
                    "last_sync": datetime.now().isoformat(),
                    "records_synced": len(offline)
                }
                save_data(SYNC_FILE, sync_status)
                
                st.success(f"✅ Successfully synced {len(offline)} records!")
                st.balloons()
        else:
            st.info("No offline records to sync")

# ==================== شريط جانبي ====================
with st.sidebar:
    st.markdown("### 👤 Officer")
    officer = st.text_input("Your Name", value=st.session_state.get("officer_name", ""))
    if officer:
        st.session_state.officer_name = officer
    
    st.markdown("---")
    st.markdown("### 📊 Quick Stats")
    
    clients = load_data(CLIENTS_FILE)
    if clients:
        df = pd.DataFrame(clients)
        pending = len(df[df['status'] == 'Pending'])
        approved = len(df[df['status'] == 'Approved'])
        total_loan = df['loan_amount'].sum()
        
        st.metric("Total Clients", len(df))
        st.metric("Pending Applications", pending)
        st.metric("Approved", approved)
        st.metric("Total Loans", f"{total_loan:,.0f} UGX")
    else:
        st.info("No data yet")
    
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("""
    **FINCA FieldLink** v1.0
    - Works offline
    - ID verification
    - Credit scoring
    - Daily reports
    - Auto-sync
    """)

# تذييل
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray; font-size: 0.9rem;'>© 2026 FINCA FieldLink. Built for Uganda.</p>", unsafe_allow_html=True)
