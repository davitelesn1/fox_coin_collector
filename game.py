import pgzrun
import random
from platformer import build, Sprite, SpriteActor
from pgzero import loaders
from collisions import pixel_perfect_collide, platform_collide, first_hit_pixel, any_hit_pixel, first_hit_aabb
from pygame import Rect
from enemy import PigEnemy
from typing import Any
from player import Player
import menu as menu_mod

# PgZero injects these globals at runtime: screen, music, sounds, keys, keyboard.
screen: Any
music: Any
sounds: Any
keys: Any
keyboard: Any

# Platform constants
TILE_SIZE = 21
ROWS = 50
COLS = 30

# Hints above are for linters only; PgZero provides the actual objects at runtime.

# Pygame constants
WIDTH = TILE_SIZE * ROWS
HEIGHT = TILE_SIZE * COLS
TITLE = " "

 # World
platforms = build("platformer_platformer.csv", TILE_SIZE)
obstacles = build("platformer_obstacles.csv", TILE_SIZE)
coins = build("platformer_coins.csv", TILE_SIZE)
scenery = build("platformer_cenario.csv", TILE_SIZE)

total_coins = len(coins)
coins_collected = 0

HUD_Y = 10
HEART_SIZE = 28
HEART_EXTRA_PADDING = 14
COIN_SOUND_VOLUME = 0.25
GAMEOVER_Y_OFFSET = 40
WIN_Y_OFFSET = 40

# Lives
MAX_LIVES = 3
lives = MAX_LIVES
INVULN_FRAMES = 90  # ~1.5s at 60 FPS
invuln_timer = 0
SPAWN_BOTTOMLEFT = (0, HEIGHT - TILE_SIZE)

color_key = (0, 0, 0)
# As retângulos left_rect assumem que a spritesheet possui uma linha espelhada do mesmo tamanho
# Se não existir, o código cai em fallback e usa os frames padrão (sem flip visual)
fox_walk = Sprite("fox.png", (0, 64, 32, 32), 8, color_key, 5)
fox_idle = Sprite("fox.png", (0, 32, 32, 32), 14, color_key, 30)
pig_walk = Sprite("pig.png", (0, 0, 32, 32), 5, color_key, 30, left_rect=(0, 0, 32, 32))
pig_idle = Sprite("pig.png", (0, 32, 32, 32), 5, color_key, 30, left_rect=(0, 32, 32, 32))

player = Player(fox_idle, fox_walk, WIDTH, HEIGHT, platforms, obstacles, gravity=1, speed=3, jump_velocity=-13)
player.bottomleft = (0, HEIGHT - TILE_SIZE)
player.alive = True
player.scale = 1
player.sprite = fox_idle

 # Game state variables
gravity = 1
jump_velocity = -13
game_over = False
game_win = False
game_state = "menu"  # "menu" or "playing"
music_on = True
sound_on = True
game_paused = False  # pausa do jogo

PIG_SPEED = 0.6

timer_seconds = 500
timer = timer_seconds
timer_active = False

# Create pig enemies on specific platforms
pig_platform_indices = [3, 4, 29, 68, 91, 147]
pig_enemies = []
for idx in pig_platform_indices:
    plat = platforms[idx]
    pig = PigEnemy(pig_walk, pig_idle, plat, platforms, TILE_SIZE, speed=PIG_SPEED)
    pig_enemies.append(pig)

enemies = pig_enemies

def draw_background():
    try:
        sky = loaders.images.load("sky")
        sw, sh = sky.get_size()
        # Azuleja a imagem para cobrir a tela toda
        for y in range(0, HEIGHT, sh):
            for x in range(0, WIDTH, sw):
                screen.blit("sky", (x, y))
    except Exception:
        # Fallback caso a imagem não exista
        screen.fill("skyblue")

def draw_heart(x, y, size=20, color="red"):
    # Coração pixelado (8x7) escalável
    pattern = [
        "01100110",
        "11111111",
        "11111111",
        "11111111",
        "01111110",
        "00111100",
        "00011000",
    ]
    scale = max(1, int(size / 8))
    for row, line in enumerate(pattern):
        for col, ch in enumerate(line):
            if ch == '1':
                rx = x + col * scale
                ry = y + row * scale
                screen.draw.filled_rect(Rect((rx, ry), (scale, scale)), color)

