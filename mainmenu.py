import os
import sys
import termios
import tty
import time
import json
from PIL import Image, ImageDraw, ImageFont
sys.path.append("..")

from lib import LCD_1inch69
from contactlist import menu_loop as contacts_menu
from addcontact import add_contact
from login import login_handle, disp, Font  # reuse display and font
from network import network_manager, cleanup_connections

# ---------------- CONFIG ----------------
rotation = 90
screen_width = 240
screen_height = 280
line_height = 40
visible_items = 4
top_padding = 60
CONTACTS_FILE = "Contacts.json"

menu_items = [
    "Keypad",
    "Contacts",
    "Add Contact",
    "Network",
    "Destroy ID",
    "Shutdown"
]

# ---------------- SSH-SAFE INPUT ----------------
def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            ch2 = sys.stdin.read(1)
            if ch2 == '[':
                ch3 = sys.stdin.read(1)
                if ch3 == 'A': return "up"
                elif ch3 == 'B': return "down"
                elif ch3 == 'D': return "left"
                elif ch3 == 'C': return "right"
            return ''
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

# ---------------- MENU HANDLERS ----------------
def handle_keypad():
    print("Keypad selected (not implemented)")

def handle_contacts():
    # Launch Contacts menu
    contacts_menu(disp, Font)  # uses the same disp instance

def handle_add_contact():
    add_contact(disp, Font)

def handle_network():
    network_manager(disp, Font)

def handle_destroy_id():
    print("Destroy ID selected (not implemented)")

def handle_shutdown():
    print("Shutting down...")
    cleanup_connections()
    raise KeyboardInterrupt  # exit menu

menu_handlers = [
    handle_keypad,
    handle_contacts,
    handle_add_contact,
    handle_network,
    handle_destroy_id,
    handle_shutdown
]

# ---------------- DRAW MENU ----------------
def draw_menu(selected_index, scroll_index):
    image = Image.new("RGB", (screen_width, screen_height), "BLACK")
    draw = ImageDraw.Draw(image)
    start_y = top_padding

    for i in range(visible_items):
        item_index = scroll_index + i
        if item_index >= len(menu_items):
            break
        item = menu_items[item_index]
        y_top = start_y + i * line_height
        y_bottom = y_top + line_height

        if item_index == selected_index:
            draw.rectangle([0, y_top, screen_width, y_bottom], fill="WHITE")
            draw.text((4, y_top + 6), item, fill="BLACK", font=Font)
            draw.text((screen_width - 20, y_top + 6), ">", fill="BLACK", font=Font)
        else:
            draw.text((4, y_top + 6), item, fill="WHITE", font=Font)

    # Scroll triangles
    triangle_size = 10
    center_x = screen_width // 2
    padding = 32
    if scroll_index > 0:
        top_y = padding + triangle_size
        draw.polygon([
            (center_x, top_y - triangle_size),
            (center_x - triangle_size, top_y),
            (center_x + triangle_size, top_y)
        ], fill="WHITE")
    if scroll_index + visible_items < len(menu_items):
        bottom_y = screen_height - padding - triangle_size
        draw.polygon([
            (center_x, bottom_y + triangle_size),
            (center_x - triangle_size, bottom_y),
            (center_x + triangle_size, bottom_y)
        ], fill="WHITE")

    rotated_image = image.rotate(rotation)
    disp.ShowImage(rotated_image)

# ---------------- MENU LOOP ----------------
def menu_loop():
    selected_index = 0
    scroll_index = 0
    draw_menu(selected_index, scroll_index)

    while True:
        key = get_key()
        if key == "\x03":  # Ctrl+C
            break
        elif key in ("\r", " "):
            # Call corresponding handler
            menu_handlers[selected_index]()
        elif key == "up":
            if selected_index > 0:
                selected_index -= 1
                if selected_index < scroll_index:
                    scroll_index -= 1
        elif key == "down":
            if selected_index < len(menu_items)-1:
                selected_index += 1
                if selected_index >= scroll_index + visible_items:
                    scroll_index += 1

        draw_menu(selected_index, scroll_index)
        time.sleep(0.05)

# ---------------- RUN ----------------
if __name__ == "__main__":
    try:
        cleanup_connections()  # Clean up on startup
        # 1️⃣ Login first
        if login_handle(correct_password="123456"):
            # 2️⃣ Only show main menu if login succeeds
            menu_loop()
        else:
            print("Login failed. Exiting.")
    except KeyboardInterrupt:
        print("\nExiting safely")
    finally:
        cleanup_connections()  # Clean up on exit
        disp.module_exit()
