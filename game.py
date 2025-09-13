import pgzrun
from platformer import *
import sys

# Platform constants
TILE_SIZE = 21
ROWS = 50
COLS = 30

# Pygame constants
WIDTH = TILE_SIZE * ROWS
HEIGHT = TILE_SIZE * COLS
TITLE = " "

# World
platforms = build("platformer_platformer.csv", TILE_SIZE)
obstacles = build("platformer_obstacles.csv", TILE_SIZE)
coins = build("platformer_coins.csv", TILE_SIZE)
scenery = build("platformer_cenario.csv", TILE_SIZE)

# Sprite definitions
# Sprite("sprite_image.png", start, num_frames, color_key, refresh)
color_key = (0, 0, 0)
fox_walk = Sprite("raposa.png", (0, 64, 32, 32), 8, color_key, 5)
fox_idle = Sprite("raposa.png", (0, 32, 32, 32), 14, color_key, 30)
pig_walk = Sprite("porco.png", (0, 0, 32, 32), 5, color_key, 30)
pig_idle = Sprite("porco.png", (0, 32, 32, 32), 5, color_key, 5)

# Player setup
player = SpriteActor(fox_idle)
player.bottomleft = (0, HEIGHT - TILE_SIZE)
player.velocity_x = 3
player.velocity_y = 0
player.jumping = False
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

# Enemy logic
class PigEnemy(SpriteActor):
    def __init__(self, sprite, platform):
        super().__init__(sprite)
        self.x = platform.x + platform.width // 2
        self.y = platform.y - platform.height // 2 - self.height // 2
        self.velocity_x = 1
        self.platform = platform
        self.flip_x = False

    def move(self):
        self.x += self.velocity_x
        # Check for edge of platform (cliff)
        if self.velocity_x < 0:  # Moving left
            foot_x = self.x - self.width // 2
            foot_y = self.y + self.height // 2 + 2
        else:  # Moving right
            foot_x = self.x + self.width // 2
            foot_y = self.y + self.height // 2 + 2

        on_platform = False
        for plat in platforms:
            if plat.collidepoint((foot_x, foot_y)):
                on_platform = True
                break

        if not on_platform:
            self.velocity_x *= -1
            self.flip_x = not self.flip_x

        # Prevent leaving platform bounds
        if self.x < self.platform.x + self.width // 2:
            self.x = self.platform.x + self.width // 2
            self.velocity_x = abs(self.velocity_x)
            self.flip_x = False
        if self.x > self.platform.x + self.platform.width - self.width // 2:
            self.x = self.platform.x + self.platform.width - self.width // 2
            self.velocity_x = -abs(self.velocity_x)
            self.flip_x = True

# Create pig enemies on specific platforms
pig_platform_indices = [4, 91, 78, 68, 60]
pig_enemies = []
for idx in pig_platform_indices:
    plat = platforms[idx]
    pig = PigEnemy(pig_walk, plat)
    pig_enemies.append(pig)

enemies = pig_enemies

def move_enemies():
    for pig in pig_enemies:
        pig.move()

clock.schedule_interval(move_enemies, .01)

def draw():
    screen.clear()
    if game_state == "menu":
        draw_menu()
    else:
        screen.fill("skyblue")
        for i, platform in enumerate(platforms):
            platform.draw()
            screen.draw.text(str(i), (platform.x, platform.y), fontsize=20, color="red")
        for obstacle in obstacles:
            obstacle.draw()
        for coin in coins:
            coin.draw()
        for scene in scenery:
            scene.draw()
        for pig in pig_enemies:
            pig.draw()
        if player.alive:
            player.draw()
        if game_over:
            screen.draw.text("Game Over!", center=(WIDTH/2, HEIGHT/2), fontsize=60, color="red")
            draw_gameover_menu()
        if game_win:
            screen.draw.text("You Win!", center=(WIDTH/2, HEIGHT/2), fontsize=60, color="green")

