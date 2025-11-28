import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import requests
import json
import os

class EchoVRFollowMe:
    def __init__(self, root):
        self.root = root
        self.root.title("Echo VR Camera Follower")
        self.root.geometry("400x600")
        self.root.resizable(False, False)
        
        self.bg_color = "#2b2b2b"
        self.card_color = "#3c3f41"
        self.accent_color = "#4a9cff"
        self.text_color = "#ffffff"
        self.subtle_text = "#aaaaaa"
        
        self.root.configure(bg=self.bg_color)
        
        self.target_player = ""
        self.is_monitoring = False
        self.base_url = "http://127.0.0.1:6721"
        self.verified_camera_index = None
        self.config_file = "config.json"
        
        # UI visibility states
        self.ui_visibility_var = tk.BooleanVar()
        self.nameplates_visibility_var = tk.BooleanVar()
        self.minimap_visibility_var = tk.BooleanVar()
        self.enemy_team_muted_var = tk.BooleanVar()
        
        # Load config
        self.config = self.load_config()
        self.corrections = self.config.get("corrections", {})
        self.last_username = self.config.get("last_username", "")
        
        # Load UI settings from config
        self.ui_visibility_var.set(self.config.get("ui_visibility", False))
        self.nameplates_visibility_var.set(self.config.get("nameplates_visibility", False))
        self.minimap_visibility_var.set(self.config.get("minimap_visibility", False))
        self.enemy_team_muted_var.set(self.config.get("enemy_team_muted", False))
        
        self.create_ui()
        
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                return {"corrections": {}, "last_username": ""}
        return {"corrections": {}, "last_username": ""}
    
    def save_config(self):
        """Save configuration to file"""
        try:
            # Update config with current UI settings
            self.config.update({
                "ui_visibility": self.ui_visibility_var.get(),
                "nameplates_visibility": self.nameplates_visibility_var.get(),
                "minimap_visibility": self.minimap_visibility_var.get(),
                "enemy_team_muted": self.enemy_team_muted_var.get()
            })
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Failed to save config: {e}")
    
    def create_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg=self.bg_color, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=self.bg_color)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title = tk.Label(header_frame, text="ECHO VR CAMERA FOLLOWER", 
                        font=("Arial", 16, "bold"), fg=self.accent_color, bg=self.bg_color)
        title.pack()
        
        subtitle = tk.Label(header_frame, text="Auto-spectate players in Echo VR", 
                           font=("Arial", 10), fg=self.subtle_text, bg=self.bg_color)
        subtitle.pack(pady=(5, 0))
        
        # Player Card
        player_card = tk.Frame(main_frame, bg=self.card_color, relief=tk.FLAT, bd=0)
        player_card.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(player_card, text="PLAYER TO FOLLOW", font=("Arial", 9, "bold"), 
                fg=self.subtle_text, bg=self.card_color).pack(anchor=tk.W, padx=15, pady=(15, 5))
        
        input_frame = tk.Frame(player_card, bg=self.card_color)
        input_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        self.player_entry = tk.Entry(input_frame, font=("Arial", 12), bg="#505050", 
                                   fg=self.text_color, insertbackground=self.text_color,
                                   relief=tk.FLAT, bd=0)
        self.player_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8)
        self.player_entry.insert(0, self.last_username)
        self.player_entry.bind('<Return>', lambda e: self.set_target_player())
        
        set_btn = tk.Button(input_frame, text="SET", font=("Arial", 10, "bold"), 
                           bg=self.accent_color, fg=self.text_color, relief=tk.FLAT, bd=0,
                           command=self.set_target_player, padx=20)
        set_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        camera_card = tk.Frame(main_frame, bg=self.card_color, relief=tk.FLAT, bd=0)
        camera_card.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(camera_card, text="CAMERA CONTROL", font=("Arial", 9, "bold"), 
                fg=self.subtle_text, bg=self.card_color).pack(anchor=tk.W, padx=15, pady=(15, 10))
        
        camera_display_frame = tk.Frame(camera_card, bg=self.card_color)
        camera_display_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        self.camera_display = tk.Label(camera_display_frame, text="--", font=("Arial", 32, "bold"), 
                                      fg=self.accent_color, bg=self.card_color)
        self.camera_display.pack()
        
        camera_label = tk.Label(camera_display_frame, text="CURRENT CAMERA", font=("Arial", 9), 
                               fg=self.subtle_text, bg=self.card_color)
        camera_label.pack()
        
        adjust_frame = tk.Frame(camera_card, bg=self.card_color)
        adjust_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        minus_btn = tk.Button(adjust_frame, text="−", font=("Arial", 16, "bold"), 
                             bg="#505050", fg=self.text_color, relief=tk.FLAT, bd=0,
                             command=lambda: self.adjust_camera(-1), width=3)
        minus_btn.pack(side=tk.LEFT)
        
        plus_btn = tk.Button(adjust_frame, text="+", font=("Arial", 16, "bold"), 
                            bg="#505050", fg=self.text_color, relief=tk.FLAT, bd=0,
                            command=lambda: self.adjust_camera(1), width=3)
        plus_btn.pack(side=tk.RIGHT)

        ui_card = tk.Frame(main_frame, bg=self.card_color, relief=tk.FLAT, bd=0)
        ui_card.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(ui_card, text="UI CONTROLS", font=("Arial", 9, "bold"), 
                fg=self.subtle_text, bg=self.card_color).pack(anchor=tk.W, padx=15, pady=(15, 10))

        ui_frame = tk.Frame(ui_card, bg=self.card_color)
        ui_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        row1 = tk.Frame(ui_frame, bg=self.card_color)
        row1.pack(fill=tk.X, pady=(0, 8))
        
        self.ui_checkbox = tk.Checkbutton(row1, text="Hide UI", variable=self.ui_visibility_var,
                                        command=self.toggle_ui_visibility, bg=self.card_color,
                                        fg=self.text_color, selectcolor="#505050",
                                        activebackground=self.card_color, activeforeground=self.text_color)
        self.ui_checkbox.pack(side=tk.LEFT)
        
        self.nameplates_checkbox = tk.Checkbutton(row1, text="Hide Nameplates", variable=self.nameplates_visibility_var,
                                                command=self.toggle_nameplates_visibility, bg=self.card_color,
                                                fg=self.text_color, selectcolor="#505050",
                                                activebackground=self.card_color, activeforeground=self.text_color)
        self.nameplates_checkbox.pack(side=tk.RIGHT)

        row2 = tk.Frame(ui_frame, bg=self.card_color)
        row2.pack(fill=tk.X)
        
        self.minimap_checkbox = tk.Checkbutton(row2, text="Hide Minimap", variable=self.minimap_visibility_var,
                                             command=self.toggle_minimap_visibility, bg=self.card_color,
                                             fg=self.text_color, selectcolor="#505050",
                                             activebackground=self.card_color, activeforeground=self.text_color)
        self.minimap_checkbox.pack(side=tk.LEFT)
        
        self.mute_checkbox = tk.Checkbutton(row2, text="Mute Enemy Team", variable=self.enemy_team_muted_var,
                                          command=self.toggle_enemy_team_muted, bg=self.card_color,
                                          fg=self.text_color, selectcolor="#505050",
                                          activebackground=self.card_color, activeforeground=self.text_color)
        self.mute_checkbox.pack(side=tk.RIGHT)
        
        control_card = tk.Frame(main_frame, bg=self.card_color, relief=tk.FLAT, bd=0)
        control_card.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(control_card, text="CONTROLS", font=("Arial", 9, "bold"), 
                fg=self.subtle_text, bg=self.card_color).pack(anchor=tk.W, padx=15, pady=(15, 10))
        
        btn_frame = tk.Frame(control_card, bg=self.card_color)
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        self.start_btn = tk.Button(btn_frame, text="START FOLLOWING", font=("Arial", 11, "bold"), 
                                  bg="#27ae60", fg=self.text_color, relief=tk.FLAT, bd=0,
                                  command=self.start_following, state=tk.DISABLED, padx=30, pady=12)
        self.start_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.stop_btn = tk.Button(btn_frame, text="STOP", font=("Arial", 11, "bold"), 
                                 bg="#e74c3c", fg=self.text_color, relief=tk.FLAT, bd=0,
                                 command=self.stop_following, state=tk.DISABLED, padx=30, pady=12)
        self.stop_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        status_card = tk.Frame(main_frame, bg=self.card_color, relief=tk.FLAT, bd=0)
        status_card.pack(fill=tk.X)
        
        tk.Label(status_card, text="STATUS", font=("Arial", 9, "bold"), 
                fg=self.subtle_text, bg=self.card_color).pack(anchor=tk.W, padx=15, pady=(15, 10))
        
        self.status_label = tk.Label(status_card, text="Enter player name to begin", 
                                    font=("Arial", 11), fg=self.text_color, bg=self.card_color, 
                                    wraplength=350, justify=tk.LEFT)
        self.status_label.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        footer_frame = tk.Frame(main_frame, bg=self.bg_color)
        footer_frame.pack(fill=tk.X, pady=(20, 0))
        
        footer_text = tk.Label(footer_frame, text="Settings are saved automatically", 
                             font=("Arial", 9), fg=self.subtle_text, bg=self.bg_color)
        footer_text.pack()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def send_ui_command(self, endpoint, value):
        """Send UI visibility command to Echo VR"""
        try:
            payload = {"visible": value}
            response = requests.post(f"{self.base_url}/{endpoint}", json=payload, timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def toggle_ui_visibility(self):
        """Toggle UI visibility"""
        value = not self.ui_visibility_var.get() 
        if self.send_ui_command("ui_visibility", value):
            self.save_config()
    
    def toggle_nameplates_visibility(self):
        """Toggle nameplates visibility"""
        value = not self.nameplates_visibility_var.get()  
        if self.send_ui_command("nameplates_visibility", value):
            self.save_config()
    
    def toggle_minimap_visibility(self):
        """Toggle minimap visibility"""
        value = not self.minimap_visibility_var.get() 
        if self.send_ui_command("minimap_visibility", value):
            self.save_config()
    
    def toggle_enemy_team_muted(self):
        """Toggle enemy team muted"""
        value = self.enemy_team_muted_var.get()
        if self.send_ui_command("enemy_team_muted", value):
            self.save_config()
    
    def update_status(self, message, is_error=False):
        """Update status message with color coding"""
        color = "#e74c3c" if is_error else self.text_color
        self.status_label.config(text=message, fg=color)
    
    def update_camera_display(self, camera_index):
        """Update the camera number display"""
        if camera_index:
            self.camera_display.config(text=str(camera_index))
        else:
            self.camera_display.config(text="--")
    
    def get_session_data(self):
        """Get session data from Echo VR"""
        try:
            response = requests.get(f"{self.base_url}/session", timeout=2)
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def switch_camera_to_index(self, camera_index):
        """Switch camera to specific index"""
        camera_mode = "pov" 
        
        try:
            payload = {"mode": camera_mode, "num": camera_index}
            response = requests.post(f"{self.base_url}/camera_mode", json=payload, timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def build_camera_mapping(self):
        """Build camera to player mapping from session data"""
        session_data = self.get_session_data()
        if not session_data:
            return {}
            
        camera_mapping = {}
        teams = session_data.get("teams", [])
        
        for team in teams:
            team_name = team.get("team", "Unknown")
            players = team.get("players", [])
            
            for player_index, player in enumerate(players):
                player_name = player.get("name", "Unknown")
                if "ORANGE" in team_name.upper():
                    camera_index = player_index + 1
                else:
                    camera_index = player_index + 6
                
                camera_mapping[camera_index] = player_name
        
        return camera_mapping
    
    def get_api_suggested_camera(self, player_name):
        """Get the camera index that API suggests for this player"""
        camera_mapping = self.build_camera_mapping()
        
        for camera_index, mapped_player in camera_mapping.items():
            if mapped_player.lower() == player_name.lower():
                return camera_index
        return None
    
    def apply_correction(self, player_name, api_camera):
        """Apply saved correction for player"""
        if player_name in self.corrections:
            correction = self.corrections[player_name]
            corrected_camera = api_camera + correction
            return corrected_camera
        return api_camera
    
    def set_target_player(self):
        player_name = self.player_entry.get().strip()
        if not player_name:
            self.update_status("Please enter a player name", is_error=True)
            return
        
        self.target_player = player_name
        
        # Save username to config
        self.config["last_username"] = player_name
        self.save_config()
        
        # Find initial camera
        api_camera = self.get_api_suggested_camera(player_name)
        if not api_camera:
            self.update_status(f"Player '{player_name}' not found in match", is_error=True)
            self.update_camera_display(None)
            self.start_btn.config(state=tk.DISABLED)
            return
        
        final_camera = self.apply_correction(player_name, api_camera)
        self.verified_camera_index = final_camera
        self.update_camera_display(final_camera)
        
        if self.switch_camera_to_index(final_camera):
            if final_camera != api_camera:
                self.update_status(f"Switched to {player_name} on camera {final_camera} (corrected from {api_camera})")
            else:
                self.update_status(f"Switched to {player_name} on camera {final_camera}")
            
            self.start_following()
        else:
            self.update_status(f"Failed to switch to camera {final_camera}", is_error=True)
    
    def adjust_camera(self, adjustment):
        """Manually adjust the current camera index"""
        if not self.target_player or not self.verified_camera_index:
            self.update_status("Set a player first", is_error=True)
            return
        
        new_camera = self.verified_camera_index + adjustment
        
        team = self.get_player_team(self.target_player)
        if team and "ORANGE" in team.upper():
            valid_range = range(1, 5)
        else:
            valid_range = range(6, 10)
            
        if new_camera not in valid_range:
            self.update_status(f"Camera {new_camera} out of valid range", is_error=True)
            return
        
        if self.switch_camera_to_index(new_camera):
            old_camera = self.verified_camera_index
            self.verified_camera_index = new_camera
            self.update_camera_display(new_camera)
            
            api_camera = self.get_api_suggested_camera(self.target_player)
            if api_camera:
                correction = new_camera - api_camera
                self.corrections[self.target_player] = correction
                self.config["corrections"] = self.corrections
                self.save_config()
            
            self.update_status(f"Camera adjusted to {new_camera} (saved)")
        else:
            self.update_status("Failed to switch camera", is_error=True)
    
    def get_player_team(self, player_name):
        """Determine which team a player is on"""
        session_data = self.get_session_data()
        if not session_data:
            return None
            
        teams = session_data.get("teams", [])
        for team in teams:
            team_name = team.get("team", "Unknown")
            players = team.get("players", [])
            for player in players:
                if player.get("name", "").lower() == player_name.lower():
                    return team_name
        return None
    
    def start_following(self):
        if not self.target_player or not self.verified_camera_index:
            return
        
        self.is_monitoring = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.player_entry.config(state=tk.DISABLED)
        
        self.update_status(f"Following {self.target_player} on camera {self.verified_camera_index}")
        
        def follow_loop():
            error_count = 0
            
            while self.is_monitoring:
                try:
                    success = self.switch_camera_to_index(self.verified_camera_index)
                    
                    if success:
                        error_count = 0
                    else:
                        error_count += 1
                    
                    if error_count >= 3:
                        api_camera = self.get_api_suggested_camera(self.target_player)
                        if api_camera:
                            final_camera = self.apply_correction(self.target_player, api_camera)
                            self.verified_camera_index = final_camera
                            self.update_camera_display(final_camera)
                            error_count = 0
                        else:
                            self.update_status("Player left the match", is_error=True)
                            self.stop_following()
                            break
                    
                    time.sleep(2)
                except:
                    time.sleep(5)
        
        threading.Thread(target=follow_loop, daemon=True).start()
        
    def stop_following(self):
        self.is_monitoring = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.player_entry.config(state=tk.NORMAL)
        self.update_status("Stopped following")
    
    def on_closing(self):
        """Save config and close"""
        self.is_monitoring = False
        self.save_config()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = EchoVRFollowMe(root)
    root.mainloop()