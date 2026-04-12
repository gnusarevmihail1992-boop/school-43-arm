import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

# --- 1. CONFIG ---
st.set_page_config(page_title="АРМ Школа: Максимум + ВШК", layout="wide")

RUS_NAMES = {
    'term': 'Четверть', 'klass': 'Класс', 'subject': 'Предмет', 'teacher': 'Учитель',
    'g5': 'Отличники', 'g4': 'Хорошисты', 'g3': 'Тройки', 'g2': 'Задолженность',
    'one_three': 'С одной 3', 'one_four': 'С одной 4', 'date': 'Дата',
    'task': 'Задача', 'fio': 'Исполнитель', 'deadline': 'Срок', 'event': 'Мероприятие',
    'eval_motivation': 'Мотивация', 'eval_content': 'Содержание', 'eval_methods': 'Методы',
    'eval_discipline': 'Дисциплина', 'eval_feedback': 'Обратная связь'
}

# --- 2. DATABASE ---
def get_db():
    conn = sqlite3.connect('school_ultimate_vshk.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS performance 
                 (term TEXT, klass TEXT, subject TEXT, teacher TEXT, 
                  g5 INT, g4 INT, g3 INT, g2 INT, one_three INT, one_four INT)''')
    c.execute('CREATE TABLE IF NOT EXISTS oge_data (fio TEXT, klass TEXT, score INT, grade INT, subject TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS extra_rating (klass TEXT, category TEXT, reason TEXT, points INT, date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS admin_tasks (task TEXT, fio TEXT, deadline TEXT, status TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS school_events (edate TEXT, event TEXT, responsible TEXT)')
    # ТАБЛИЦА ВШК (Внутришкольный контроль)
    c.execute('''CREATE TABLE IF NOT EXISTS vshk_visits 
                 (teacher TEXT, klass TEXT, subject TEXT, goal TEXT, vdate TEXT, 
                  eval_motivation INT, eval_content INT, eval_methods INT, 
                  eval_discipline INT, eval_feedback INT, conclusion TEXT)''')
    conn.commit()
    return conn

db = get_db()

# --- 3. AUTH ---
if "auth" not in st.session_state: st.session_state.auth = False
def login():
    st.sidebar.title("🔐 Авторизация")
    pwd = st.sidebar.text_input("Пароль", type="password")
    if st.sidebar.button("Войти"):
        if pwd == "admin123":
            st.session_state.auth = True
            st.rerun()
        else: st.sidebar.error("Нет доступа")

if not st.session_state.auth:
    login()
else:
    # --- 4. NAVIGATION ---
    st.sidebar.title("🏛️ УПРАВЛЕНИЕ")
    u_name = st.sidebar.text_input("Пользователь:", "Завуч")
    choice = st.sidebar.radio("РАЗДЕЛЫ:", [
        "📊 Дашборд", "🔍 Внутришкольный контроль (ВШК)", "📝 Академические отчеты", 
        "🤖 AI и Красная зона", "🏆 Рейтинг классов", "🎓 Аналитика ОГЭ", 
        "🎯 Адресные задачи", "📅 План на месяц", "💾 Хранилище"
    ])

    # --- РАЗДЕЛ: ВШК (НОВЫЙ) ---
    if choice == "🔍 Внутришкольный контроль (ВШК)":
        st.header("🔍 Система Внутришкольного Контроля")
        tab1, tab2, tab3 = st.tabs(["📋 Карта посещения урока", "📈 Аналитика по учителям", "🗓️ Журнал контроля"])
        
        with tab1:
            st.subheader("Лист наблюдения и анализа урока")
            with st.form("vshk_form", clear_on_submit=True):
                c1, c2 = st.columns(2)
                v_teacher = c1.text_input("ФИО Учителя")
                v_klass = c1.text_input("Класс")
                v_subj = c2.text_input("Предмет")
                v_goal = c2.text_input("Цель посещения")
                
                st.write("**Оценка критериев (1-5 баллов):**")
                g = st.columns(5)
                e_mot = g[0].slider("Мотивация", 1, 5, 4)
                e_con = g[1].slider("Содержание", 1, 5, 4)
                e_met = g[2].slider("Методы", 1, 5, 4)
                e_dis = g[3].slider("Дисциплина", 1, 5, 4)
                e_fed = g[4].slider("Фидбек", 1, 5, 4)
                
                v_conc = st.text_area("Выводы и рекомендации педагогу")
                if st.form_submit_button("СОХРАНИТЬ АНАЛИЗ В БАЗУ"):
                    db.execute("INSERT INTO vshk_visits VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                               (v_teacher, v_klass, v_subj, v_goal, str(date.today()), e_mot, e_con, e_met, e_dis, e_fed, v_conc))
                    db.commit(); st.success("Результаты контроля сохранены!"); st.rerun()

        with tab2:
            st.subheader("Методический профиль педагога")
            df_vshk = pd.read_sql_query("SELECT * FROM vshk_visits", db)
            if not df_vshk.empty:
                sel_t = st.selectbox("Выберите учителя для анализа", df_vshk['teacher'].unique())
                t_data = df_vshk[df_vshk['teacher'] == sel_t]
                
                # Построение лепестковой диаграммы компетенций
                categories = ['Мотивация', 'Содержание', 'Методы', 'Дисциплина', 'Фидбек']
                values = [t_data['eval_motivation'].mean(), t_data['eval_content'].mean(), 
                          t_data['eval_methods'].mean(), t_data['eval_discipline'].mean(), 
                          t_data['eval_feedback'].mean()]
                
                fig = go.Figure(data=go.Scatterpolar(r=values, theta=categories, fill='toself', name=sel_t))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), title=f"Компетенции: {sel_t}")
                st.plotly_chart(fig)
                st.write("Последние рекомендации:", t_data.iloc[-1]['conclusion'])
            else: st.info("Данных контроля еще нет.")

        with tab3:
            st.subheader("История посещений")
            st.dataframe(df_vshk.rename(columns=RUS_NAMES), use_container_width=True)

    # --- РАЗДЕЛ: ДАШБОРД ---
    elif choice == "📊 Дашборд":
        df_p = pd.read_sql_query("SELECT * FROM performance", db)
        if not df_p.empty:
            df_p['Качество %'] = (df_p['g5'] + df_p['g4']) / (df_p['g5'] + df_p['g4'] + df_p['g3'] + df_p['g2']) * 100
            st.plotly_chart(px.bar(df_p, x='klass', y='Качество %', color='subject', title="Свод по школе"), use_container_width=True)
        else: st.info("Данные отсутствуют.")

    # --- РАЗДЕЛ: АКАДЕМИЧЕСКИЕ ОТЧЕТЫ ---
    elif choice == "📝 Академические отчеты":
        t1, t2, t3, t4 = st.tabs(["📉 Четверти", "📚 Предметы", "👥 Классы", "📥 Ввод данных"])
        df = pd.read_sql_query("SELECT * FROM performance", db)
        with t4:
            with st.form("in_f", clear_on_submit=True):
                c = st.columns(2); term = c[0].selectbox("Четверть", ["1","2","3","4","Год"]); kl = c[0].text_input("Класс")
                sj = c[1].text_input("Предмет"); tc = c[1].text_input("Учитель")
                g = st.columns(6)
                g5=g[0].number_input("5", 0); g4=g[1].number_input("4", 0); g3=g[2].number_input("3", 0)
                g2=g[3].number_input("2", 0); o3=g[4].number_input("С одной 3", 0); o4=g[5].number_input("С одной 4", 0)
                if st.form_submit_button("Сохранить"):
                    db.execute("INSERT INTO performance VALUES (?,?,?,?,?,?,?,?,?,?)", (term, kl, sj, tc, g5, g4, g3, g2, o3, o4))
                    db.commit(); st.rerun()
        if not df.empty:
            with t1: st.write(df[df['term'] == st.selectbox("Период", df['term'].unique())])
            with t3: st.table(df[df['klass'] == st.selectbox("Выбор класса", df['klass'].unique())])

    # --- РАЗДЕЛ: AI И КРАСНАЯ ЗОНА ---
    elif choice == "🤖 AI и Красная зона":
        st.subheader("🚨 Красная зона (Задолженности)")
        red = pd.read_sql_query("SELECT * FROM performance WHERE g2 > 0", db)
        if not red.empty: st.error(f"Обнаружено {len(red)} проблемных точек!"); st.dataframe(red)
        else: st.success("Критиков нет.")

    # --- РАЗДЕЛ: РЕЙТИНГ ---
    elif choice == "🏆 Рейтинг классов":
        rv, ri = st.tabs(["📊 Рейтинг", "➕ Ввод"])
        with ri:
            with st.form("r_f"):
                rk = st.text_input("Класс"); rc = st.selectbox("Кат.", ["Дежурство", "Успеваемость", "Мероприятия", "Жизнь"])
                rp = st.number_input("Балл", 0); rr = st.text_input("Причина")
                if st.form_submit_button("OK"):
                    db.execute("INSERT INTO extra_rating VALUES (?,?,?,?,?)", (rk, rc, rr, rp, str(date.today())))
                    db.commit(); st.rerun()
        with rv:
            p = pd.read_sql_query("SELECT klass, SUM(g5) as s5, SUM(g2) as s2 FROM performance GROUP BY klass", db)
            e = pd.read_sql_query("SELECT klass, SUM(points) as pts FROM extra_rating GROUP BY klass", db)
            if not p.empty:
                res = pd.merge(p, e.fillna(0), on='klass', how='left').fillna(0)
                res['ИТОГО'] = res['s5']*2 - res['s2']*5 + res['pts']
                st.table(res.sort_values('ИТОГО', ascending=False))

    # --- ОСТАЛЬНЫЕ РАЗДЕЛЫ КРАТКО ---
    elif choice == "🎓 Аналитика ОГЭ":
        with st.form("oge"):
            f = st.text_input("ФИО"); kl = st.text_input("Класс"); sc = st.number_input("Балл", 0)
            if st.form_submit_button("Анализ"):
                gr = 2 if sc < 15 else (3 if sc < 23 else (4 if sc < 32 else 5))
                db.execute("INSERT INTO oge_data VALUES (?,?,?,?, 'ОГЭ')", (f, kl, sc, gr)); db.commit(); st.rerun()

    elif choice == "🎯 Адресные задачи":
        with st.expander("Новая задача"):
            with st.form("t"):
                tx = st.text_area("Суть"); tf = st.text_input("Кому"); td = st.date_input("Срок")
                if st.form_submit_button("OK"):
                    db.execute("INSERT INTO admin_tasks VALUES (?,?,?, 'В работе')", (tx, tf, str(td))); db.commit(); st.rerun()
        st.table(pd.read_sql_query(f"SELECT * FROM admin_tasks WHERE fio='{u_name}' OR fio='Все'", db))

    elif choice == "📅 План на месяц":
        with st.form("p"):
            ed = st.date_input("Дата"); ev = st.text_input("Событие"); er = st.text_input("Отв.")
            if st.form_submit_button("В план"):
                db.execute("INSERT INTO school_events VALUES (?,?,?)", (str(ed), ev, er)); db.commit(); st.rerun()
        st.table(pd.read_sql_query("SELECT * FROM school_events", db).sort_values('edate'))

    elif choice == "💾 Хранилище":
        st.header("💾 Выгрузка всех данных")
        for t in ["performance", "vshk_visits", "admin_tasks", "oge_data"]:
            df_t = pd.read_sql_query(f"SELECT * FROM {t}", db)
            if not df_t.empty:
                st.download_button(f"Скачать {t.upper()}", df_t.to_csv(index=False).encode('utf-8'), f"{t}.csv")