def draw_menu():
    screen.blit("menu", (0, 0))  # Background image stretched

    # Buttons on the right
    button_w = 200
    button_h = 60
    button_gap = 30
    top_margin = 40
    right_margin = 60

    button_x = WIDTH - button_w - right_margin
    button_start_y = top_margin
    button_music_y = button_start_y + button_h + button_gap
    button_sound_y = button_music_y + button_h + button_gap
    button_exit_y = button_sound_y + button_h + button_gap

    button_start = Rect((button_x, button_start_y), (button_w, button_h))
    button_music = Rect((button_x, button_music_y), (button_w, button_h))
    button_sound = Rect((button_x, button_sound_y), (button_w, button_h))
    button_exit = Rect((button_x, button_exit_y), (button_w, button_h))

    screen.draw.filled_rect(button_start, "green")
    screen.draw.text("START", center=button_start.center, fontsize=40, color="white")

    screen.draw.filled_rect(button_music, "blue")
    music_text = "Music: On" if music_on else "Music: Off"
    screen.draw.text(music_text, center=button_music.center, fontsize=32, color="white")

    screen.draw.filled_rect(button_sound, "orange")
    sound_text = "Sound: On" if sound_on else "Sound: Off"
    screen.draw.text(sound_text, center=button_sound.center, fontsize=32, color="black")

    screen.draw.filled_rect(button_exit, "red")
    screen.draw.text("QUIT", center=button_exit.center, fontsize=40, color="white")

    global menu_buttons
    menu_buttons = {
        "start": button_start,
        "music": button_music,
        "sound": button_sound,
        "exit": button_exit
    }

def draw_gameover_menu():
    button_menu = Rect((WIDTH/2 - 100, HEIGHT/2 + 80), (200, 60))
    screen.draw.filled_rect(button_menu, "purple")
    screen.draw.text("MENU", center=button_menu.center, fontsize=40, color="white")

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

def update():
    global game_over, game_win

    if game_state == "menu":
        start_menu_music()
        return

    if game_over or not player.alive:
        return

    if not music.is_playing("house") and music_on and not game_over:
        start_game_music()

    # Player movement left
    if keyboard.LEFT and player.midleft[0] > 0:
        player.x -= player.velocity_x
        player.sprite = fox_walk
        player.flip_x = True
        if player.collidelist(platforms) != -1:
            obj = platforms[player.collidelist(platforms)]
            player.x = obj.x + (obj.width/2 + player.width/2)

    # Player movement right
    elif keyboard.RIGHT and player.midright[0] < WIDTH:
        player.x += player.velocity_x
        player.sprite = fox_walk
        player.flip_x = False
        if player.collidelist(platforms) != -1:
            obj = platforms[player.collidelist(platforms)]
            player.x = obj.x - (obj.width/2 + player.width/2)

    # Gravity
    player.y += player.velocity_y
    player.velocity_y += gravity

    if player.collidelist(platforms) != -1:
        obj = platforms[player.collidelist(platforms)]
        if player.velocity_y > 0:
            player.y = obj.y - (obj.height/2 + player.height/2)
            player.jumping = False
        else:
            player.y = obj.y + (obj.height/2 + player.height/2)
        player.velocity_y = 0

    # Collision with obstacles
    if player.collidelist(obstacles) != -1:
        if sound_on and player.alive:
            sounds.hero_hurt.play()
            sounds.gameover.play()
        player.alive = False
        game_over = True
        stop_game_music()

    # Collision with enemies
    for enemy in enemies:
        if player.colliderect(enemy) and player.alive:
            if sound_on:
                sounds.hero_hurt.play()
                sounds.gameover.play()
            player.alive = False
            game_over = True
            stop_game_music()

    # Collision with coins
    for coin in coins[:]:
        if player.colliderect(coin):
            coins.remove(coin)
            if sound_on:
                sounds.money.play()
    
    if len(coins) == 0:
        game_win = True

def on_key_down(key):
    global game_state, game_over
    if game_state == "menu":
        if key == keys.RETURN or key == keys.ENTER:
            game_state = "playing"
            start_game_music()
        return
    if game_over or not player.alive:
        return
    if key == keys.SPACE and not player.jumping:
        player.velocity_y = jump_velocity
        player.jumping = True

def on_mouse_down(pos):
    global game_state, music_on, sound_on, game_over
    if game_state == "menu":
        btns = menu_buttons
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
            sys.exit()
    elif game_over:
        button_menu = Rect((WIDTH/2 - 100, HEIGHT/2 + 80), (200, 60))
        if button_menu.collidepoint(pos):
            reset_game()
            stop_game_music()
            game_state = "menu"

def reset_game():
    global player, game_over, game_win, coins
    player.x = 0
    player.y = HEIGHT - TILE_SIZE
    player.alive = True
    player.velocity_x = 3
    player.velocity_y = 0
    player.jumping = False
    player.sprite = fox_idle
    game_over = False
    game_win = False
    coins = build("platformer_coins.csv", TILE_SIZE)
    start_game_music()

def on_key_up(key):
    if game_state == "menu" or game_over:
        return
    if key == keys.LEFT or key == keys.RIGHT:
        player.sprite = fox_idle

pgzrun.go()