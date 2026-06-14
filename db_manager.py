import os
import psycopg2

class DBManager:
    def __init__(self):
        self.config = {
            "dbname": "VKR",
            "user": "postgres",
            "password": os.getenv("DB_PASSWORD", ""),  
            "host": "localhost",
            "port": "5432"
        }
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        try:
            self.conn = psycopg2.connect(**self.config)
            self.cursor = self.conn.cursor()
        except Exception as e:
            print(f"Предупреждение: Не удалось подключиться к БД ({e}).")
            self.conn = None
            self.cursor = None

    def load_equations(self):
        if not self.cursor: 
            return None
        try:
            self.cursor.execute("SELECT название, формула_latex FROM public.уравнения WHERE название IN ('Сен-Венан', 'Адвекция-Диффузия', 'КФЛ')")
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Ошибка при получении уравнений: {e}")
            return None

    def load_substances(self):
        if not self.cursor: 
            return []
        try:
            self.cursor.execute("SELECT идентификатор_вещества, название, коэффициент_диффузии FROM вещества")
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Ошибка при получении веществ: {e}")
            return []

    def load_weather(self):
        if not self.cursor: 
            return []
        try:
            self.cursor.execute("SELECT идентификатор_погоды, название, модификатор_диффузии, модификатор_скорости, коэффициент_разбавления FROM погодные_условия")
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Ошибка при получении погодных условий: {e}")
            return []

    def save_initial_data(self, params, src_x, src_y, dx, dy, dt, cfl_limit, sub_id, mass_rate, w_id):
        if not self.cursor: 
            return None
        try:
            self.cursor.execute("""
                INSERT INTO проекты (название_сценария, шаг_расчетной_сетки_x, шаг_расчетной_сетки_y, временной_шаг_dt, предельное_значение_кфл) 
                VALUES (%s, %s, %s, %s, %s) RETURNING идентификатор_проекта
            """, ("Моделирование с учетом метеоусловий", float(dx), float(dy), float(dt), float(cfl_limit)))
            pid = self.cursor.fetchone()[0]
            
            self.cursor.execute("""
                INSERT INTO параметры (project_id, sinuosity, width, length, avg_depth, flow_speed, wind_speed) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (pid, params["sinuosity"], params["width"], params["length"], params["avg_depth"], params["flow_speed"], params["wind_speed"], w_id))
            
            self.cursor.execute("""
                INSERT INTO источники_загрязнения (ссылка_на_проект, координата_сброса_x, координата_сброса_y, ссылка_на_вещество, расход_вещества) 
                VALUES (%s, %s, %s, %s, %s)
            """, (pid, float(src_x), float(src_y), sub_id, float(mass_rate)))
            self.conn.commit()
            return pid
        except Exception as e:
            print(f"Ошибка записи параметров в БД: {e}")
            self.conn.rollback()
            return None

    def save_results(self, project_id, max_c):
        if not self.cursor or not project_id: 
            return
        try:
            self.cursor.execute("INSERT INTO результаты_моделирования (ссылка_на_проект, концентрация_вещества) VALUES (%s, %s)", (project_id, max_c))
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка сохранения результатов: {e}")
            self.conn.rollback()

    def close(self):
        if self.conn:
            self.cursor.close()
            self.conn.close()