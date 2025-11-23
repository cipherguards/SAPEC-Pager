import os
import json
import time
from PIL import Image, ImageDraw, ImageFont

# ---------------- FONT SETUP ----------------
Font = None  # will be set from main program
line_height = 40
top_margin = 40
bottom_margin = 40

CONTACTS_FILE = "Contacts.json"

# ---------------- CONTACT LOOKUP ----------------
def load_contact(nickname):
    if not os.path.exists(CONTACTS_FILE):
        return None
    with open(CONTACTS_FILE, "r") as f:
        try:
            contacts = json.load(f)
        except json.JSONDecodeError:
            return None
    for c in contacts:
        if c["nickname"].lower() == nickname.lower():
            return c
    return None

# ---------------- PLACEHOLDER HANDLERS ----------------
def chat_handler(nickname):
    print(f"Chat triggered for {nickname}")

def call_handler(nickname):
    print(f"Call triggered for {nickname}")

# helper text sizing
def text_size(draw, text, font):
    bbox = draw.textbbox((0,0), text, font=font)
    return bbox[2]-bbox[0], bbox[3]-bbox[1]

# ---------------- DRAW FUNCTIONS ----------------
def draw_main_screen(disp, contact, focus_index):
    global Font, line_height, top_margin, bottom_margin

    image = Image.new("RGB", (240, 280), "BLACK")
    draw = ImageDraw.Draw(image)

    # Centered nickname
    w, _ = text_size(draw, contact["nickname"], Font)
    draw.text(((240 - w)//2, top_margin), contact["nickname"], fill="WHITE", font=Font)

    # Number below nickname
    number_y = top_margin + line_height
    if "number" in contact:
        num_text = str(contact["number"])
        w, _ = text_size(draw, num_text, Font)
        draw.text(((240 - w)//2, number_y), num_text, fill="WHITE", font=Font)

    # Show Address button under number
    show_y = number_y + line_height + 10
    if focus_index == 0:
        draw.rectangle([4, show_y, 240-4, show_y+line_height], fill="WHITE")
        draw.text((10, show_y+6), "Show Address", fill="BLACK", font=Font)
    else:
        draw.rectangle([4, show_y, 240-4, show_y+line_height], outline="WHITE")
        draw.text((10, show_y+6), "Show Address", fill="WHITE", font=Font)

    # Chat and Call buttons horizontally at bottom
    btn_y = 280 - line_height - bottom_margin
    btn_width = (240 - 12) // 2
    # Chat
    if focus_index == 1:
        draw.rectangle([4, btn_y, 4 + btn_width, btn_y+line_height], fill="WHITE")
        draw.text((10, btn_y+6), "Chat", fill="BLACK", font=Font)
    else:
        draw.rectangle([4, btn_y, 4 + btn_width, btn_y+line_height], outline="WHITE")
        draw.text((10, btn_y+6), "Chat", fill="WHITE", font=Font)
    # Call
    call_x = 8 + btn_width
    if focus_index == 2:
        draw.rectangle([call_x, btn_y, call_x + btn_width, btn_y+line_height], fill="WHITE")
        draw.text((call_x + 6, btn_y+6), "Call", fill="BLACK", font=Font)
    else:
        draw.rectangle([call_x, btn_y, call_x + btn_width, btn_y+line_height], outline="WHITE")
        draw.text((call_x + 6, btn_y+6), "Call", fill="WHITE", font=Font)

    disp.ShowImage(image.rotate(90))

def draw_address_screen(disp, address):
    global line_height
    image = Image.new("RGB", (240, 280), "BLACK")
    draw = ImageDraw.Draw(image)

    lines = []
    max_chars_per_line = 20
    for i in range(0, len(address), max_chars_per_line):
        lines.append(address[i:i+max_chars_per_line])

    total_height = len(lines) * line_height
    start_y = max((280 - total_height)//2, 10)

    for idx, line in enumerate(lines):
        w, _ = text_size(draw, line, Font)
        draw.text(((240 - w)//2, start_y + idx*line_height), line, fill="WHITE", font=Font)

    disp.ShowImage(image.rotate(90))

# ---------------- CONTACT DETAILS FUNCTION ----------------
def contact_details(nickname, disp, font):
    global Font
    Font = font  # use font from main program

    contact = load_contact(nickname)
    if not contact:
        print(f"No contact found for {nickname}")
        return

    focus_index = 0
    draw_main_screen(disp, contact, focus_index)

    # Simple SSH input
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

    while True:
        key = get_key()
        if key == "\x03":  # Ctrl+C
            break
        elif key == "up":
            focus_index = (focus_index - 1) % 3
        elif key in ("down", "right"):
            focus_index = (focus_index + 1) % 3
        elif key in ("\r", " "):
            if focus_index == 0:  # Show Address
                draw_address_screen(disp, contact["address"])
                while True:
                    k = get_key()
                    if k in ("\x1b", "left", "\r", " "):
                        break
                draw_main_screen(disp, contact, focus_index)
            elif focus_index == 1:
                chat_handler(nickname)
            elif focus_index == 2:
                call_handler(nickname)
        elif key in ("\x1b", "left"):
            break

        draw_main_screen(disp, contact, focus_index)
        time.sleep(0.05)
