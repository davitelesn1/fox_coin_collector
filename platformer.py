from pgzero import game, loaders
from pgzero.actor import Actor, POS_TOPLEFT, ANCHOR_CENTER, transform_anchor


def build(filename, tile_size):
    with open(filename, "r") as f:
        contents = f.read().splitlines()

    contents = [c.split(",") for c in contents]
    for row in range(len(contents)):
        for col in range(len(contents[0])):
            val = contents[row][col]
            if val.isdigit() or (val[0] == "-" and val[1:].isdigit()):
                contents[row][col] = int(val)

    items = []
    for row in range(len(contents)):
        for col in range(len(contents[0])):
            tile_num = contents[row][col]
            if tile_num != -1:
                flipped_h = bool(tile_num & 0x80000000)
                flipped_v = bool(tile_num & 0x40000000)
                flipped_d = bool(tile_num & 0x20000000)
                rotated_hex = bool(tile_num & 0x10000000)
                tile_num &= 0x0FFFFFFF
                item = Actor(f"tiles/tile_{tile_num:04d}")
                if flipped_d:
                    item.flip_d = True
                if flipped_h:
                    item.flip_x = True
                if flipped_v:
                    item.flip_y = True
                if rotated_hex:
                    pass
                item.topleft = (tile_size * col, tile_size * row)
                items.append(item)

    return items


class SpriteSheet(object):
    def __init__(self, filename):
        
        key = filename.replace('\\', '/').lstrip('./')
        if key.startswith('images/'):
            key = key[len('images/'):]
        if key.lower().endswith('.png'):
            key = key[:-4]
        self.sheet = loaders.images.load(key)

    def image_at(self, rectangle, color_key=None):
        x, y, w, h = rectangle
        return self.sheet.subsurface((x, y, w, h))

    def images_at(self, rects, color_key=None):
        return [self.image_at(rect, color_key) for rect in rects]

    def load_strip(self, rect, image_count, color_key=None):
        tups = [(rect[0] + rect[2] * x, rect[1], rect[2], rect[3]) for x in range(image_count)]
        return self.images_at(tups, color_key)


class Sprite(object):
    def __init__(self, filename, rect, count, color_key=None, frames=1, left_rect=None):
        self.filename = filename
        ss = SpriteSheet(f"./images/sprites/{filename}")
        self.images = ss.load_strip(rect, count, color_key)
        self.images_left = None
        use_explicit_left = left_rect is not None and tuple(left_rect) != tuple(rect)
        if use_explicit_left:
            try:
                self.images_left = ss.load_strip(left_rect, count, color_key)
            except Exception:
                self.images_left = None
        if self.images_left is None and isinstance(self.images, list) and len(self.images) > 0:
            try:
                self.images_left = [self._flip_h(img) for img in self.images]
            except Exception:
                self.images_left = None
        self.i = 0
        self.frames = frames
        self.frame_num = frames

    def next(self, use_left=False):
        current_images = self.images_left if (use_left and self.images_left) else self.images
        if self.frame_num == 0:
            self.i = (self.i + 1) % len(current_images)
            self.frame_num = self.frames
        else:
            self.frame_num -= 1
        return current_images[self.i]

    def _flip_h(self, surf):
        w, h = surf.get_size()
        dst = surf.copy()
        try:
            dst.fill((0, 0, 0, 0))
        except Exception:
            try:
                dst.fill((0, 0, 0))
                if hasattr(dst, 'set_colorkey'):
                    dst.set_colorkey((0, 0, 0))
            except Exception:
                pass
        for x in range(w):
            try:
                column = surf.subsurface((x, 0, 1, h))
                dst.blit(column, (w - 1 - x, 0))
            except Exception:
                step = 2
                for xx in range(0, w, step):
                    bw = min(step, w - xx)
                    block = surf.subsurface((xx, 0, bw, h))
                    dst.blit(block, (w - xx - bw, 0))
                break
        return dst


