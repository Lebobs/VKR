import numpy as np
import tkinter as tk
from tkinter import messagebox, ttk
from tabulate import tabulate

from db_manager import DBManager
from calc_core import SimulationCore
from visualizer import SimulationVisualizer

db = DBManager()

def print_table(data, headers):
    print(tabulate(data, headers=headers, tablefmt="grid"))

def get_pretty_formula(name):
    formulas_map = {
        'Сен-Венан': '∂H/∂t + ∇·(H·v) = 0',
        'Адвекция-Диффузия': '∂C/∂t + v·∇C = D·ΔC',
        'КФЛ': 'dt ≤ min(dx/u, dy/v)'
    }
    return formulas_map.get(name, 'Формула не найдена')

class SimulationGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Моделирование распространения загрязнителя")
        
        self.substances_data = db.load_substances()
        self.substance_names = [sub[1] for sub in self.substances_data] if self.substances_data else ["Нет данных"]
        
        self.weather_data = db.load_weather()
        self.weather_names = [w[1] for w in self.weather_data] if self.weather_data else ["Нет данных"]
        
        self.create_input_panel()
        run_button = tk.Button(self, text="Запустить моделирование", command=self.run_simulation, bg="#e1e1e1", padx=10)
        run_button.pack(pady=15)
    
    def create_input_panel(self):
        frame = tk.Frame(self)
        frame.pack(padx=15, pady=15)
        
        input_width = 30
        combo_width = 28
        
        tk.Label(frame, text="Паттерн участка:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.pattern_entry = tk.Entry(frame, width=input_width)
        self.pattern_entry.insert(0, "Река")
        self.pattern_entry.grid(row=0, column=1, padx=5, pady=4)
        
        tk.Label(frame, text="Извилистость:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.sinuosity_entry = tk.Entry(frame, width=input_width)
        self.sinuosity_entry.insert(0, "1.4")
        self.sinuosity_entry.grid(row=1, column=1, padx=5, pady=4)
        
        tk.Label(frame, text="Ширина (м):").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        self.width_entry = tk.Entry(frame, width=input_width)
        self.width_entry.insert(0, "100")
        self.width_entry.grid(row=2, column=1, padx=5, pady=4)
        
        tk.Label(frame, text="Длина (м):").grid(row=3, column=0, sticky="w", padx=5, pady=4)
        self.length_entry = tk.Entry(frame, width=input_width)
        self.length_entry.insert(0, "700")
        self.length_entry.grid(row=3, column=1, padx=5, pady=4)
        
        tk.Label(frame, text="Глубина (м):").grid(row=4, column=0, sticky="w", padx=5, pady=4)
        self.avg_depth_entry = tk.Entry(frame, width=input_width)
        self.avg_depth_entry.insert(0, "10")
        self.avg_depth_entry.grid(row=4, column=1, padx=5, pady=4)
        
        tk.Label(frame, text="Скорость течения (м/с):").grid(row=5, column=0, sticky="w", padx=5, pady=4)
        self.flow_speed_entry = tk.Entry(frame, width=input_width)
        self.flow_speed_entry.insert(0, "1.0")
        self.flow_speed_entry.grid(row=5, column=1, padx=5, pady=4)
        
        tk.Label(frame, text="Скорость ветра (м/с):").grid(row=6, column=0, sticky="w", padx=5, pady=4)
        self.wind_speed_entry = tk.Entry(frame, width=input_width)
        self.wind_speed_entry.insert(0, "5.0")
        self.wind_speed_entry.grid(row=6, column=1, padx=5, pady=4)
        
        tk.Label(frame, text="Тип токсичного вещества:").grid(row=7, column=0, sticky="w", padx=5, pady=4)
        self.substance_combo = ttk.Combobox(frame, values=self.substance_names, state="readonly", width=combo_width)
        if self.substance_names:
            self.substance_combo.current(0)
        self.substance_combo.grid(row=7, column=1, padx=5, pady=4)

        tk.Label(frame, text="Погодные условия:").grid(row=8, column=0, sticky="w", padx=5, pady=4)
        self.weather_combo = ttk.Combobox(frame, values=self.weather_names, state="readonly", width=combo_width)
        if self.weather_names:
            self.weather_combo.current(0)
        self.weather_combo.grid(row=8, column=1, padx=5, pady=4)

        tk.Label(frame, text="Расход вещества (кг/с):").grid(row=9, column=0, sticky="w", padx=5, pady=4)
        self.mass_rate_entry = tk.Entry(frame, width=input_width)
        self.mass_rate_entry.insert(0, "5.0")
        self.mass_rate_entry.grid(row=9, column=1, padx=5, pady=4)
    
    def run_simulation(self):
        try:
            params = {
                "pattern": self.pattern_entry.get(),
                "sinuosity": float(self.sinuosity_entry.get()),
                "width": float(self.width_entry.get()),
                "length": float(self.length_entry.get()),
                "avg_depth": float(self.avg_depth_entry.get()),
                "flow_speed": float(self.flow_speed_entry.get()),
                "wind_speed": float(self.wind_speed_entry.get())
            }
            mass_rate = float(self.mass_rate_entry.get())
            selected_substance = self.substance_combo.get()
            selected_weather = self.weather_combo.get()
        except ValueError:
            messagebox.showerror("Ошибка", "Введите числовые значения.")
            return

        substance_info = next((s for s in self.substances_data if s[1] == selected_substance), (None, "Неизвестно", 0.5))
        sub_id = substance_info[0]
        D_coef = max(0.01, float(substance_info[2]))

        weather_info = next((w for w in self.weather_data if w[1] == selected_weather), (None, "Ясно (Стандарт)", 1.0, 1.0, 0.0))
        w_id = weather_info[0]
        mod_diff = float(weather_info[2])
        mod_speed = float(weather_info[3])
        washout_coef = float(weather_info[4])

        D_coef *= mod_diff
        params["flow_speed"] *= mod_speed

        nx, ny = 120, 120
        y_domain_max = params["width"] * 3.5
        dx = params["length"] / nx
        dy = y_domain_max / ny
        
        src_x_m = params["length"] * 0.15
        amp = max(0.0, params["sinuosity"] - 1.0) * params["width"] * 1.5
        src_y_m = (params["width"] * 1.75) + amp * np.sin(3.5 * np.pi * src_x_m / params["length"])
        
        src_x = int(np.clip(src_x_m / dx, 0, nx - 1))
        src_y = int(np.clip(src_y_m / dy, 0, ny - 1))
        
        X_m, Y_m = np.meshgrid(np.arange(nx) * dx, np.arange(ny) * dy)
        river_center = (params["width"] * 1.75) + amp * np.sin(3.5 * np.pi * X_m / params["length"])
        river_mask = (Y_m >= river_center - params["width"] / 2) & (Y_m <= river_center + params["width"] / 2)
        
        theta = np.arctan(amp * (3.5 * np.pi / params["length"]) * np.cos(3.5 * np.pi * X_m / params["length"]))
        U_mesh = params["flow_speed"] * np.cos(theta)
        V_mesh = params["flow_speed"] * np.sin(theta)
        
        max_u = np.max(np.abs(U_mesh)) + 1e-6
        max_v = np.max(np.abs(V_mesh)) + 1e-6
        
        cfl_limit = 1.0 / (max_u / dx + max_v / dy + 2.0 * D_coef / (dx**2) + 2.0 * D_coef / (dy**2))
        dt = cfl_limit * 0.40 
        
        project_id = db.save_initial_data(params, src_x_m, src_y_m, dx, dy, dt, cfl_limit, sub_id, mass_rate, w_id)
        
        concentration = SimulationCore.adv_diff_model_2d(params, nx, ny, dx, dy, src_x, src_y, D_coef, mass_rate, dt, U_mesh, V_mesh, river_mask, washout_coef)
        
        cell_volume = dx * dy * params["avg_depth"]
        mass_in_water_kg = float(np.sum(concentration) * cell_volume / 1000.0)
        max_concentration = float(concentration.max())
        
        db.save_results(project_id, max_concentration)
        SimulationVisualizer.visualize_2d_pollution(concentration, U_mesh, V_mesh, river_mask, src_x_m, src_y_m, params, y_domain_max, mass_in_water_kg, max_concentration, selected_substance, selected_weather)

if __name__ == "__main__":
    if db.cursor:
        formulas = db.load_equations()
        if formulas:
            print_table([[n, get_pretty_formula(n)] for n, _ in formulas], ["Название", "Формула"])
    app = SimulationGUI()
    app.mainloop()
    db.close()