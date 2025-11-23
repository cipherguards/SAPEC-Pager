import os
import json
import time
from PIL import Image, ImageDraw, ImageFont

CONTACTS_FILE = "Contacts.json"
line_height = 40
top_padding = 60
visible_items = 4

# ---------------- CONTACT LOADING ----------------
def load_contacts():
    if not os.path.exists(CONTACTS_FILE):
        return []
    with open(CONTACTS_FILE, "r") as f:
        try:
            contacts = json.load(f)
            contacts.sort(key=lambda c: c["nickname"].lower())
            return contacts
        except json.JSONDecodeError:
            print("Error: Contacts.json malformed")
            return []

# ---------------- INPUT ----------------
import termios, tty, sys
def get_key():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
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
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

# ---------------- DRAW ----------------
def draw_menu(contact_names, selected_index, scroll_index, disp):
    image = Image.new("RGB", (240, 280), "BLACK")
    draw = ImageDraw.Draw(image)
    start_y = top_padding

    for i in range(visible_items):
        idx = scroll_index + i
        if idx >= len(contact_names):
            break
        item = contact_names[idx]
        y_top = start_y + i * line_height
        y_bottom = y_top + line_height
        if idx == selected_index:
            draw.rectangle([0, y_top, 240, y_bottom], fill="WHITE")
            draw.text((4, y_top + 6), item, fill="BLACK", font=disp.Font)
            draw.text((240-20, y_top+6), ">", fill="BLACK", font=disp.Font)
        else:
            draw.text((4, y_top + 6), item, fill="WHITE", font=disp.Font)

    disp.ShowImage(image.rotate(90))

def draw_no_match(disp):
    image = Image.new("RGB", (240, 280), "BLACK")
    draw = ImageDraw.Draw(image)
    msg = "No matches"
    bbox = draw.textbbox((0,0), msg, font=disp.Font)
    w = bbox[2]-bbox[0]
    h = bbox[3]-bbox[1]
    draw.text(((240 - w)//2, (280 - h)//2), msg, fill="WHITE", font=disp.Font)
    disp.ShowImage(image.rotate(90))
    time.sleep(1)

# ---------------- MENU LOOP ----------------
from contactdetails import contact_details
def menu_loop(disp, font):
    disp.Font = font  # attach font for draw functions
    contacts = load_contacts()
    if not contacts:
        print("No contacts found.")
        return

    all_names = [c["nickname"] for c in contacts]
    filter_text = ""
    filtered_names = all_names.copy()
    selected_index = 0
    scroll_index = 0

    draw_menu(filtered_names, selected_index, scroll_index, disp)

    while True:
        key = get_key()

        if key == "\x03":  # Ctrl+C
            break
        elif key in ("\r", " "):
            if filtered_names:
                contact_details(filtered_names[selected_index], disp, font)
        elif key == "up":
            if selected_index > 0:
                selected_index -= 1
                if selected_index < scroll_index:
                    scroll_index -= 1
        elif key == "down":
            if selected_index < len(filtered_names) - 1:
                selected_index += 1
                if selected_index >= scroll_index + visible_items:
                    scroll_index += 1
        elif key in ("left", "\x1b"):
             if filter_text:
                 # If a filter is active, just clear it
                 filter_text = ""
                 filtered_names = all_names.copy()
                 selected_index = 0
                 scroll_index = 0
             else:
             # No filter → exit contacts menu
                 break

        elif key == "\x7f":  # backspace
            if filter_text:
                filter_text = filter_text[:-1]
        elif len(key) == 1 and key.isprintable():
            filter_text += key

        # Apply filter
        if filter_text:
            norm = filter_text.lower().replace(" ", "").replace("-", "")
            filtered_names = [n for n in all_names if norm in n.lower().replace(" ", "").replace("-", "")]
            if not filtered_names:
                draw_no_match(disp)
                filtered_names = all_names.copy()
                filter_text = ""
                selected_index = 0
                scroll_index = 0
                continue

        if selected_index >= len(filtered_names):
            selected_index = len(filtered_names) - 1

        draw_menu(filtered_names, selected_index, scroll_index, disp)
        time.sleep(0.05)
