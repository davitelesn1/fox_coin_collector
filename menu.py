from pygame import Rect
from pgzero.builtins import keys
_buttons = {}

def draw_menu(screen, WIDTH, music_on=True, sound_on=True):
    screen.blit("menu", (0, 0))

    button_w = 200
    button_h = 60
    button_gap = 30
    bottom_margin = 40
    right_margin = 60

    button_x = screen.width - button_w - right_margin
    total_buttons = 4
    total_height = total_buttons * button_h + (total_buttons - 1) * button_gap
    button_start_y = screen.height - bottom_margin - total_height
    button_music_y = button_start_y + button_h + button_gap
    button_sound_y = button_music_y + button_h + button_gap
    button_exit_y = button_sound_y + button_h + button_gap

    start = Rect((button_x, button_start_y), (button_w, button_h))
    music = Rect((button_x, button_music_y), (button_w, button_h))
    sound = Rect((button_x, button_sound_y), (button_w, button_h))
    exitb = Rect((button_x, button_exit_y), (button_w, button_h))

    screen.draw.filled_rect(start, "orange")
    screen.draw.text("START", center=start.center, fontsize=40, color="black")

    screen.draw.filled_rect(music, "orange")
    screen.draw.filled_rect(sound, "orange")
    screen.draw.filled_rect(exitb, "orange")
    screen.draw.text("QUIT", center=exitb.center, fontsize=40, color="black")
    # Dynamic labels for music/sound
    music_text = "Music: On" if music_on else "Music: Off"
    sound_text = "Sound: On" if sound_on else "Sound: Off"
    screen.draw.text(music_text, center=music.center, fontsize=32, color="black")
    screen.draw.text(sound_text, center=sound.center, fontsize=32, color="black")

    global _buttons
    _buttons = {
        "start": start,
        "music": music,
        "sound": sound,
        "exit": exitb,
    }
    return _buttons

def get_buttons():
    return _buttons

def handle_menu_key(key):
    if key == keys.RETURN or (hasattr(keys, 'ENTER') and key == getattr(keys, 'ENTER')):
        return "start"
    if key == keys.SPACE:
        return None
    return None

def draw_gameover_screen(screen, WIDTH, HEIGHT):
    try:
        screen.blit("gameover", (-100, -30))
    except Exception:
        screen.clear()
        screen.fill("black")
    screen.draw.text("Pressione ENTER ou ESPAÇO", center=(WIDTH/2, HEIGHT/2 + 20), fontsize=40, color="white")
    screen.draw.text("para voltar ao menu", center=(WIDTH/2, HEIGHT/2 + 60), fontsize=30, color="white")

def draw_win_screen(screen, WIDTH, HEIGHT):
    try:
        screen.blit("win", (-70, -70))
    except Exception:
        screen.clear()
        screen.fill("black")
    screen.draw.text("Pressione ENTER ou ESPAÇO", center=(WIDTH/2, HEIGHT/2 + 20), fontsize=40, color="white")
    screen.draw.text("para voltar ao menu", center=(WIDTH/2, HEIGHT/2 + 60), fontsize=30, color="white")
