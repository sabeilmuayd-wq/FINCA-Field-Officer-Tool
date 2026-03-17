import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import json
import os

# إعدادات الصفحة
st.set_page_config(
    page_title="FINCA Field Officer Tool",
    page_icon="🏦",
    layout="wide"
)

# عنوان التطبيق
st.markdown("""
<h1 style='text-align: center; color: #2ecc71;'>🏦 FINCA Field Officer Tool</h1>
<h4 style='text-align: center;'>Empower your loan officers. Serve more customers. Zero paperwork.</h4>
<hr>
""", unsafe_allow_html=True)

# محاكاة قاعدة بيانات بسيطة (في ملف)
DATA_FILE = "finca_clients.json"

def load_clients():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_client(client_data):
    clients = load_clients()
    clients.append(client_data)
    with open(DATA_FILE, 'w') as f:
        json.dump(clients, f, indent=2)

# واجهة التطبيق - 3 أقسام رئيسية
tab1, tab2, tab3 = st.tabs(["➕ Register New Client", "📋 View All Clients", "📊 Daily Report"])

# TAB 1: تسجيل عميل جديد
with tab1:
    st.subheader("Register a New Client")
    
    col1, col2 = st.columns(2)
    
    with col1:
        client_name = st.text_input("Client Full Name *")
        client_phone = st.text_input("Phone Number *")
        client_village = st.text_input("Village/Location *")
        client_business = st.text_input("Type of Business")
        
    with col2:
        loan_amount = st.number_input("Loan Amount Requested (UGX) *", min_value=0, step=100000)
        loan_purpose = st.selectbox(
            "Loan Purpose",
            ["Business Expansion", "Agriculture", "School Fees", "Medical", "Home Improvement", "Other"]
        )
        loan_term = st.selectbox(
            "Loan Term (Months)",
            [1, 3, 6, 12, 24]
        )
        officer_name = st.text_input("Loan Officer Name *")
    
    # ملاحظات إضافية
    notes = st.text_area("Additional Notes")
    
    # زر التسجيل
    if st.button("✅ Register Client", type="primary", use_container_width=True):
        if client_name and client_phone and client_village and loan_amount > 0 and officer_name:
            
            client_data = {
                "id": str(uuid.uuid4())[:8],
                "name": client_name,
                "phone": client_phone,
                "village": client_village,
                "business": client_business,
                "loan_amount": loan_amount,
                "loan_purpose": loan_purpose,
                "loan_term": loan_term,
                "officer": officer_name,
                "notes": notes,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "status": "Pending"
            }
            
            save_client(client_data)
            st.success(f"✅ Client {client_name} registered successfully!")
            st.balloons()
        else:
            st.error("Please fill all required fields (*)")

# TAB 2: عرض كل العملاء
with tab2:
    st.subheader("All Registered Clients")
    
    clients = load_clients()
    
    if clients:
        # تحويل البيانات إلى DataFrame للعرض
        df = pd.DataFrame(clients)
        
        # أزرار تصفية
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_status = st.selectbox("Filter by Status", ["All", "Pending", "Approved", "Rejected"])
        with col2:
            filter_officer = st.selectbox("Filter by Officer", ["All"] + list(df['officer'].unique()))
        with col3:
            search = st.text_input("Search by Name or Phone")
        
        # تطبيق التصفية
        filtered_df = df.copy()
        if filter_status != "All":
            filtered_df = filtered_df[filtered_df['status'] == filter_status]
        if filter_officer != "All":
            filtered_df = filtered_df[filtered_df['officer'] == filter_officer]
        if search:
            filtered_df = filtered_df[
                filtered_df['name'].str.contains(search, case=False) |
                filtered_df['phone'].str.contains(search)
            ]
        
        # عرض الجدول
        st.dataframe(
            filtered_df[['date', 'name', 'phone', 'village', 'loan_amount', 'status', 'officer']],
            use_container_width=True,
            hide_index=True
        )
        
        # تفاصيل العميل عند النقر (محاكاة بسيطة)
        st.subheader("Update Client Status")
        col1, col2 = st.columns(2)
        with col1:
            client_id_to_update = st.text_input("Enter Client ID to update status")
        with col2:
            new_status = st.selectbox("New Status", ["Pending", "Approved", "Rejected"])
        
        if st.button("Update Status"):
            # هنا يمكن إضافة منطق التحديث
            st.info("This will update the client status. (Full implementation coming soon)")
            
    else:
        st.info("No clients registered yet. Use the 'Register' tab to add your first client.")

# TAB 3: التقرير اليومي
with tab3:
    st.subheader("Daily Report")
    
    clients = load_clients()
    
    if clients:
        df = pd.DataFrame(clients)
        df['date_only'] = pd.to_datetime(df['date']).dt.date
        
        # اختيار التاريخ
        selected_date = st.date_input("Select Date", datetime.now().date())
        
        # تصفية حسب التاريخ
        daily_clients = df[df['date_only'] == selected_date]
        
        if not daily_clients.empty:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Clients Today", len(daily_clients))
            
            with col2:
                total_amount = daily_clients['loan_amount'].sum()
                st.metric("Total Loan Amount", f"{total_amount:,.0f} UGX")
            
            with col3:
                avg_amount = daily_clients['loan_amount'].mean()
                st.metric("Average Loan", f"{avg_amount:,.0f} UGX")
            
            # عرض العملاء
            st.subheader(f"Clients on {selected_date}")
            st.dataframe(
                daily_clients[['name', 'phone', 'village', 'loan_amount', 'status', 'officer']],
                use_container_width=True,
                hide_index=True
            )
            
            # زر التحميل
            csv = daily_clients.to_csv(index=False)
            st.download_button(
                label="📥 Download Report as CSV",
                data=csv,
                file_name=f"finca_report_{selected_date}.csv",
                mime="text/csv"
            )
        else:
            st.info(f"No clients registered on {selected_date}")
    else:
        st.info("No data available yet")

# شريط جانبي بمعلومات
with st.sidebar:
    st.markdown("### ℹ️ About This Tool")
    st.markdown("""
    **FINCA Field Officer Tool** helps you:
    - Register clients instantly on your phone
    - Track all loan applications
    - Generate daily reports automatically
    - Eliminate paperwork and errors
    
    **Version:** 1.0 (Demo)
    """)
    
    st.markdown("---")
    st.markdown("### 📊 Quick Stats")
    
    clients = load_clients()
    if clients:
        df = pd.DataFrame(clients)
        st.metric("Total Clients", len(df))
        st.metric("Total Loans", f"{df['loan_amount'].sum():,.0f} UGX")
        st.metric("Pending Applications", len(df[df['status'] == 'Pending']))
    else:
        st.info("No data yet")

# تذييل
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Built exclusively for FINCA Uganda | Demo Version</p>", unsafe_allow_html=True)
