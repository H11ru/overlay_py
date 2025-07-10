import pygame
import ctypes
from ctypes import wintypes
import sys
from pynput import mouse

# Initialize Pygame
pygame.init()
info = pygame.display.Info()
size = (info.current_w, info.current_h)
screen = pygame.display.set_mode(size, pygame.NOFRAME)

TRANSPARENT = (74, 46, 99)  # #4A2E63

hwnd = pygame.display.get_wm_info()['window']

# Make window always on top
HWND_TOPMOST = -1
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_SHOWWINDOW = 0x0040
ctypes.windll.user32.SetWindowPos(
    hwnd, wintypes.HWND(HWND_TOPMOST), 0, 0, 0, 0,
    SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
)

# Set window to be layered (NO WS_EX_TRANSPARENT)
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
ctypes.windll.user32.SetWindowLongW(
    hwnd, GWL_EXSTYLE,
    style | WS_EX_LAYERED
)

color_key = (TRANSPARENT[2] << 16) | (TRANSPARENT[1] << 8) | TRANSPARENT[0]
ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, color_key, 0, 0x1)

clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 28)

# Overlay box properties
SNAP_DIST = 20

# Primary menu overlay (always visible)
menu_rect = pygame.Rect(50, 50, 300, 300) # Make menu multiple of 100 in size so all overlays snap together well
menu_overlay = {'rect': menu_rect, 'label': 'Menu', 'visible': True} # (220, 220, 220)

# Toggleable overlays
toggle_overlays = [
    {'rect': pygame.Rect(100, 300, 200, 100), 'label': 'Clock', 'visible': False},
    {'rect': pygame.Rect(400, 300, 400, 600), 'label': 'Notepad', 'visible': False},
    {'rect': pygame.Rect(800, 300, 200, 200), 'label': 'Calculator', 'visible': False},
]

# Toggle buttons (positions relative to menu)
TOGGLE_BTN_W, TOGGLE_BTN_H = 260, 40
toggle_btns = [
    pygame.Rect(menu_rect.x, menu_rect.y + 60, TOGGLE_BTN_W, TOGGLE_BTN_H),
    pygame.Rect(menu_rect.x, menu_rect.y + 110, TOGGLE_BTN_W, TOGGLE_BTN_H),
    pygame.Rect(menu_rect.x, menu_rect.y + 160, TOGGLE_BTN_W, TOGGLE_BTN_H),
]

# Z-order: menu always at bottom, overlays above
z_order = [0, 1, 2, 3]  # 0: menu, 1: red, 2: green, 3: blue

# Shared mouse state
mouse_pos = [0, 0]
mouse_pressed = [False]
dragging_idx = None
drag_offset = (0, 0)

def on_click(x, y, button, pressed):
    mouse_pos[0], mouse_pos[1] = x, y
    if button == mouse.Button.left:
        mouse_pressed[0] = pressed

def on_move(x, y):
    mouse_pos[0], mouse_pos[1] = x, y

from pynput import mouse
listener = mouse.Listener(on_click=on_click, on_move=on_move)
listener.daemon = True
listener.start()

def clamp_rect(rect):
    rect.x = max(0, min(size[0] - rect.width, rect.x))
    rect.y = max(0, min(size[1] - rect.height, rect.y))

