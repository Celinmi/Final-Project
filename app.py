import streamlit as st
import pandas as pd
import numpy as np
from geopy.distance import geodesic
from scipy.optimize import linear_sum_assignment
import requests

# טוען את קובץ ה-CSV מ-GitHub
url = 'https://raw.githubusercontent.com/Celinmi/Final-Project/main/volunteer_pool.csv' 
Volunteer_pool = pd.read_csv(url)
logo_url = 'https://raw.githubusercontent.com/Celinmi/Final-Project/main/ידידים - לוגו.jpg'
back_ground_url = 'https://raw.githubusercontent.com/Celinmi/Final-Project/main/ידידים - רקע.jpg'
categories = ['הנעה', "פנצ'ר", 'רכב נעול', 'קורונה - קניית תרופות', 'דלת', 'אחר', 'שמן-מים-דלק', 'שינוע', 'קורונה - שינוע מזון', 'קורונה - קניית אוכל', 'חילוץ שטח']

st.markdown(
    f"""
    <style>
    .main {{
        background-image: url("{back_ground_url}");
        background-size: 100vw 100vh;  # This sets the size to cover 100% of the viewport width and height
        background-position: center;  
        background-repeat: no-repeat;
    }}
    .stButton button {{
        background-color: rgba(255, 255, 255, 0.8);
        color: black;
        border-radius: 12px;
    }}
    .stTextInput, .stNumberInput input {{
        color: black;
    }}
    .title {{
        background-color: rgba(255, 255, 255, 0.8); /* רקע בהיר */
        color: black !important;
        padding: 10px;
        border-radius: 10px;
    }}
    .header {{
        background-color: rgba(255, 255, 255, 0.8); /* רקע בהיר */
        color: black !important;
        padding: 5px;
        border-radius: 5px;
    }}
    .css-10trblm, .css-1v3fvcr p {{
        color: white !important;
    }}
    .stTitle, .stHeader, .stSubheader, .stMarkdown, .stText, .stNumberInput label, .stDateInput label {{
        color: white !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

st.image(logo_url, width=200)

st.markdown('<h1 class="title">"בחירת מתנדב אופטימלי"</h1>', unsafe_allow_html=True)

st.markdown('<h2 class="header">הזן פרטים לבחירת כונן</h2>', unsafe_allow_html=True)

# קלטים מהמשתמש
location = st.text_input("הכנס מיקום תקלה - קו אורך, קו רוחב לדוגמה 34.784 , 32.085")
caller_id = st.text_input("הכנס מזהה ייחודי של הפונה - שם פרטי ו 4 ספרות אחרונות של ת.ז")
category = st.selectbox("בחר קטגוריה של התקלה", categories)

if st.button("בחר מתנדב"):
    if location and caller_id:
        Volunteer_pool = Volunteer_pool[Volunteer_pool['זמינות'] == 'זמין']

        # הכנת פול של פניות
        calling_pool = pd.DataFrame({
            'מזהה פונה': [caller_id],
            'קטגוריה': [category],
            'מיקום תקלה': [location]
        })

        # הכנת מטריצת העלויות
        cost_matrix = []
        for call_index, call_row in calling_pool.iterrows():
            row = []
            call_location = tuple(map(float, call_row['מיקום תקלה'].split(',')))
            for vol_index, vol_row in Volunteer_pool.iterrows():
                vol_location = tuple(map(float, vol_row['מיקום כונן'].split(',')))
                distance = geodesic(call_location, vol_location).kilometers
                row.append(distance)
            cost_matrix.append(row)

        cost_matrix = np.array(cost_matrix)

        # נרמול ציוני המתנדבים
        def normalize_scores(scores):
            return (scores - scores.min()) / (scores.max() - scores.min())

        volunteer_scores = normalize_scores(Volunteer_pool['final score'])

        # הוספת הציונים למטריצת העלויות
        cost_matrix += volunteer_scores.values.reshape(1, -1)

        # וידוא שהמטריצה ריבועית
        n, m = cost_matrix.shape
        max_dim = max(n, m)
        if n < max_dim:
            cost_matrix = np.vstack([cost_matrix, np.full((max_dim - n, m), 1e6)])
        if m < max_dim:
            cost_matrix = np.hstack([cost_matrix, np.full((max_dim, max_dim - m), 1e6)])

        # ביצוע האלגוריתם ההונגרי
        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        # קבלת התוצאות
        results = []
        for row, col in zip(row_ind, col_ind):
            if row < len(calling_pool) and col < len(Volunteer_pool):
                distance = geodesic(calling_pool.iloc[row]['מיקום תקלה'], Volunteer_pool.iloc[col]['מיקום כונן']).kilometers
                assignment = (
                    calling_pool.iloc[row]['מזהה פונה'],
                    Volunteer_pool.iloc[col]['מזהה כונן'],
                    category,
                    distance
                )
                results.append(assignment)

        results_df = pd.DataFrame(results, columns=['מזהה פונה', 'מזהה כונן', 'קטגוריה', 'מרחק בק"מ'])

        # הצגת התוצאות
        st.write("תוצאות הבחירה:")
        st.dataframe(results_df)

    else:
        st.write("יש להזין את כל השדות.")