class Actor(Actor):
    def __init__(self, image, pos=POS_TOPLEFT, anchor=ANCHOR_CENTER, **kwargs):
        self._flip_x = False
        self._flip_y = False
        self._flip_d = False
        self._scale = 1
        self._mask = None
        self.fps = 5
        self.direction = 0
        super().__init__(image, pos, anchor, **kwargs)

    @property
    def images(self):
        return self._images

    @images.setter
    def images(self, images):
        self._images = images
        if len(self._images) != 0:
            self.image = self._images[0]

    def next_image(self):
        if self.image in self._images:
            current = self._images.index(self.image)
            if current == len(self._images) - 1:
                self.image = self._images[0]
            else:
                self.image = self._images[current + 1]
        else:
            self.image = self._images[0]

    # No animate method needed (tiles are static)

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, scale):
        self._scale = scale
        self._transform_surf()

    @property
    def flip_x(self):
        return self._flip_x

    @flip_x.setter
    def flip_x(self, flip_x):
        self._flip_x = flip_x
        self._transform_surf()

    @property
    def flip_y(self):
        return self._flip_y

    @flip_y.setter
    def flip_y(self, flip_y):
        self._flip_y = flip_y
        self._transform_surf()

    @property
    def flip_d(self):
        return self._flip_d

    @flip_d.setter
    def flip_d(self, flip_d):
        self._flip_d = flip_d
        self._transform_surf()

    @property
    def sprite(self):
        return self._sprite

    @sprite.setter
    def sprite(self, sprite):
        self._sprite = sprite

    @property
    def image(self):
        return self._image_name

    @image.setter
    def image(self, image):
        self._image_name = image
        self._orig_surf = self._surf = loaders.images.load(image)
        self._update_pos()
        self._transform_surf()

    def _transform_surf(self):
        self._surf = self._orig_surf
        p = self.pos
        self.width, self.height = self._surf.get_size()
        w, h = self._orig_surf.get_size()
        ax, ay = self._untransformed_anchor
        anchor = transform_anchor(ax, ay, w, h, 0)
        self._anchor = (anchor[0], anchor[1])
        self.pos = p
        self._mask = None

    def draw(self):
        game.screen.blit(self._surf, self.topleft)


class SpriteActor(Actor):
    def __init__(self, sprite, pos=POS_TOPLEFT, anchor=ANCHOR_CENTER, **kwargs):
        self._flip_x = False
        self._flip_y = False
        self._scale = 1
        self._mask = None
        self.fps = 5
        self.direction = 0
        self.sprite = sprite
        # Pass image resource key without extension to PgZero loader
        base_name = sprite.filename[:-4] if sprite.filename.lower().endswith('.png') else sprite.filename
        super().__init__(f"sprites/{base_name}", pos, anchor, **kwargs)
        self._orig_surf = self.sprite.images[self.sprite.i]
        self._update_pos()
        self._transform_surf()

    @property
    def images(self):
        return self._images

    @images.setter
    def images(self, images):
        self._images = images
        if len(self._images) != 0:
            self.image = self._images[0]

    def next_image(self):
        if not hasattr(self, '_images') or not isinstance(self._images, list) or len(self._images) == 0:
            return
        try:
            current = self._images.index(self.image) if self.image in self._images else -1
        except Exception:
            current = -1
        if current == -1 or current == len(self._images) - 1:
            self.image = self._images[0]
        else:
            self.image = self._images[current + 1]

    # Animation handled per-frame in draw via sprite.frame_num

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, scale):
        self._scale = scale
        self._transform_surf()

    @property
    def flip_x(self):
        return self._flip_x

    @flip_x.setter
    def flip_x(self, flip_x):
        self._flip_x = flip_x
        self._transform_surf()

    @property
    def flip_y(self):
        return self._flip_y

    @flip_y.setter
    def flip_y(self, flip_y):
        self._flip_y = flip_y
        self._transform_surf()

    @property
    def sprite(self):
        return self._sprite

    @sprite.setter
    def sprite(self, sprite):
        self._sprite = sprite

    @property
    def image(self):
        return self._image_name

    @image.setter
    def image(self, image):
        self._image_name = image
        self._orig_surf = self._surf = loaders.images.load(image)
        self._update_pos()
        self._transform_surf()

    def _transform_surf(self):
        self._surf = self._orig_surf
        p = self.pos
        self.width, self.height = self._surf.get_size()
        w, h = self._orig_surf.get_size()
        ax, ay = self._untransformed_anchor
        anchor = transform_anchor(ax, ay, w, h, 0)
        self._anchor = (anchor[0], anchor[1])
        self.pos = p
        self._mask = None

    def draw(self):
        if self.sprite:
            # Choose frames based on flip_x; if no images_left, mirror at draw time
            using_left_list = self.flip_x and bool(self.sprite.images_left)
            base_images = self.sprite.images_left if using_left_list else self.sprite.images
            if self.sprite.frame_num == 0:
                self.sprite.i = (self.sprite.i + 1) % len(base_images)
                self.sprite.frame_num = self.sprite.frames
            else:
                self.sprite.frame_num -= 1
            frame = base_images[self.sprite.i]
            if self.flip_x and not using_left_list:
                # Dynamically mirror the frame if no left-facing strip exists
                try:
                    frame = self.sprite._flip_h(frame)
                except Exception:
                    pass
            self._orig_surf = self._surf = frame
            self._update_pos()
            self._transform_surf()
            game.screen.blit(self._surf, self.topleft)
        else:
            game.screen.blit(self._surf, self.topleft)