def snap_to_others(idx, overlays_all):
    rect = overlays_all[idx]['rect']
    # Snap to screen edges
    if abs(rect.left) <= SNAP_DIST:
        rect.left = 0
    if abs(rect.top) <= SNAP_DIST:
        rect.top = 0
    if abs(rect.right - size[0]) <= SNAP_DIST:
        rect.right = size[0]
    if abs(rect.bottom - size[1]) <= SNAP_DIST:
        rect.bottom = size[1]
    # Snap to other overlays (only visible ones, skip self and menu)
    for j, other_overlay in enumerate(overlays_all):
        if j == idx or not other_overlay.get('visible', True):
            continue
        other = other_overlay['rect']
        # Snap left/right
        if abs(rect.right - other.left) <= SNAP_DIST and rect.bottom > other.top and rect.top < other.bottom:
            rect.right = other.left
        if abs(rect.left - other.right) <= SNAP_DIST and rect.bottom > other.top and rect.top < other.bottom:
            rect.left = other.right
        # Snap top/bottom
        if abs(rect.bottom - other.top) <= SNAP_DIST and rect.right > other.left and rect.left < other.right:
            rect.bottom = other.top
        if abs(rect.top - other.bottom) <= SNAP_DIST and rect.right > other.left and rect.left < other.right:
            rect.top = other.bottom

        # Snap left edges (if the left edge of this overlay is within SNAP_DIST of the left edge of the other overlay, set the left edge to the left edge of the other overlay)
        other_left = other.left
        this_left = rect.left
        def closeenough(a, b):
            return abs(a - b) <= SNAP_DIST
        if abs(this_left - other_left) <= SNAP_DIST and (closeenough(other.top, rect.bottom) or closeenough(other.bottom, rect.top)): # If the sides of the overlays close enough, and this left hting, sedge
            #print("Edge snapped!")
            rect.left = other_left

        
        # Snap right edges
        other_right = other.right
        this_right = rect.right
        if abs(this_right - other_right) <= SNAP_DIST and (closeenough(other.top, rect.bottom) or closeenough(other.bottom, rect.top)):
            rect.right = other_right

        # Snap top edges
        other_top = other.top
        this_top = rect.top
        if abs(this_top - other_top) <= SNAP_DIST and (closeenough(other.left, rect.right) or closeenough(other.right, rect.left)):
            rect.top = other_top

        # Snap bottom edges
        other_bottom = other.bottom
        this_bottom = rect.bottom
        if abs(this_bottom - other_bottom) <= SNAP_DIST and (closeenough(other.left, rect.right) or closeenough(other.right, rect.left)):
            rect.bottom = other_bottom
import datetime



# Calculator state
calc_input = ""
calc_result = ""
calc_active = False

# Notepad state
if __import__("os").path.exists("notesdata.txt"):
    with open("notesdata.txt", "r") as f:
        notepad_lines = f.readlines()
else:
    notepad_lines = [""]

