import streamlit as st
import pandas as pd
import requests
import json
import plotly.express as px
from datetime import datetime, date

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(page_title="АРМ Школа 43: ВЕЧНЫЙ", layout="wide")

# !!! СЮДА ВСТАВЬТЕ ССЫЛКУ ИЗ ШАГА 1 !!!
API_URL = "https://api.npoint.io/eb2d450515527689c1a1" 

# --- ФУНКЦИИ ХРАНИЛИЩА ---
def load_data():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200: return response.json()
        else: return {"performance": [], "tasks": [], "rating": [], "oge": [], "vshk": []}
    except:
        return {"performance": [], "tasks": [], "rating": [], "oge": [], "vshk": []}

def save_data(data):
    requests.post(API_URL, json=data)

# Загружаем данные в сессию
if "db" not in st.session_state:
    st.session_state.db = load_data()

# --- АВТОРИЗАЦИЯ ---
if "auth" not in st.session_state: st.session_state.auth = False

def login():
    st.sidebar.title("🔐 Доступ")
    pwd = st.sidebar.text_input("Введите пароль", type="password")
    if st.sidebar.button("Войти"):
        if pwd == "admin123":
            st.session_state.auth = True
            st.rerun()
        else: st.sidebar.error("Ошибка")

if not st.session_state.auth:
    login()
    st.stop()
else:
    # --- НАВИГАЦИЯ ---
    u_fio = st.sidebar.text_input("Ваше ФИО:", "Завуч")
    choice = st.sidebar.radio("МЕНЮ:", ["📊 Аналитика", "📝 Отчеты", "🏆 Рейтинг классов", "🔍 ВШК", "🎓 ОГЭ", "📅 Планы", "💾 Выгрузка"])

    # --- РЕАЛИЗАЦИЯ (ОБЩАЯ ЛОГИКА) ---
    def update_and_sync():
        save_data(st.session_state.db)
        st.success("Данные синхронизированы с облаком!")
        st.rerun()

    if choice == "📝 Отчеты":
        st.header("Внесение отчетов")
        with st.form("per_f", clear_on_submit=True):
            c = st.columns(2)
            term = c[0].selectbox("Четверть", ["1", "2", "3", "4"])
            klass = c[0].text_input("Класс")
            subj = c[1].text_input("Предмет")
            g = st.columns(4)
            g5 = g[0].number_input("5", 0); g2 = g[3].number_input("2", 0)
            if st.form_submit_button("Сохранить"):
                new_row = {"term": term, "klass": klass, "subj": subj, "g5": g5, "g2": g2, "date": str(date.today())}
                st.session_state.db["performance"].append(new_row)
                update_and_sync()
        
        if st.session_state.db["performance"]:
            st.table(pd.DataFrame(st.session_state.db["performance"]))

    elif choice == "📊 Аналитика":
        st.header("Аналитический мониторинг")
        if st.session_state.db["performance"]:
            df = pd.DataFrame(st.session_state.db["performance"])
            st.plotly_chart(px.bar(df, x='klass', y='g5', color='subj', title="Успехи классов (Кол-во '5')"))
        else: st.info("Нет данных")

    elif choice == "📅 Планы":
        st.header("План на месяц")
        with st.form("pl_f"):
            ed = st.date_input("Дата"); ev = st.text_input("Событие"); er = st.text_input("Отв.")
            if st.form_submit_button("Внести"):
                st.session_state.db["tasks"].append({"date": str(ed), "event": ev, "resp": er})
                update_and_sync()
        if st.session_state.db["tasks"]:
            st.table(pd.DataFrame(st.session_state.db["tasks"]))

    elif choice == "💾 Выгрузка":
        st.header("Управление базой")
        if st.button("🔄 Принудительно загрузить данные из облака"):
            st.session_state.db = load_data()
            st.rerun()
        st.info("Данные сохраняются автоматически при каждом нажатии кнопки 'Сохранить'.")