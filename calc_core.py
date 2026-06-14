import numpy as np

class SimulationCore:
    @staticmethod
    def adv_diff_model_2d(params, nx, ny, dx, dy, src_x, src_y, D_coef, mass_rate, dt, U_mesh, V_mesh, river_mask, washout_coef):
        C = np.zeros((ny, nx))
        total_simulation_time = 300.0 
        steps = int(total_simulation_time / dt)
        cell_volume_m3 = dx * dy * params["avg_depth"]
        added_concentration_mg_l = (mass_rate * dt * 1000.0) / cell_volume_m3
        u_pos, u_neg = np.maximum(U_mesh, 0), np.minimum(U_mesh, 0)
        v_pos, v_neg = np.maximum(V_mesh, 0), np.minimum(V_mesh, 0)
        
        for _ in range(steps):
            C[src_y, src_x] += added_concentration_mg_l
            dC = np.zeros_like(C)
            dC[:, 1:] -= u_pos[:, 1:] * (C[:, 1:] - C[:, :-1]) / dx
            dC[:, :-1] -= u_neg[:, :-1] * (C[:, 1:] - C[:, :-1]) / dx
            dC[1:, :] -= v_pos[1:, :] * (C[1:, :] - C[:-1, :]) / dy
            dC[:-1, :] -= v_neg[:-1, :] * (C[1:, :] - C[:-1, :]) / dy
            dC[:, 1:-1] += D_coef * (C[:, 2:] - 2 * C[:, 1:-1] + C[:, :-2]) / (dx**2)
            dC[1:-1, :] += D_coef * (C[2:, :] - 2 * C[1:-1, :] + C[:-2, :]) / (dy**2)
            
            if washout_coef > 0:
                dC -= washout_coef * C
                
            C += dC * dt

            C = np.clip(C, 0.0, 1e6)
            C[~river_mask] = 0
            
        return C