import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime, date

# --- 1. НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(page_title="АРМ Школа PRO: Стабильная версия", layout="wide")

# Словарь перевода для таблиц
RUS = {
    'term': 'Четверть', 'klass': 'Класс', 'subject': 'Предмет', 'teacher': 'Учитель',
    'g5': '5', 'g4': '4', 'g3': '3', 'g2': '2 (Задолж)',
    'one_three': 'С одной 3', 'one_four': 'С одной 4', 'date': 'Дата',
    'task': 'Задача', 'fio': 'Исполнитель', 'deadline': 'Срок', 'status': 'Статус', 
    'category': 'Категория', 'reason': 'Причина', 'points': 'Баллы', 'event': 'Событие'
}

# --- 2. РАБОТА С БАЗОЙ ДАННЫХ ---
def get_db_connection():
    conn = sqlite3.connect('school_stable_v8.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS performance (term TEXT, klass TEXT, subject TEXT, teacher TEXT, g5 INT, g4 INT, g3 INT, g2 INT, one_three INT, one_four INT)')
    c.execute('CREATE TABLE IF NOT EXISTS oge_data (fio TEXT, klass TEXT, score INT, grade INT, subject TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS extra_rating (klass TEXT, category TEXT, reason TEXT, points INT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS admin_tasks (task TEXT, fio TEXT, deadline TEXT, status TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS school_events (edate TEXT, event TEXT, responsible TEXT)')
    conn.commit()
    conn.close()

init_db()

# --- 3. АВТОРИЗАЦИЯ ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def login_form():
    st.sidebar.title("🔐 Авторизация")
    pwd = st.sidebar.text_input("Введите пароль", type="password", key="login_pwd")
    if st.sidebar.button("Войти", key="login_btn"):
        if pwd == "admin123":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.sidebar.error("Неверный пароль")

if not st.session_state.authenticated:
    login_form()
