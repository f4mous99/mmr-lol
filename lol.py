import requests
import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading

# Configuración de la API (usar variable de entorno en producción)
api_key = ''

# --- Funciones auxiliares ---
def roman_to_number(roman):
    conversion = {'IV': 4, 'III': 3, 'II': 2, 'I': 1, '': 0}
    return conversion.get(roman, 0)

def get_rank_from_mmr(mmr):
    ranges = [
        (2800, "CHALLENGER", ""),
        (2600, "GRANDMASTER", ""),
        (2400, "MASTER", ""),
        (2200, "DIAMOND", 1),
        (2100, "DIAMOND", 2),
        (2000, "DIAMOND", 3),
        (1900, "DIAMOND", 4),
        (1800, "EMERALD", 1),
        (1700, "EMERALD", 2),
        (1600, "EMERALD", 3),
        (1500, "EMERALD", 4),
        (1400, "PLATINUM", 1),
        (1300, "PLATINUM", 2),
        (1200, "PLATINUM", 3),
        (1100, "PLATINUM", 4),
        (1000, "GOLD", 1),
        (900, "GOLD", 2),
        (800, "GOLD", 3),
        (700, "GOLD", 4),
        (600, "SILVER", 1),
        (500, "SILVER", 2),
        (400, "SILVER", 3),
        (300, "SILVER", 4),
        (200, "BRONZE", 1),
        (100, "BRONZE", 2),
        (0, "IRON", 1)
    ]
    
    for limit, tier, division in ranges:
        if mmr >= limit:
            return f"{tier.upper()} {division}" if division else f"{tier.upper()}"
    return "IRON"

# --- Funciones de la API ---
def get_puuid(api_key, game_name, tag_line):
    url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    headers = {'X-Riot-Token': api_key}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get('puuid')
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error al obtener PUUID: {e}")

def get_summoner_id(api_key, puuid):
    url = f"https://la2.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    headers = {'X-Riot-Token': api_key}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get('id')
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error al obtener Summoner ID: {e}")

def get_ranked_info_solo_duo(api_key, summoner_id):
    url = f"https://la2.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}"
    headers = {'X-Riot-Token': api_key}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        for entry in response.json():
            if entry['queueType'] == 'RANKED_SOLO_5x5':
                return entry
        return None
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error al obtener ranking: {e}")

def get_match_history_solo_duo(api_key, puuid):
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
    headers = {'X-Riot-Token': api_key}
    params = {'queue': 420, 'count': 90}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error al obtener historial: {e}")

def get_match_details(api_key, match_id):
    url = f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}"
    headers = {'X-Riot-Token': api_key}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error en detalles de partida: {e}")

def calculate_mmr(tier, rank, lp, win_rate):
    tier_values = {
        'IRON': 0, 'BRONZE': 200, 'SILVER': 400,
        'GOLD': 600, 'PLATINUM': 1000, 'EMERALD': 1400,
        'DIAMOND': 1800, 'MASTER': 2200, 'GRANDMASTER': 2400,
        'CHALLENGER': 2600
    }
    
    rank_value = roman_to_number(rank) * 25
    base_mmr = tier_values.get(tier.upper(), 0) + rank_value + lp
    adjusted_mmr = base_mmr + (win_rate - 50) * 1.5
    
    return int(adjusted_mmr)

