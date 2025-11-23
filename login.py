import os
import sys
import termios
import tty
import time
import logging
from PIL import Image, ImageDraw, ImageFont
sys.path.append("..")
from lib import LCD_1inch69

# ---------------- DISPLAY SETUP ----------------
RST = 27
DC = 25
BL = 18

disp = LCD_1inch69.LCD_1inch69()
disp.Init()
disp.clear()
disp.bl_DutyCycle(60)

# ---------------- FONT ----------------
Font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 28)      # title
FontSmall = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 20)  # attempts

# ---------------- CONFIG ----------------
rotation = 90
screen_width = 240
screen_height = 280
border = 0
max_attempts = 3
max_chars = 6

# helper text size
def text_size(draw, text, font):
    bbox = draw.textbbox((0,0), text, font=font)
    return bbox[2]-bbox[0], bbox[3]-bbox[1]

# ---------------- SSH-SAFE INPUT ----------------
def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

# ---------------- DRAW FUNCTION ----------------
def draw_login(password_chars, attempts_left):
    image = Image.new("RGB", (screen_width, screen_height), "BLACK")
    draw = ImageDraw.Draw(image)
    safe_width = screen_width - 2 * border

    # Title
    title = "PASSCODE"
    w, h = text_size(draw, title, Font)
    x = border + (safe_width - w) // 2
    draw.text((x, border + 40), title, fill="WHITE", font=Font)

    # Password slots (6 fixed)
    slot_y = border + 125
    slot_width = 20
    slot_spacing = 20
    total_width = max_chars*slot_width + (max_chars-1)*slot_spacing
    start_x = border + (safe_width - total_width) // 2

    for i in range(max_chars):
        char = "*" if i < len(password_chars) else "•"
        draw.text((start_x + i*(slot_width + slot_spacing), slot_y), char, fill="WHITE", font=Font)

    # Attempts left
    attempts_text = f"Attempts left: {attempts_left}"
    w, h = text_size(draw, attempts_text, FontSmall)
    x = border + (safe_width - w) // 2
    draw.text((x, slot_y + 90), attempts_text, fill="WHITE", font=FontSmall)

    # Rotate and show
    image = image.rotate(rotation)
    disp.ShowImage(image)

# ---------------- LOGIN HANDLE ----------------
def login_handle(correct_password="123456"):
    """Function callable by other scripts. Returns True on success, False on failure."""
    attempts_left = max_attempts
    password_chars = []
    draw_login(password_chars, attempts_left)

    logging.info("Type password. Backspace allowed. Enter to submit.")

    while attempts_left > 0:
        key = get_key()

        if key == "\x03":  # Ctrl+C
            return False
        elif key == "\r":  # Enter
            entered_password = "".join(password_chars)
            # --- FOR TESTING ALWAYS TRUE ---
            success = True  # replace with actual check later
            if success:
                logging.info("Login successful!")
                draw_login(password_chars, attempts_left)
                time.sleep(0.5)
                return True
            else:
                attempts_left -= 1
                password_chars = []
                draw_login(password_chars, attempts_left)
        elif key in ("\x7f", "\b"):  # Backspace
            if password_chars:
                password_chars.pop()
                draw_login(password_chars, attempts_left)
        elif 32 <= ord(key) <= 126 and len(password_chars) < max_chars:
            password_chars.append(key)
            draw_login(password_chars, attempts_left)

    logging.info("Login failed.")
    draw_login(password_chars, 0)
    time.sleep(1)
    return False

# ---------------- LOGIN LOOP ----------------
if __name__ == "__main__":
    try:
        result = login_handle()
        if result:
            logging.info("Proceed to Main Menu / Contacts / Add Contact")
        else:
            logging.info("Login failed. Exiting.")
    except KeyboardInterrupt:
        logging.info("Interrupted")
    finally:
        disp.module_exit()
        print("\nExited safely")
