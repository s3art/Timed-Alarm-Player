from datetime import datetime
import os
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pygame

# Initialize pygame mixer for audio
pygame.mixer.init()


class TimedMusicPlayerApp:

  def __init__(self, root):
    self.root = root
    self.root.title("Timed Alarm Player")
    self.root.geometry("600x500")
    self.root.minsize(550, 450)

    self.schedules = []  # List to store active schedule dictionaries
    self.is_running = True

    # --- UI Layout ---
    title_label = tk.Label(
        root, text="Timed Music Scheduler", font=("Arial", 16, "bold")
    )
    title_label.pack(pady=10)

    # Input Frame
    input_frame = tk.LabelFrame(
        root, text=" Add New Schedule ", font=("Arial", 10, "bold"), padx=10, pady=10
    )
    input_frame.pack(fill="x", padx=15, pady=5)

    # 1. File Selection
    tk.Label(input_frame, text="Music File:").grid(
        row=0, column=0, sticky="w", pady=5
    )
    self.file_path_var = tk.StringVar()
    self.file_entry = tk.Entry(
        input_frame, textvariable=self.file_path_var, width=35
    )
    self.file_entry.grid(row=0, column=1, padx=5, pady=5)
    tk.Button(input_frame, text="Browse", command=self.browse_file).grid(
        row=0, column=2, pady=5
    )

    # 2. Day of Week
    tk.Label(input_frame, text="Day of Week:").grid(
        row=1, column=0, sticky="w", pady=5
    )
    self.day_var = tk.StringVar(value="Everyday")
    days = [
        "Everyday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    self.day_dropdown = ttk.Combobox(
        input_frame, textvariable=self.day_var, values=days, state="readonly"
    )
    self.day_dropdown.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

    # 3. Time (HH:MM)
    tk.Label(input_frame, text="Time (24-hr HH:MM):").grid(
        row=2, column=0, sticky="w", pady=5
    )
    time_frame = tk.Frame(input_frame)
    time_frame.grid(row=2, column=1, sticky="w", padx=5, pady=5)

    self.hour_var = tk.StringVar(value="08")
    self.minute_var = tk.StringVar(value="00")
    tk.Entry(time_frame, textvariable=self.hour_var, width=3).pack(side="left")
    tk.Label(time_frame, text=":").pack(side="left")
    tk.Entry(time_frame, textvariable=self.minute_var, width=3).pack(
        side="left"
    )
    tk.Label(
        time_frame, text=" (e.g., 08:30, 17:00)", fg="gray", font=("Arial", 9)
    ).pack(side="left", padx=5)

    # 4. Duration
    tk.Label(input_frame, text="Duration (Seconds):").grid(
        row=3, column=0, sticky="w", pady=5
    )
    self.duration_var = tk.StringVar(value="60")
    tk.Entry(input_frame, textvariable=self.duration_var, width=10).grid(
        row=3, column=1, sticky="w", padx=5, pady=5
    )

    # Add Button
    tk.Button(
        input_frame,
        text="Add Schedule",
        bg="#4CAF50",
        fg="white",
        font=("Arial", 10, "bold"),
        command=self.add_schedule,
    ).grid(row=4, column=0, columnspan=3, pady=10)

    # --- Scheduled List Frame ---
    list_frame = tk.LabelFrame(
        root, text=" Active Schedules ", font=("Arial", 10, "bold"), padx=10, pady=10
    )
    list_frame.pack(fill="both", expand=True, padx=15, pady=5)

    self.schedule_listbox = tk.Listbox(list_frame, font=("Arial", 9))
    self.schedule_listbox.pack(
        side="left", fill="both", expand=True, padx=(0, 5)
    )

    scrollbar = tk.Scrollbar(
        list_frame, orient="vertical", command=self.schedule_listbox.yview
    )
    scrollbar.pack(side="right", fill="y")
    self.schedule_listbox.config(yscrollcommand=scrollbar.set)

    tk.Button(
        root, text="Remove Selected Schedule", command=self.remove_schedule
    ).pack(pady=5)

    # Status Bar
    self.status_var = tk.StringVar(value="Status: Background Monitor Running...")
    status_bar = tk.Label(
        root,
        textvariable=self.status_var,
        bd=1,
        relief=tk.SUNKEN,
        anchor="w",
        font=("Arial", 9),
    )
    status_bar.pack(side="bottom", fill="x")

    # Start background thread to check schedules
    self.monitor_thread = threading.Thread(target=self.run_scheduler, daemon=True)
    self.monitor_thread.start()

    root.protocol("WM_DELETE_WINDOW", self.on_closing)

  def browse_file(self):
    filename = filedialog.askopenfilename(
        title="Select Audio File",
        filetypes=[("Audio Files", "*.mp3 *.wav *.ogg"), ("All Files", "*.*")],
    )
    if filename:
      self.file_path_var.set(filename)

  def add_schedule(self):
    filepath = self.file_path_var.get().strip()
    day = self.day_var.get()
    hour = self.hour_var.get().strip()
    minute = self.minute_var.get().strip()
    duration_str = self.duration_var.get().strip()

    # Validation
    if not filepath or not os.path.exists(filepath):
      messagebox.showerror("Error", "Please select a valid audio file path.")
      return

    if not hour.isdigit() or not minute.isdigit() or not duration_str.isdigit():
      messagebox.showerror(
          "Error", "Time (Hour/Minute) and Duration must be valid numbers."
      )
      return

    hour_int, minute_int = int(hour), int(minute)
    if not (0 <= hour_int <= 23 and 0 <= minute_int <= 59):
      messagebox.showerror(
          "Error", "Invalid time format. Use Hour: 0-23, Minute: 0-59."
      )
      return

    time_str = f"{hour_int:02d}:{minute_int:02d}"
    duration = int(duration_str)

    schedule_item = {
        "file": filepath,
        "day": day,
        "time": time_str,
        "duration": duration,
        "last_played": None,  # Prevents repeating multiple times within the same minute
    }

    self.schedules.append(schedule_item)
    display_text = (
        f"[{day}] at {time_str} -> {os.path.basename(filepath)} ({duration}s)"
    )
    self.schedule_listbox.insert(tk.END, display_text)

    # Reset inputs
    self.file_path_var.set("")
    messagebox.onsaved = True
    self.status_var.set(
        f"Status: Added schedule for {day} at {time_str} successfully."
    )

  def remove_schedule(self):
    try:
      selected_idx = self.schedule_listbox.curselection()[0]
      self.schedule_listbox.delete(selected_idx)
      removed = self.schedules.pop(selected_idx)
      self.status_var.set(
          f"Status: Removed schedule for {removed['day']} at {removed['time']}."
      )
    except IndexError:
      messagebox.showwarning(
          "Warning", "Please select a schedule from the list to remove."
      )

  def play_audio(self, filepath, duration):
    try:
      self.status_var.set(f"Playing: {os.path.basename(filepath)}...")
      pygame.mixer.music.load(filepath)
      pygame.mixer.music.play()

      start_time = time.time()
      while pygame.mixer.music.get_busy():
        if time.time() - start_time > duration:
          pygame.mixer.music.stop()
          break
        time.sleep(0.5)

      pygame.mixer.music.stop()
      self.status_var.set("Status: Background Monitor Running...")
    except Exception as e:
      self.status_var.set(f"Error playing file: {str(e)}")

  def run_scheduler(self):
    """Background thread checking current time against active schedules every second."""
    while self.is_running:
      now = datetime.now()
      current_day = now.strftime("%A")  # e.g., 'Monday'
      current_time_str = now.strftime("%H:%M")  # e.g., '08:00'
      current_date_str = now.strftime("%Y-%m-%d")

      for item in self.schedules:
        # Check if time matches and day matches ('Everyday' or specific day)
        if item["time"] == current_time_str and (
            item["day"] == "Everyday" or item["day"] == current_day
        ):

          # Unique identifier per minute to make sure it only triggers once per minute slot
          play_identifier = f"{current_date_str} {current_time_str}"
          if item["last_played"] != play_identifier:
            item["last_played"] = play_identifier

            # Run playback in a separate thread so the GUI doesn't freeze
            threading.Thread(
                target=self.play_audio,
                args=(item["file"], item["duration"]),
                daemon=True,
            ).start()

      time.sleep(1)

  def on_closing(self):
    self.is_running = False
    pygame.mixer.quit()
    self.root.destroy()


if __name__ == "__main__":
  root = tk.Tk()
  app = TimedMusicPlayerApp(root)
  root.mainloop()