def draw_hud():
    coin_text = f"{coins_collected}/{total_coins}"
    COIN_FONT_SIZE = 40
    screen.draw.text(coin_text, (30, HUD_Y), fontsize=COIN_FONT_SIZE, color="yellow")
    est_char_w = int(0.6 * COIN_FONT_SIZE)
    hearts_start_x = 30 + len(coin_text) * est_char_w + HEART_EXTRA_PADDING
    heart_scale = max(1, int(HEART_SIZE / 8))
    heart_width = 8 * heart_scale
    heart_gap = max(4, heart_scale)
    for i in range(lives):
        draw_heart(hearts_start_x + i * (heart_width + heart_gap), HUD_Y - 2, size=HEART_SIZE, color="red")
    screen.draw.text("Press P to pause", center=(WIDTH/2, 20), fontsize=28, color="white")
    timer_text = f"Tempo: {int(timer)}s"
    screen.draw.text(timer_text, (WIDTH - 200, HUD_Y), fontsize=40, color="black")

def draw():
    screen.clear()
    if game_state == "menu":
        draw_menu()
    else:
        # Background image (tiling + fallback)
        draw_background()
        for i, platform in enumerate(platforms):
            platform.draw()
        for obstacle in obstacles:
            obstacle.draw()
        for coin in coins:
            coin.draw()
        for scene in scenery:
            scene.draw()
        for pig in pig_enemies:
            pig.draw()
        if player.alive:
            # Blink while invulnerable to give feedback
            if invuln_timer <= 0 or ((invuln_timer // 5) % 2 == 0):
                player.draw()
        draw_hud()
        if game_over:
            draw_gameover_screen()
        if game_win:
            draw_win_screen()

def draw_menu():
    menu_mod.draw_menu(screen, WIDTH, music_on=music_on, sound_on=sound_on)

def draw_gameover_menu():
    draw_gameover_screen()

def _draw_fullscreen_image(key: str):
    try:
        surf = loaders.images.load(key)
        sw, sh = surf.get_size()
        x = (WIDTH - sw) // 2
        y = (HEIGHT - sh) // 2
        screen.blit(surf, (x, y))
    except Exception:
        screen.fill("black")

def draw_gameover_screen():
    menu_mod.draw_gameover_screen(screen, WIDTH, HEIGHT)

def draw_win_screen():
    menu_mod.draw_win_screen(screen, WIDTH, HEIGHT)

def start_menu_music():
    if music_on and not music.is_playing('sneaking_around'):
        music.play('sneaking_around')
        music.set_volume(0.5)

def start_game_music():
    if music_on and not music.is_playing("house"):
        music.stop()
        music.play("house")
        music.set_volume(0.7)

def stop_game_music():
    music.stop()

# Helpers
def lose_life_and_respawn():
    global lives, game_over, invuln_timer
    # Prevent multiple triggers during invulnerability window
    if invuln_timer > 0:
        return
    lives -= 1
    if lives <= 0:
        game_over = True
        player.alive = False
        stop_game_music()
        if sound_on:
            sounds.gameover.play()
        return
    # Respawn player at initial position with brief invulnerability
    player.bottomleft = SPAWN_BOTTOMLEFT
    player.velocity_x = 3
    player.velocity_y = 0
    player.jumping = False
    player.sprite = fox_idle
    invuln_timer = INVULN_FRAMES

def warp_to_spawn_no_penalty():
    """Teleport the player back to spawn without losing a life (used during invulnerability)."""
    player.bottomleft = SPAWN_BOTTOMLEFT
    player.velocity_x = 3
    player.velocity_y = 0
    player.jumping = False
    player.sprite = fox_idle

def update():
    global game_over, game_win, timer, timer_active, coins_collected, invuln_timer, game_paused

    if game_state == "menu":
        start_menu_music()
        timer_active = False
        return

    if game_over or not player.alive:
        timer_active = False
        return

    if not music.is_playing("house") and music_on and not game_over and not game_win:
        start_game_music()

    # Aplicar estado de pausa nas sprites (congela animação)
    player.paused = game_paused
    for enemy in enemies:
        enemy.paused = game_paused

    # Se pausado, não atualiza lógica de jogo
    if game_paused:
        return

    for enemy in enemies:
        enemy.move()

    # Invulnerability timer countdown after respawn
    if invuln_timer > 0:
        invuln_timer -= 1

    # Timer logic
    if not timer_active:
        timer_active = True
    if timer_active:
        timer -= 1/60  # update é chamado ~60 vezes por segundo
        if timer <= 0:
            timer = 0
            game_over = True
            player.alive = False
            stop_game_music()
            if sound_on:
                sounds.gameover.play()

    # Delegate movement and gravity to Player
    player.update(keyboard)

    # Collision with obstacles (spikes/lava) pixel-perfect
    # If invulnerable, warp back to spawn without losing life to avoid falling into void.
    if any_hit_pixel(player, obstacles):
        if invuln_timer <= 0:
            if sound_on:
                sounds.hero_hurt.play()
            lose_life_and_respawn()
        else:
            warp_to_spawn_no_penalty()

    # Collision with enemies -> pixel-perfect -> lose a life and respawn
    if invuln_timer <= 0 and player.alive:
        if any_hit_pixel(player, enemies):
            if sound_on:
                sounds.hero_hurt.play()
            lose_life_and_respawn()

    # Collision with coins
    hit_coin = first_hit_aabb(player, coins)
    if hit_coin:
        try:
            coins.remove(hit_coin)
        except Exception:
            pass
        coins_collected += 1
        if sound_on:
            try:
                sounds.money.set_volume(COIN_SOUND_VOLUME)
            except Exception:
                pass
            sounds.money.play()
    
    # Fail-safe: if player falls below the screen, respawn appropriately
    if player.top > HEIGHT + TILE_SIZE:
        if invuln_timer > 0:
            warp_to_spawn_no_penalty()
        else:
            lose_life_and_respawn()

    # Win when all coins are collected
    if len(coins) == 0:
        game_win = True
        timer_active = False

def on_key_down(key):
    global game_state, game_over, game_paused
    if game_state == "menu":
        action = menu_mod.handle_menu_key(key)
        if action == "start":
            game_state = "playing"
            try:
                music.stop()
            except Exception:
                pass
            start_game_music()
        return
    # On Game Over/Win screens: allow quick return to menu
    if game_over or game_win:
        ok = {keys.SPACE, keys.RETURN}
        if hasattr(keys, 'ENTER'):
            ok.add(getattr(keys, 'ENTER'))
        if key in ok:
            reset_game()
            stop_game_music()
            game_state = "menu"
        return
    if not player.alive:
        return
    # Toggle pausa
    if key == keys.P:
        game_paused = not game_paused
        return
    if key == keys.SPACE and not player.jumping:
        player.jump()

def on_mouse_down(pos):
    global game_state, music_on, sound_on, game_over
    if game_state == "menu":
        btns = menu_mod.get_buttons()
        if btns["start"].collidepoint(pos):
            stop_game_music()
            game_state = "playing"
            start_game_music()
        elif btns["music"].collidepoint(pos):
            music_on = not music_on
            if not music_on:
                stop_game_music()
            else:
                if game_state == "playing" and not game_over:
                    start_game_music()
        elif btns["sound"].collidepoint(pos):
            sound_on = not sound_on
        elif btns["exit"].collidepoint(pos):
            raise SystemExit
    elif game_over or game_win:
        # Any click returns to menu from game over/win
        reset_game()
        stop_game_music()
        game_state = "menu"

def reset_game():
    global player, game_over, game_win, coins, coins_collected, timer, timer_active, lives, invuln_timer
    player.bottomleft = SPAWN_BOTTOMLEFT
    player.alive = True
    player.velocity_y = 0
    player.jumping = False
    player.sprite = fox_idle
    game_over = False
    game_win = False
    coins = build("platformer_coins.csv", TILE_SIZE)
    coins_collected = 0
    timer = timer_seconds
    timer_active = False
    lives = MAX_LIVES
    invuln_timer = 0
    start_game_music()

def on_key_up(key):
    if game_state == "menu" or game_over:
        return
    if key == keys.LEFT or key == keys.RIGHT:
        player.sprite = fox_idle

pgzrun.go()