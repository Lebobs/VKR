import numpy as np
import matplotlib.pyplot as plt

class SimulationVisualizer:
    @staticmethod
    @staticmethod
    def visualize_2d_pollution(concentration, u_mesh, v_mesh, river_mask, src_x_m, src_y_m, params, total_mass, max_c, substance_name, weather_name):
        fig, ax = plt.subplots(figsize=(12, 6))
        ny, nx = concentration.shape
        
        amp_plot = max(0.0, params["sinuosity"] - 0.5) * params["width"] * 1.5
        y_domain_max = (params["width"] * 1.75 + amp_plot + params["width"] / 2) * 1.1
        
        vmax_val = max_c * 0.6 if max_c > 1e-4 else 1.0
        ax.imshow(concentration, origin='lower', cmap='YlOrRd', extent=[0, params["length"], 0, y_domain_max], alpha=0.8, vmax=vmax_val)
        
        x_plot = np.linspace(0, params["length"], 400)
        center_plot = (params["width"] * 1.75) + amp_plot * np.sin(3.5 * np.pi * x_plot / params["length"])
        ax.plot(x_plot, center_plot + params["width"]/2, color='darkblue', linewidth=1.5, label='Берега')
        ax.plot(x_plot, center_plot - params["width"]/2, color='darkblue', linewidth=1.5)
        
        X, Y = np.meshgrid(np.linspace(0, params["length"], nx), np.linspace(0, y_domain_max, ny))
        
        u_viz = np.where(river_mask, u_mesh, np.nan)
        v_viz = np.where(river_mask, v_mesh, np.nan)
        
        stride = 12
        scale = max(params["flow_speed"] * 15, 20) 
        ax.quiver(X[::stride, ::stride], Y[::stride, ::stride], 
                  u_viz[::stride, ::stride], v_viz[::stride, ::stride], 
                  color='blue', alpha=0.6, scale=scale, pivot='mid', width=0.003, label='Течение')
        
        if params["wind_speed"] > 0:
            w_stride = 15
            river_mask_dilated = river_mask.copy()
            for dx_off, dy_off in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                river_mask_dilated |= np.roll(river_mask, shift=(dy_off, dx_off), axis=(0, 1))
            
            X_w, Y_w = X[::w_stride, ::w_stride], Y[::w_stride, ::w_stride]
            mask_w = ~river_mask_dilated[::w_stride, ::w_stride]
            w_u = np.where(mask_w, params["wind_speed"], np.nan)
            w_v = np.zeros_like(w_u)
            
            ax.quiver(X_w, Y_w, w_u, w_v, color='gray', alpha=0.6, scale=150, 
                      pivot='tail', width=0.004, headwidth=4, label='Ветер (над сушей)')
        
        ax.scatter(src_x_m, src_y_m, color='red', marker='*', s=300, edgecolors='white', label='Источник', zorder=10)
        
        info_text = f"СВОДКА:\nВещество: {substance_name}\nПогода: {weather_name}\nГлубина: {params['avg_depth']}м\nМакс. конц: {max_c:.2f} мг/л\nМасса: {total_mass:.2f} кг"
        fig.text(0.81, 0.5, info_text, fontsize=9, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.set_title("Моделирование распространения загрязнителя в водной среде на основе модели 'мелкой воды'")
        ax.set_xlim(0, params["length"])
        ax.set_ylim(0, y_domain_max)
        ax.legend(loc='upper right')
        plt.tight_layout(rect=[0, 0, 0.78, 1])
        plt.show()