else:
    # --- 4. НАВИГАЦИЯ ---
    st.sidebar.title("🏛️ УПРАВЛЕНИЕ ШКОЛОЙ")
    current_user = st.sidebar.text_input("Ваше ФИО:", "Администратор", key="user_name")
    
    choice = st.sidebar.radio("МЕНЮ РАЗДЕЛОВ:", [
        "📊 Главный Дашборд", 
        "🤖 AI и Красная зона",
        "📝 Академические отчеты", 
        "🏆 Рейтинг классов", 
        "🎓 Аналитика ОГЭ", 
        "🎯 Адресные задачи", 
        "📅 План на месяц",
        "💾 Выгрузка данных"
    ], key="main_menu")

    conn = get_db_connection()

    # --- РАЗДЕЛ: ДАШБОРД ---
    if choice == "📊 Главный Дашборд":
        st.header("📊 Мониторинг качества образования")
        df = pd.read_sql_query("SELECT * FROM performance", conn)
        if not df.empty:
            df['Качество %'] = (df['g5'] + df['g4']) / (df['g5'] + df['g4'] + df['g3'] + df['g2']) * 100
            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                st.plotly_chart(px.bar(df, x='klass', y='Качество %', color='subject', title="Качество по классам"), use_container_width=True, key="chart_q")
            with col_chart2:
                st.plotly_chart(px.pie(df, values='g5', names='klass', title="Доля отличников"), use_container_width=True, key="chart_p")
        else:
            st.info("Данные успеваемости еще не внесены в базу.")

    # --- РАЗДЕЛ: AI И КРАСНАЯ ЗОНА ---
    elif choice == "🤖 AI и Красная зона":
        st.header("🚨 Красная зона: Анализ рисков")
        df_red = pd.read_sql_query("SELECT * FROM performance WHERE g2 > 0", conn)
        if not df_red.empty:
            st.error(f"ВНИМАНИЕ: Обнаружено {len(df_red)} случаев задолженностей!")
            st.dataframe(df_red.rename(columns=RUS), use_container_width=True)
        else:
            st.success("Критических проблем с неуспеваемостью не выявлено.")

    # --- РАЗДЕЛ: АКАДЕМИЧЕСКИЕ ОТЧЕТЫ ---
    elif choice == "📝 Академические отчеты":
        t1, t2, t3, t4 = st.tabs(["📊 По четвертям", "📚 По предметам", "👥 По классам", "📥 Ввод данных"])
        df_perf = pd.read_sql_query("SELECT * FROM performance", conn)
        
        with t4:
            with st.form("add_per_form"):
                e1, e2 = st.columns(2)
                f_term = e1.selectbox("Четверть", ["1", "2", "3", "4", "Год"], key="f_term")
                f_klass = e1.text_input("Класс", key="f_kl")
                f_subj = e2.text_input("Предмет", key="f_sj")
                f_teach = e2.text_input("Учитель", key="f_tc")
                st.write("Количество оценок:")
                g = st.columns(6)
                v5 = g[0].number_input("5", 0, key="v5")
                v4 = g[1].number_input("4", 0, key="v4")
                v3 = g[2].number_input("3", 0, key="v3")
                v2 = g[3].number_input("2", 0, key="v2")
                o3 = g[4].number_input("С одной 3", 0, key="vo3")
                o4 = g[5].number_input("С одной 4", 0, key="vo4")
                if st.form_submit_button("СОХРАНИТЬ ОТЧЕТ"):
                    conn.execute("INSERT INTO performance VALUES (?,?,?,?,?,?,?,?,?,?)", (f_term, f_klass, f_subj, f_teach, v5, v4, v3, v2, o3, o4))
                    conn.commit()
                    st.success("Данные сохранены!")
                    st.rerun()

        if not df_perf.empty:
            df_v = df_perf.rename(columns=RUS)
            with t1: st.dataframe(df_v[df_v['Четверть'] == st.selectbox("Выбор четверти", df_perf['term'].unique(), key="s1")], use_container_width=True)
            with t2: st.dataframe(df_v[df_v['Предмет'] == st.selectbox("Выбор предмета", df_perf['subject'].unique(), key="s2")], use_container_width=True)
            with t3: st.write(df_v[df_v['Класс'] == st.selectbox("Выбор класса", df_perf['klass'].unique(), key="s3")])

    # --- РАЗДЕЛ: РЕЙТИНГ КЛАССОВ ---
    elif choice == "🏆 Рейтинг классов":
        rt1, rt2 = st.tabs(["📈 Итоговый рейтинг", "➕ Добавить показатели"])
        with rt2:
            with st.form("add_rating"):
                rk = st.text_input("Класс", key="rk")
                rc = st.selectbox("Категория", ["Дежурство", "Успеваемость", "Участие в мероприятиях", "Школьная жизнь"], key="rcAT")
                rr = st.text_input("Причина / Событие", key="rr")
                rp = st.number_input("Баллы", value=0, key="rp")
                if st.form_submit_button("Начислить баллы"):
                    conn.execute("INSERT INTO extra_rating VALUES (?,?,?,?,?)", (rk, rc, rr, rp, str(date.today())))
                    conn.commit(); st.success("Баллы внесены!"); st.rerun()
        
        with rt1:
            p = pd.read_sql_query("SELECT klass, SUM(g5) as s5, SUM(g2) as s2 FROM performance GROUP BY klass", conn)
            e = pd.read_sql_query("SELECT klass, SUM(points) as pts FROM extra_rating GROUP BY klass", conn)
            if not p.empty:
                res = pd.merge(p, e.fillna(0), on='klass', how='left').fillna(0)
                res['Итоговый балл'] = res['s5']*2 - res['s2']*5 + res['pts']
                st.table(res.sort_values('Итоговый балл', ascending=False).rename(columns={'klass':'Класс', 'pts':'Бонусы'}))

    # --- РАЗДЕЛ: ОГЭ ---
    elif choice == "🎓 Аналитика ОГЭ":
        with st.form("oge_add"):
            coge = st.columns(2)
            of = coge[0].text_input("ФИО ученика", key="of")
            ok = coge[0].text_input("Класс", key="ok")
            os = coge[1].number_input("Балл", 0, key="os")
            osub = coge[1].text_input("Предмет", key="osub")
            if st.form_submit_button("Анализ пробника"):
                ogr = 2 if os < 15 else (3 if os < 23 else (4 if os < 32 else 5))
                conn.execute("INSERT INTO oge_data VALUES (?,?,?,?,?)", (of, ok, os, ogr, osub))
                conn.commit(); st.success("Данные в базе"); st.rerun()
        oge_df = pd.read_sql_query("SELECT * FROM oge_data", conn)
        if not oge_df.empty: st.write(oge_df.rename(columns=RUS))

    # --- РАЗДЕЛ: ЗАДАЧИ ---
    elif choice == "🎯 Адресные задачи":
        st.subheader(f"Задачи для: {current_user}")
        my_tasks = pd.read_sql_query(f"SELECT * FROM admin_tasks WHERE fio='{current_user}' OR fio='Все'", conn)
        st.dataframe(my_tasks.rename(columns=RUS), use_container_width=True)
        with st.expander("➕ Новая задача"):
            with st.form("new_task"):
                t_tx = st.text_area("Суть задачи", key="ttx")
                t_f = st.text_input("ФИО Исполнителя", key="tfio")
                t_d = st.date_input("Срок", key="tdead")
                if st.form_submit_button("Утвердить"):
                    conn.execute("INSERT INTO admin_tasks VALUES (?,?,?,?)", (t_tx, t_f, str(t_d), "В работе"))
                    conn.commit(); st.success("Задача поставлена"); st.rerun()

    # --- РАЗДЕЛ: ПЛАН НА МЕСЯЦ ---
    elif choice == "📅 План на месяц":
        with st.form("plan_f"):
            pd1 = st.date_input("Дата", key="pd")
            pe1 = st.text_input("Мероприятие", key="pe")
            pr1 = st.text_input("Кто отвечает", key="pr")
            if st.form_submit_button("Добавить в план"):
                conn.execute("INSERT INTO school_events VALUES (?,?,?)", (str(pd1), pe1, pr1))
                conn.commit(); st.success("Событие добавлено!"); st.rerun()
        pl_df = pd.read_sql_query("SELECT * FROM school_events", conn).sort_values('edate')
        st.table(pl_df.rename(columns={'edate':'Дата','event':'Событие','responsible':'Ответственный'}))

    # --- РАЗДЕЛ: ВЫГРУЗКА ---
    elif choice == "💾 Выгрузка данных":
        st.header("💾 Управление базой данных")
        t_name = st.selectbox("Выберите таблицу для скачивания", ["performance", "oge_data", "extra_rating", "admin_tasks", "school_events"])
        df_exp = pd.read_sql_query(f"SELECT * FROM {t_name}", conn)
        if not df_exp.empty:
            csv = df_exp.to_csv(index=False).encode('utf-8')
            st.download_button("СКАЧАТЬ В EXCEL (CSV)", csv, f"{t_name}.csv", "text/csv")

    conn.close()


