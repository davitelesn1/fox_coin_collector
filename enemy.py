import random
from platformer import SpriteActor

class PigEnemy(SpriteActor):
    def __init__(self, walk_sprite, idle_sprite, platform, platforms, tile_size, speed=1.0):
        super().__init__(walk_sprite)
        self.walk_sprite = walk_sprite
        self.idle_sprite = idle_sprite
        self.speed = speed
        self.velocity_x = self.speed
        self.platform = platform
        self.flip_x = False
        self.state = "walk"  # walk | idle
        self.pause_point = None
        self.pause_timer = 0   # frames
        self.dir_sign = 1      # 1 right, -1 left
        self._platforms = platforms
        self._tile_size = tile_size
        # position on top of platform
        self.x = platform.x + platform.width // 2
        self.y = platform.y - platform.height // 2 - self.height // 2
        # Determine patrol bounds across contiguous tiles
        self.left_bound, self.right_bound = self._compute_patrol_bounds(platform)

    def _compute_patrol_bounds(self, start_platform):
        lookup = {(plat.x, plat.y): plat for plat in self._platforms}
        left_plat = start_platform
        while (left_plat.x - self._tile_size, left_plat.y) in lookup:
            left_plat = lookup[(left_plat.x - self._tile_size, left_plat.y)]
        right_plat = start_platform
        while (right_plat.x + self._tile_size, right_plat.y) in lookup:
            right_plat = lookup[(right_plat.x + self._tile_size, right_plat.y)]
        left_bound = left_plat.x - (left_plat.width // 2) + (self.width // 2)
        right_bound = right_plat.x + (right_plat.width // 2) - (self.width // 2)
        return left_bound, right_bound

    def move(self):
        # Idle state
        if self.state == "idle":
            if self.pause_timer > 0:
                self.pause_timer -= 1
            if self.pause_timer <= 0:
                self.state = "walk"
                self.sprite = self.walk_sprite
                self.velocity_x = self.speed * self.dir_sign
                self.flip_x = True if self.dir_sign < 0 else False
                self.pause_point = None
            return

        # Walking
        self.x += self.velocity_x
        if self.velocity_x < 0:
            foot_x = self.x - self.width // 2
            foot_y = self.y + self.height // 2 + 2
        else:
            foot_x = self.x + self.width // 2
            foot_y = self.y + self.height // 2 + 2

        on_platform = False
        for plat in self._platforms:
            if plat.collidepoint((foot_x, foot_y)):
                on_platform = True
                break

        if not on_platform:
            self.velocity_x *= -1
            self.dir_sign = 1 if self.velocity_x > 0 else -1
            self.flip_x = not self.flip_x
            self.pause_point = None

        if self.x < self.left_bound:
            self.x = self.left_bound
            self.velocity_x = abs(self.velocity_x)
            self.dir_sign = 1
            self.flip_x = False
            self.pause_point = None
        if self.x > self.right_bound:
            self.x = self.right_bound
            self.velocity_x = -abs(self.velocity_x)
            self.dir_sign = -1
            self.flip_x = True
            self.pause_point = None

        # Random pause
        if self.pause_point is None and random.random() < 0.007:
            left = int(self.left_bound + 2)
            right = int(self.right_bound - 2)
            if right >= left:
                self.pause_point = random.randint(left, right)

        if self.pause_point is not None:
            if (self.velocity_x > 0 and self.x >= self.pause_point) or (self.velocity_x < 0 and self.x <= self.pause_point):
                self.state = "idle"
                self.sprite = self.idle_sprite
                self.dir_sign = 1 if self.velocity_x > 0 else -1
                self.velocity_x = 0
                self.pause_timer = random.randint(60, 180)
                self.flip_x = True if self.dir_sign < 0 else False
