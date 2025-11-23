import subprocess
import time
from PIL import Image, ImageDraw
import sys, tty, termios

# ----------- CONFIG -----------
LINE_HEIGHT = 40
TOP_PAD = 60
VISIBLE = 4


# ----------- CONNECTION CLEANUP -----------
def get_connection_profiles():
    """Get all connection profile names using nmcli."""
    result = subprocess.run(
        ['nmcli', '-t', 'connection', 'show'],
        stdout=subprocess.PIPE
    )
    profiles = []
    if result.returncode == 0:
        for line in result.stdout.decode().splitlines():
            if not line:
                continue
            parts = line.split(':')
            if len(parts) >= 1:
                profile_name = parts[0]
                profiles.append(profile_name)
    return profiles

def delete_profile(profile_name):
    """Delete a connection profile."""
    result = subprocess.run(
        ['nmcli', 'connection', 'delete', profile_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return result.returncode == 0

def cleanup_connections():
    """Remove all connection profiles except 'preconfigured' and 'lo'."""
    profiles = get_connection_profiles()
    for profile in profiles:
        if profile not in ("preconfigured", "lo"):
            delete_profile(profile)

# ----------- WIFI SCAN -----------
def scan_wifi():
    """Always perform a fresh scan and return clean list."""
    result = subprocess.run(
        ['nmcli', '-t', '-f', 'SSID,SECURITY,SIGNAL', 'dev', 'wifi', 'list', '--rescan', 'yes'],
        stdout=subprocess.PIPE
    )

    networks = []
    if result.returncode == 0:
        for line in result.stdout.decode().splitlines():
            if not line:
                continue
            ssid, security, signal = (line.split(':') + ["", "", ""])[:3]

            # Skip blank SSIDs (noise entries)
            if not ssid.strip():
                continue

            networks.append((ssid, security, signal))
    return networks


# ----------- CONNECT -----------
def connect_to(ssid, password=""):
    if not password:  # Open network
        cmd = ['nmcli', 'device', 'wifi', 'connect', ssid]
    else:  # Secured network
        cmd = ['nmcli', 'device', 'wifi', 'connect', ssid, 'password', password]

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("CMD:", cmd)
    print("STDOUT:", res.stdout.decode())
    print("STDERR:", res.stderr.decode())
    print("RETURN CODE:", res.returncode)
    
    return res.returncode == 0

# ----------- INPUT -----------
def get_key():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)

        if ch == '\x1b':  # arrow keys
            if sys.stdin.read(1) == '[':
                ch2 = sys.stdin.read(1)
                return {"A": "up", "B": "down", "C": "right", "D": "left"}.get(ch2, "")
            return ""
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


# ----------- MENU DRAW -----------
def draw_menu(disp, networks, selected, scroll):
    img = Image.new("RGB", (240, 280), "BLACK")
    draw = ImageDraw.Draw(img)

    for i in range(VISIBLE):
        idx = scroll + i
        if idx >= len(networks):
            break

        ssid, sec, sig = networks[idx]
        y = TOP_PAD + i * LINE_HEIGHT

        label = f"{ssid} [{'Open' if sec in ('', '--') else 'Sec'}]"

        if idx == selected:
            draw.rectangle([0, y, 240, y + LINE_HEIGHT], fill="WHITE")
            draw.text((4, y + 6), label, fill="BLACK", font=disp.Font)
            draw.text((220, y + 6), ">", fill="BLACK", font=disp.Font)
        else:
            draw.text((4, y + 6), label, fill="WHITE", font=disp.Font)

    disp.ShowImage(img.rotate(90))


# ----------- PASSWORD ENTRY -----------
def prompt_password(disp, ssid):
    password = ""
    input_active = True  # True = input field, False = button
    cursor_visible = True
    toggle = time.time()

    while True:
        if time.time() - toggle > 0.5:
            cursor_visible = not cursor_visible
            toggle = time.time()

        img = Image.new("RGB", (240, 280), "BLACK")
        draw = ImageDraw.Draw(img)

        title = f"Password"
        draw.text((10, TOP_PAD), title, fill="WHITE", font=disp.Font)

        # Input box
        box_y = TOP_PAD + 50
        if input_active:
            draw.rectangle([10, box_y, 230, box_y + LINE_HEIGHT], fill="WHITE")
            show = ("*" * len(password)) + ("|" if cursor_visible else "")
            draw.text((14, box_y + 6), show, fill="BLACK", font=disp.Font)
        else:
            draw.rectangle([10, box_y, 230, box_y + LINE_HEIGHT], outline="WHITE")
            show = "*" * len(password)
            draw.text((14, box_y + 6), show, fill="WHITE", font=disp.Font)

        # Connect button
        btn_y = box_y + LINE_HEIGHT + 20
        btn_text = "Connect"
        if not input_active:
            draw.rectangle([10, btn_y, 230, btn_y + LINE_HEIGHT], fill="WHITE")
            draw.text((14, btn_y + 6), btn_text, fill="BLACK", font=disp.Font)
        else:
            draw.rectangle([10, btn_y, 230, btn_y + LINE_HEIGHT], outline="WHITE")
            draw.text((14, btn_y + 6), btn_text, fill="WHITE", font=disp.Font)

        disp.ShowImage(img.rotate(90))

        key = get_key()
        if key == "up":
            input_active = True
        elif key == "down":
            input_active = False
        elif key in ("\r", " "):
            if not input_active:  # Button pressed
                return password
        elif key in ("\x1b", "left"):
            return None
        elif input_active:
            if key == "\x7f":
                password = password[:-1]
            elif key and key.isprintable():
                password += key


# ----------- NOTIFICATION -----------
def notify(disp, msg):
    img = Image.new("RGB", (240, 280), "BLACK")
    draw = ImageDraw.Draw(img)
    draw.text((20, 130), msg, fill="WHITE", font=disp.Font)
    disp.ShowImage(img.rotate(90))
    time.sleep(1.5)


# ----------- MAIN MENU LOOP -----------
def network_manager(disp, font):
    disp.Font = font

    networks = scan_wifi()
    if not networks:
        notify(disp, "No networks")
        return

    sel = 0
    scroll = 0

    draw_menu(disp, networks, sel, scroll)

    while True:
        key = get_key()

        if key in ("left", "\x1b"):
            return

        if key == "up" and sel > 0:
            sel -= 1
            if sel < scroll:
                scroll -= 1

        elif key == "down" and sel < len(networks) - 1:
            sel += 1
            if sel >= scroll + VISIBLE:
                scroll += 1

        elif key in ("\r", " "):
            ssid, sec, _ = networks[sel]
            if sec in ("", "--"):
                success = connect_to(ssid)
            else:
                pwd = prompt_password(disp, ssid)
                success = connect_to(ssid, pwd) if pwd else False

            notify(disp, "Connected ✓" if success else "Failed ✗")

            # Always full rescan so hotspot appears again
            networks = scan_wifi()
            sel = 0
            scroll = 0

        draw_menu(disp, networks, sel, scroll)