# --- Interfaz Gráfica ---
class MMRCalculatorApp:
    def __init__(self, root):
        self.root = root
        root.title("Calculadora de MMR - LoL")
        root.geometry("800x500")
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configuración de estilos
        self.style.configure(
            'TEntry',
            fieldbackground='#444444',
            foreground='white',
            insertbackground='white',
            padding=5,
            bordercolor='',
            troughcolor='#333333',        
            lightcolor='#00b8d4',
            darkcolor='#00b8d4',


        )       
        self.style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor='#333333',
            background='#00b8d4',  # Color celeste
            bordercolor='#333333',
            lightcolor='#00b8d4',
            darkcolor='#00b8d4',
            thickness=20
        )
        
        self.style.configure('TLabel', background='#333333', foreground='white', padding=5)
        self.style.configure('TFrame', background='#333333')
        
        main_frame = ttk.Frame(root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configurar grid responsivo
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=3)
        
        # Etiquetas y campos de entrada
        ttk.Label(main_frame, text="Nombre de Invocador:").grid(
            row=0, column=0, pady=5, sticky=tk.E, padx=(0, 10))
        
        self.game_name_entry = ttk.Entry(main_frame, width=30, style='TEntry')
        self.game_name_entry.grid(
            row=0, column=1, pady=5, sticky=tk.EW, padx=(0, 20))
        
        ttk.Label(main_frame, text="Tag (ej: LAS):").grid(
            row=1, column=0, pady=5, sticky=tk.E, padx=(0, 10))
        
        self.tag_entry = ttk.Entry(main_frame, width=15, style='TEntry')
        self.tag_entry.grid(
            row=1, column=1, pady=5, sticky=tk.W, padx=(0, 20))
        
        # Barra de progreso
        self.progress = ttk.Progressbar(
            main_frame, style="Custom.Horizontal.TProgressbar", orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress.grid(
            row=2, column=0, columnspan=2, pady=15, sticky=tk.EW, padx=20)
        
        # Área de resultados
        self.results_text = tk.Text(
            main_frame, height=15, width=60, 
            bg='#222222', fg='white', state=tk.DISABLED)
        self.results_text.grid(
            row=3, column=0, columnspan=2, pady=10, sticky=tk.NSEW, padx=20)
        
        # Botón
        self.calculate_btn = ttk.Button(main_frame, text="Calcular MMR", command=self.start_calculation)
        self.calculate_btn.grid(
            row=4, column=0, columnspan=2, pady=10, sticky=tk.EW, padx=20)
        
        # Hacer expandible el área de texto
        main_frame.rowconfigure(3, weight=1)
    def start_calculation(self):
        self.calculate_btn.config(state=tk.DISABLED)
        self.progress['value'] = 0
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.config(state=tk.DISABLED)
        threading.Thread(target=self.calculate_mmr).start()
    
    def update_progress(self, value):
        self.progress['value'] = value
        self.root.update_idletasks()
    
    def log_message(self, message):
        self.results_text.config(state=tk.NORMAL)
        self.results_text.insert(tk.END, message + "\n")
        self.results_text.see(tk.END)
        self.results_text.config(state=tk.DISABLED)
    
    def calculate_mmr(self):
        try:
            game_name = self.game_name_entry.get().strip()
            tag_line = self.tag_entry.get().strip()
            
            if not game_name or not tag_line:
                messagebox.showwarning("Error", "Ingresa nombre y tag")
                return
            
            # Paso 1: Obtener PUUID
            self.log_message("[1/5] Encontrando Jugador...")
            puuid = get_puuid(api_key, game_name, tag_line)
            self.update_progress(20)
            
            # Paso 2: Obtener historial de partidas
            self.log_message("[2/5] Analizando partidas...")
            match_ids = get_match_history_solo_duo(api_key, puuid)
            self.update_progress(40)
            
            # Paso 3: Calcular Win Rate
            self.log_message("[3/5] Calculando rendimiento...")
            wins, losses = 0, 0
            for match_id in match_ids[:90]:
                match_data = get_match_details(api_key, match_id)
                for participant in match_data['info']['participants']:
                    if participant['puuid'] == puuid:
                        if participant['win']:
                            wins += 1
                        else:
                            losses += 1
            total_games = wins + losses
            if total_games == 0:
             raise Exception("No hay partidas recientes en Solo/Duo.")
            win_rate = round((wins / total_games * 100), 2) if total_games > 0 else 0
            self.update_progress(60)
            
            # Paso 4: Obtener rango actual
            self.log_message("[4/5] Obteniendo ranking...")
            summoner_id = get_summoner_id(api_key, puuid)
            ranked_info = get_ranked_info_solo_duo(api_key, summoner_id)
            self.update_progress(80)
            
            # Paso 5: Calcular MMR
            self.log_message("[5/5] Calculando MMR...")
            if ranked_info:
                tier = ranked_info['tier']
                rank = ranked_info.get('rank', '')
                lp = ranked_info['leaguePoints']
                mmr = calculate_mmr(tier, rank, lp, win_rate)
                estimated_rank = get_rank_from_mmr(mmr)
                
                result = (
                    f"\nResultados:\n"
                    f"Rango Actual: {tier} {rank} ({lp} LP)\n"
                    f"Win Rate: {win_rate}% ({wins}W {losses}L)\n"
                    f"MMR Estimado: {estimated_rank}\n"
                    f"Puntos MMR: {mmr}"
                )
            else:
                result = "\nJugador sin rango en Solo/Duo"
            
            self.log_message(result)
            self.update_progress(100)
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.calculate_btn.config(state=tk.NORMAL)
            self.update_progress(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = MMRCalculatorApp(root)
    root.mainloop()
