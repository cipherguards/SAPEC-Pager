import os
import json
import time
from PIL import Image, ImageDraw, ImageFont

CONTACTS_FILE = "Contacts.json"
line_height = 40
top_margin = 40
bottom_margin = 40

def add_contact(disp, font):
    Font = font  # use the main menu font

    fields = ["address", "nickname", "number", "whitelist"]
    values = {"address": "", "nickname": "", "number": "", "whitelist": False}
    screen_index = 0
    input_active = True  # True = input field, False = button/checkbox
    cursor_visible = True
    last_cursor_toggle = time.time()

    # helper for text size
    def text_size(draw, text, font):
        bbox = draw.textbbox((0,0), text, font=font)
        return bbox[2]-bbox[0], bbox[3]-bbox[1]

    # ---------------- DRAWING ----------------
    def draw_screen():
        nonlocal cursor_visible
        image = Image.new("RGB", (240, 280), "BLACK")
        draw = ImageDraw.Draw(image)

        titles = ["Enter Address", "Enter Nickname", "Enter Number (optional)", "Whitelist"]
        # Title centered
        w, _ = text_size(draw, titles[screen_index], Font)
        draw.text(((240 - w)//2, top_margin), titles[screen_index], fill="WHITE", font=Font)

        y = top_margin + 50
        # Input fields
        if screen_index < 3:
            val = values[fields[screen_index]]
            display_text = val + ("|" if cursor_visible else "")
            if input_active:
                draw.rectangle([10, y, 230, y+line_height], fill="WHITE")
                draw.text((14, y+6), display_text, fill="BLACK", font=Font)
            else:
                draw.rectangle([10, y, 230, y+line_height], outline="WHITE")
                draw.text((14, y+6), display_text, fill="WHITE", font=Font)
            # Next button at bottom
            btn_y = 280 - line_height - bottom_margin
            btn_text = "Next"
            tw, _ = text_size(draw, btn_text, Font)
            if not input_active:
                draw.rectangle([10, btn_y, 230, btn_y+line_height], fill="WHITE")
                draw.text(((240 - tw)//2, btn_y+6), btn_text, fill="BLACK", font=Font)
            else:
                draw.rectangle([10, btn_y, 230, btn_y+line_height], outline="WHITE", fill=None)
                draw.text(((240 - tw)//2, btn_y+6), btn_text, fill="WHITE", font=Font)
        else:
            # Checkbox
            chk_y = y
            draw.rectangle([10, chk_y, 50, chk_y+line_height], outline="WHITE", fill=None)
            if values["whitelist"]:
                # Draw a cross
                draw.line([12, chk_y+4, 48, chk_y+line_height-4], fill="WHITE", width=2)
                draw.line([12, chk_y+line_height-4, 48, chk_y+4], fill="WHITE", width=2)
            draw.text((60, chk_y+6), "Whitelist", fill="WHITE", font=Font)
            # Finish button
            btn_y = 280 - line_height - bottom_margin
            btn_text = "Finish"
            tw, _ = text_size(draw, btn_text, Font)
            if not input_active:
                draw.rectangle([10, btn_y, 230, btn_y+line_height], fill="WHITE")
                draw.text(((240 - tw)//2, btn_y+6), btn_text, fill="BLACK", font=Font)
            else:
                draw.rectangle([10, btn_y, 230, btn_y+line_height], outline="WHITE", fill=None)
                draw.text(((240 - tw)//2, btn_y+6), btn_text, fill="WHITE", font=Font)

        disp.ShowImage(image.rotate(90))

    # ---------------- INPUT ----------------
    import sys, termios, tty
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
        # Blink cursor
        if time.time() - last_cursor_toggle > 0.5:
            cursor_visible = not cursor_visible
            last_cursor_toggle = time.time()

        draw_screen()
        key = get_key()
        if key == "\x03":  # Ctrl+C
            break

        # ---------------- NAVIGATION ----------------
        if key in ("up",):
            if input_active:
                input_active = False  # move from input to button
            else:
                input_active = True  # move from button back to input
        elif key in ("down",):
            if input_active:
                input_active = False  # move from input to button
            else:
                input_active = True  # move from button to input
        elif key in ("right",):
            input_active = False  # move focus to button/checkbox
        elif key in ("left", "\x1b"):
            if screen_index == 0 and input_active:
                break  # exit menu from first screen input
            else:
                if screen_index > 0:
                    screen_index -= 1
                    input_active = True
                else:
                    input_active = True  # first screen, stay in input

        # ---------------- ENTER / SPACE ----------------
        elif key in ("\r", " "):
            if screen_index < 3 and not input_active:  # Next button
                screen_index += 1
                input_active = True
            elif screen_index == 3 and not input_active:  # Finish button
                contact = {"nickname": values["nickname"], "address": values["address"]}
                if values["number"]:
                    try:
                        contact["number"] = int(values["number"])
                    except:
                        pass
                contacts = []
                if os.path.exists(CONTACTS_FILE):
                    with open(CONTACTS_FILE, "r") as f:
                        try:
                            contacts = json.load(f)
                        except:
                            contacts = []
                contacts.append(contact)
                with open(CONTACTS_FILE, "w") as f:
                    json.dump(contacts, f, indent=4)
                break
            elif screen_index == 3 and input_active:  # Checkbox toggle
                values["whitelist"] = not values["whitelist"]

        # ---------------- TEXT INPUT ----------------
        elif len(key) == 1 and input_active and screen_index < 3:
            if key == "\x7f":  # backspace
                values[fields[screen_index]] = values[fields[screen_index]][:-1]
            else:
                values[fields[screen_index]] += key