# get rid of any linefeeds after note pad lines
notepad_lines = [line.rstrip('\n') for line in notepad_lines]
notepad_active = False
notepad_cursor = [0, 0]  # [line, col]
notepad_last_blink = 0
notepad_scroll = 0
notepad_show_cursor = True
started_clicking = False
was_originally_dragging = False
running = True
try:
    while running:
            
        # In your event loop, handle typing for calculator and notepad:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if calc_active:
                    if event.key == pygame.K_RETURN:
                        try:
                            calc_result = str(eval(calc_input))
                        except Exception as e:
                            calc_result = "Error"
                    elif event.key == pygame.K_BACKSPACE:
                        calc_input = calc_input[:-1]
                    else:
                        if event.unicode.isprintable():
                            calc_input += event.unicode
                elif notepad_active:
                    # When keypress, reset cursor blink to the first frame after it toggles on
                    notepad_last_blink = pygame.time.get_ticks()
                    notepad_show_cursor = True
                    # This is so that it shows when typim
                    if event.key == pygame.K_BACKSPACE:
                        line, col = notepad_cursor
                        if col > 0:
                            notepad_lines[line] = notepad_lines[line][:col-1] + notepad_lines[line][col:]
                            notepad_cursor[1] -= 1
                        elif line > 0:
                            prev_len = len(notepad_lines[line-1])
                            notepad_lines[line-1] += notepad_lines[line]
                            del notepad_lines[line]
                            notepad_cursor = [line-1, prev_len]
                    elif event.key == pygame.K_RETURN:
                        line, col = notepad_cursor
                        new_line = notepad_lines[line][col:]
                        notepad_lines[line] = notepad_lines[line][:col]
                        notepad_lines.insert(line+1, new_line)
                        notepad_cursor = [line+1, 0]
                    elif event.key == pygame.K_LEFT:
                        line, col = notepad_cursor
                        if col > 0:
                            notepad_cursor[1] -= 1
                        elif line > 0:
                            notepad_cursor = [line-1, len(notepad_lines[line-1])]
                    elif event.key == pygame.K_RIGHT:
                        line, col = notepad_cursor
                        if col < len(notepad_lines[line]):
                            notepad_cursor[1] += 1
                        elif line < len(notepad_lines)-1:
                            notepad_cursor = [line+1, 0]
                    elif event.key == pygame.K_UP:
                        line, col = notepad_cursor
                        if line > 0:
                            notepad_cursor = [line-1, min(col, len(notepad_lines[line-1]))]
                    elif event.key == pygame.K_DOWN:
                        line, col = notepad_cursor
                        if line < len(notepad_lines)-1:
                            notepad_cursor = [line+1, min(col, len(notepad_lines[line+1]))]
                    else:
                        if event.unicode.isprintable():
                            line, col = notepad_cursor
                            notepad_lines[line] = notepad_lines[line][:col] + event.unicode + notepad_lines[line][col:]
                            notepad_cursor[1] += 1

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                # Activate calculator if clicked
                if toggle_overlays[2]['visible'] and toggle_overlays[2]['rect'].collidepoint(mx, my):
                    calc_active = True
                    notepad_active = False
                # Activate notepad if clicked
                elif toggle_overlays[1]['visible'] and toggle_overlays[1]['rect'].collidepoint(mx, my):
                    notepad_active = True
                    calc_active = False
                else:
                    calc_active = False
                    notepad_active = False



        mx, my = mouse_pos
        overlays_all = [menu_overlay] + toggle_overlays

            
        # In your main loop, before drawing overlays, add:
        if pygame.time.get_ticks() - notepad_last_blink > 500:
            notepad_show_cursor = not notepad_show_cursor
            notepad_last_blink = pygame.time.get_ticks()

        if mouse_pressed[0] and not started_clicking:
            started_clicking = True
            # Check if clicking on a overlay. if so, start drag it
            # also, check the toggle buttons first up
            # Toggle buttons
            dont_do_anything = False
            for i, btn in enumerate(toggle_btns):
                if btn.collidepoint(mx, my):
                    dont_do_anything = True
            # If no toggle buttons in the way, set that overlay s the one being dragged
            if not dont_do_anything:
                for idx in reversed(z_order):
                    if overlays_all[idx].get('visible', True) and overlays_all[idx]['rect'].collidepoint(mx, my):
                        dragging_idx = idx
                        drag_offset = (mx - overlays_all[idx]['rect'].x, my - overlays_all[idx]['rect'].y)
                        # Bring to top (except menu)
                        if idx != 0:
                            z_order.remove(idx)
                            z_order.append(idx)
                        break
        
        if not mouse_pressed[0] and started_clicking:
            started_clicking = False
            # If we were dragging, snap to others and reset dragging index
            if dragging_idx is not None:
                snap_to_others(dragging_idx, overlays_all)
                dragging_idx = None

        if mouse_pressed[0]:
            if dragging_idx is None:
                # Check toggle buttons first (menu always at idx 0)
                for i, btn in enumerate(toggle_btns):
                    if btn.collidepoint(mx, my):
                        toggle_overlays[i]['visible'] = not toggle_overlays[i]['visible']
                        # Wait for mouse release to avoid rapid toggling
                        while mouse_pressed[0]:
                            pygame.event.pump()
                            clock.tick(60)
                        break
                else:
                    # Check overlays for dragging (topmost first, only visible overlays)
                    for idx in reversed(z_order):
                        if overlays_all[idx].get('visible', True):
                            if overlays_all[idx]['rect'].collidepoint(mx, my) and was_originally_dragging == overlays_all[idx]['label']:
                                dragging_idx = idx
                                drag_offset = (mx - overlays_all[idx]['rect'].x, my - overlays_all[idx]['rect'].y)
                                # Bring to top (except menu)
                                if idx != 0:
                                    z_order.remove(idx)
                                    z_order.append(idx)
                                break
            else:
                rect = overlays_all[dragging_idx]['rect']
                rect.x = mx - drag_offset[0]
                rect.y = my - drag_offset[1]
                clamp_rect(rect)
                snap_to_others(dragging_idx, overlays_all)
        else:
            dragging_idx = None
        # Update toggle button positions if menu moves
        for i, btn in enumerate(toggle_btns):
            btn.x = menu_overlay['rect'].x + 20
            btn.y = menu_overlay['rect'].y + 60 + i * 50

        screen.fill(TRANSPARENT)
        # Draw overlays in z-order
        for idx in z_order:
            """overlay = overlays_all[idx]
            if not overlay.get('visible', True):
                continue
            pygame.draw.rect(screen, overlay['color'], overlay['rect'])
            text = font.render(f"{overlay['label']} overlay", True, (0, 0, 0))
            text_rect = text.get_rect(center=overlay['rect'].center)
            screen.blit(text, text_rect)
            # Draw toggle buttons if menu
            if idx == 0:
                for i, btn in enumerate(toggle_btns):
                    pygame.draw.rect(screen, (180, 180, 180), btn)
                    label = small_font.render(f"Toggle {toggle_overlays[i]['label']} Overlay", True, (0, 0, 0))
                    screen.blit(label, (btn.x + 10, btn.y + 8))""" # Assumes all overlays are similar, too general
            # we need a huge match tower
            t = overlays_all[idx]["label"]
            overlay = overlays_all[idx]
            # First, if its disabled, skip
            if not overlay.get('visible', True):
                continue
            match t:
                case "Menu":
                    # Draw menu overlay as a gray boxoid with a ittle in the top left and toggle buttons
                    pygame.draw.rect(screen, (220, 220, 220), overlay['rect'])
                    text = font.render(f"{overlay['label']} overlay", True, (0, 0, 0))
                    text_rect = text.get_rect(topleft=(overlay['rect'].x + 10, overlay['rect'].y + 10))
                    screen.blit(text, text_rect)
                    # Draw toggle buttons
                    for i, btn in enumerate(toggle_btns):
                        pygame.draw.rect(screen, (180, 180, 180), btn)
                        label = small_font.render(f"Toggle {toggle_overlays[i]['label']} Overlay", True, (0, 0, 0))
                        screen.blit(label, (btn.x + 10, btn.y + 8))
                    # Draw border
                    pygame.draw.rect(screen, (0, 0, 0), overlay['rect'], 2)
                case "Clock":
                    pygame.draw.rect(screen, (100, 100, 100), overlay['rect'])
                    now = datetime.datetime.now()
                    time_str = now.strftime("%H:%M:%S")
                    date_str = now.strftime("%d/%m/%Y")
                    time_font = pygame.font.Font(None, 48)
                    time_text = time_font.render(time_str, True, (0, 0, 0))
                    date_text = small_font.render(date_str, True, (0, 0, 0))
                    screen.blit(time_text, (overlay['rect'].x + 20, overlay['rect'].y + 30))
                    screen.blit(date_text, (overlay['rect'].x + 20, overlay['rect'].y + 80))
                    pygame.draw.rect(screen, (0, 0, 0), overlay['rect'], 2)
                case "Notepad":
                    pygame.draw.rect(screen, (200, 200, 200), overlay['rect'])
                    text_area = pygame.Rect(overlay['rect'].x + 10, overlay['rect'].y + 10, overlay['rect'].width - 20, overlay['rect'].height - 20)
                    pygame.draw.rect(screen, (255, 255, 255), text_area)
                    x, y = text_area.x + 5, text_area.y + 5
                    line_height = small_font.get_height() + 2
                    max_width = text_area.width - 10
                    max_lines = (text_area.height - 10) // line_height

                    hyphen = "-"
                    draw_lines = []
                    cursor_vis_line = 0  # The line index where the cursor should be drawn (in draw_lines)
                    cursor_vis_x = x     # The x position for the cursor

                    # --- Build draw_lines and track cursor position ---
                    cursor_abs_line = 0
                    for lidx, line in enumerate(notepad_lines):
                        words = line.split(' ')
                        current = ""
                        for word in words:
                            test = current + ("" if current == "" else " ") + word
                            if small_font.size(test)[0] > max_width and current != "":
                                draw_lines.append(current)
                                current = word
                            else:
                                current = test
                            # Hard wrap for long words with hyphen
                            while small_font.size(current)[0] > max_width:
                                for i in range(1, len(current)+1):
                                    if small_font.size(current[:i] + hyphen)[0] > max_width:
                                        break
                                else:
                                    i = len(current)
                                if i == 1:
                                    draw_lines.append(current[:1] + hyphen)
                                    current = current[1:]
                                else:
                                    draw_lines.append(current[:i-1] + hyphen)
                                    current = current[i-1:]
                        draw_lines.append(current)

                        # Track cursor's visual line and x
                        if lidx == notepad_cursor[0]:
                            # Now, find which visual line and x the cursor is on
                            upto = notepad_lines[lidx][:notepad_cursor[1]]
                            words2 = upto.split(' ')
                            current2 = ""
                            for word2 in words2:
                                test2 = current2 + ("" if current2 == "" else " ") + word2
                                if small_font.size(test2)[0] > max_width and current2 != "":
                                    cursor_vis_line += 1
                                    current2 = word2
                                else:
                                    current2 = test2
                                while small_font.size(current2)[0] > max_width:
                                    for i in range(1, len(current2)+1):
                                        if small_font.size(current2[:i] + hyphen)[0] > max_width:
                                            break
                                    else:
                                        i = len(current2)
                                    if i == 1:
                                        cursor_vis_line += 1
                                        current2 = current2[1:]
                                    else:
                                        cursor_vis_line += 1
                                        current2 = current2[i-1:]
                            cursor_vis_x = x + small_font.size(current2)[0]
                        else:
                            # For each line before the cursor line, increment cursor_vis_line
                            if lidx < notepad_cursor[0]:
                                # Count how many visual lines this logical line took
                                words2 = line.split(' ')
                                current2 = ""
                                for word2 in words2:
                                    test2 = current2 + ("" if current2 == "" else " ") + word2
                                    if small_font.size(test2)[0] > max_width and current2 != "":
                                        cursor_vis_line += 1
                                        current2 = word2
                                    else:
                                        current2 = test2
                                    while small_font.size(current2)[0] > max_width:
                                        for i in range(1, len(current2)+1):
                                            if small_font.size(current2[:i] + hyphen)[0] > max_width:
                                                break
                                        else:
                                            i = len(current2)
                                        if i == 1:
                                            cursor_vis_line += 1
                                            current2 = current2[1:]
                                        else:
                                            cursor_vis_line += 1
                                            current2 = current2[i-1:]
                                cursor_vis_line += 1

                    # --- Auto-scroll so cursor is always visible ---
                    if cursor_vis_line < notepad_scroll:
                        notepad_scroll = cursor_vis_line
                    elif cursor_vis_line >= notepad_scroll + max_lines:
                        notepad_scroll = cursor_vis_line - max_lines + 1

                    # Only draw visible lines
                    visible_lines = draw_lines[notepad_scroll:notepad_scroll+max_lines]
                    for i, line in enumerate(visible_lines):
                        txt = small_font.render(line, True, (0, 0, 0))
                        screen.blit(txt, (x, y + i * line_height))

                    # Draw cursor if active and visible
                    if notepad_active and notepad_show_cursor:
                        rel_line = cursor_vis_line - notepad_scroll
                        if 0 <= rel_line < max_lines:
                            pygame.draw.line(screen, (0, 0, 0), (cursor_vis_x, y + rel_line * line_height), (cursor_vis_x, y + rel_line * line_height + line_height), 2)
                    pygame.draw.rect(screen, (0, 0, 0), overlay['rect'], 2)
                case "Calculator":
                    pygame.draw.rect(screen, (220, 220, 220), overlay['rect'])
                    input_rect = pygame.Rect(overlay['rect'].x + 10, overlay['rect'].y + 20, overlay['rect'].width - 20, 40)
                    pygame.draw.rect(screen, (240, 240, 240), input_rect)
                    # Clip input text if too long
                    input_display = calc_input
                    while font.size(input_display)[0] > input_rect.width - 10 and len(input_display) > 0:
                        input_display = input_display[1:]
                    input_text = font.render(input_display, True, (0, 0, 0))
                    screen.blit(input_text, (input_rect.x + 5, input_rect.y + 5))
                    # Draw blinking cursor if active
                    if calc_active and notepad_show_cursor:
                        cursor_x = input_rect.x + 5 + font.size(input_display)[0]
                        cursor_y = input_rect.y + 5
                        pygame.draw.line(screen, (0, 0, 0), (cursor_x, cursor_y), (cursor_x, cursor_y + font.get_height()), 2)
                    # Clip result text if too long
                    result_display = f"= {calc_result}"
                    while small_font.size(result_display)[0] > input_rect.width - 10 and len(result_display) > 0:
                        # You hardly care about tyhe last decimals, and theyre likely floating point mistakes, so start rmeoving the end, not the start
                        result_display = result_display[:-1]
                    result_text = small_font.render(result_display, True, (0, 0, 0))
                    screen.blit(result_text, (input_rect.x + 5, input_rect.y + 50))
                    pygame.draw.rect(screen, (0, 0, 0), overlay['rect'], 2)

        pygame.display.update()
        clock.tick(60)
except Exception as e:
    with open("noooooooo.txt", "w") as f:
        f.write(f"Error: {e.__class__.__name__}: {e}\n")

finally:
    with open("notesdata.txt", "w") as f:
        k = 0
        for line in notepad_lines:
            k += 1
            fin = k == len(notepad_lines)
            f.write(line + "\n" if not fin else line)

    # cleanup listerners pyggame and some other things
    listener.stop()
    pygame.quit()
    sys.exit()