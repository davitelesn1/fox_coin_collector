from platformer import SpriteActor
from collisions import platform_collide


## Using shared collisions.pixel_perfect_collide


class Player(SpriteActor):
    def __init__(self, idle_sprite, walk_sprite, width, height, platforms, obstacles, gravity=1, speed=3, jump_velocity=-13):
        super().__init__(idle_sprite)
        self.idle_sprite = idle_sprite
        self.walk_sprite = walk_sprite
        self.sprite = idle_sprite
        self.velocity_x = speed
        self.velocity_y = 0
        self.jumping = False
        self.alive = True
        self.scale = 1
        self.flip_x = False
        self._platforms = platforms
        self._obstacles = obstacles
        self._gravity = gravity
        self._jump_velocity = jump_velocity
        self._world_w = width
        self._world_h = height
        self.grounded = False

    def _find_solid_platform(self):
        for plat in self._platforms:
            if self.colliderect(plat) and platform_collide(self, plat):
                return plat
        return None

    def handle_input(self, keyboard):
        moved = False
        if getattr(keyboard, 'left') and self.midleft[0] > 0:
            self.x -= self.velocity_x
            self.sprite = self.walk_sprite
            self.flip_x = True
            moved = True
            obj = self._find_solid_platform()
            if obj is not None:
                self.x = obj.x + (obj.width/2 + self.width/2)
        elif getattr(keyboard, 'right') and self.midright[0] < self._world_w:
            self.x += self.velocity_x
            self.sprite = self.walk_sprite
            self.flip_x = False
            moved = True
            obj = self._find_solid_platform()
            if obj is not None:
                self.x = obj.x - (obj.width/2 + self.width/2)
        if not moved:
            self.sprite = self.idle_sprite

    def jump(self):
        if not self.jumping:
            self.velocity_y = self._jump_velocity
            self.jumping = True
            self.grounded = False

    def apply_gravity(self):
        # If currently grounded, keep attached to ground with a small downward probe
        if self.grounded:
            snap_done = False
            for probe in (1, 2):
                self.y += probe
                obj = self._find_solid_platform()
                if obj is not None:
                    self.y = obj.y - (obj.height/2 + self.height/2)
                    self.velocity_y = 0
                    self.jumping = False
                    snap_done = True
                    break
                self.y -= probe
            if snap_done:
                return
            # no ground below within tolerance -> start falling
            self.grounded = False

        # Apply gravity when not grounded
        self.y += self.velocity_y
        self.velocity_y += self._gravity
        obj = self._find_solid_platform()
        if obj is not None:
            if self.velocity_y > 0:
                # Land on top
                self.y = obj.y - (obj.height/2 + self.height/2)
                self.jumping = False
                self.grounded = True
                # Ensure stable resting
                self.velocity_y = 0
                return
            else:
                # Hit head under a platform
                self.y = obj.y + (obj.height/2 + self.height/2)
                self.velocity_y = 0

    def hit_obstacle(self):
        return self.collidelist(self._obstacles) != -1

    def update(self, keyboard):
        if not self.alive:
            return
        self.handle_input(keyboard)
        self.apply_gravity()
