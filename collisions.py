_alpha_bbox_cache = {}


def _pixel_is_opaque(rgb_or_rgba):
    try:
        if len(rgb_or_rgba) == 4:
            return rgb_or_rgba[3] >= 192  # avoid hits on anti-aliased halos
        return tuple(rgb_or_rgba[:3]) != (0, 0, 0)
    except Exception:
        return True


def _collision_surface(obj):
    # Prefer the actual frame drawn (cached by our SpriteActor/Actor)
    surf = getattr(obj, "_surf", None)
    if surf is not None:
        return surf
    # Fallback: try reconstructing from sprite state if available
    try:
        if hasattr(obj, "sprite") and getattr(obj, "sprite", None):
            using_left_list = getattr(obj, "flip_x", False) and bool(obj.sprite.images_left)
            base_images = obj.sprite.images_left if using_left_list else obj.sprite.images
            if base_images:
                idx = getattr(obj.sprite, "i", 0) % len(base_images)
                frame = base_images[idx]
                if getattr(obj, "flip_x", False) and not using_left_list:
                    try:
                        frame = obj.sprite._flip_h(frame)
                    except Exception:
                        pass
                return frame
    except Exception:
        return None
    return None


def _inset_for(obj):
    try:
        if hasattr(obj, "sprite") and getattr(obj, "sprite", None):
            return (4, 3)
    except Exception:
        pass
    return (1, 1)


def _pixel_perfect_collide(a, b, inset_getter):
    # Quick AABB reject
    left = int(max(a.left, b.left))
    top = int(max(a.top, b.top))
    right = int(min(a.right, b.right))
    bottom = int(min(a.bottom, b.bottom))
    if left >= right or top >= bottom:
        return False

    try:
        sa = _collision_surface(a)
        sb = _collision_surface(b)
        if sa is None or sb is None:
            return a.colliderect(b)
        aw, ah = sa.get_size()
        bw, bh = sb.get_size()

        # Prefilter by alpha bounding boxes to avoid scanning transparent halos
        def alpha_bbox(surf):
            # Tiny cache keyed by (id, size) to avoid recomputation within a frame
            sw, sh = surf.get_size()
            key = (id(surf), sw, sh)
            cached = _alpha_bbox_cache.get(key)
            if cached is not None:
                return cached
            minx, miny, maxx, maxy = sw, sh, -1, -1
            for yy in range(sh):
                for xx in range(sw):
                    c = surf.get_at((xx, yy))
                    if _pixel_is_opaque(c):
                        if xx < minx:
                            minx = xx
                        if yy < miny:
                            miny = yy
                        if xx > maxx:
                            maxx = xx
                        if yy > maxy:
                            maxy = yy
            if maxx == -1:
                _alpha_bbox_cache[key] = None
                return None
            bbox = (minx, miny, maxx + 1, maxy + 1)
            _alpha_bbox_cache[key] = bbox
            return bbox

        bb_a = alpha_bbox(sa)
        bb_b = alpha_bbox(sb)
        if bb_a is None or bb_b is None:
            return False

        # Convert local alpha bboxes to world coords
        a_lx0, a_ly0, a_lx1, a_ly1 = bb_a
        b_lx0, b_ly0, b_lx1, b_ly1 = bb_b
        a_wx0, a_wy0, a_wx1, a_wy1 = a.left + a_lx0, a.top + a_ly0, a.left + a_lx1, a.top + a_ly1
        b_wx0, b_wy0, b_wx1, b_wy1 = b.left + b_lx0, b.top + b_ly0, b.left + b_lx1, b.top + b_ly1

        # Intersect refined bounds
        left = max(left, int(max(a_wx0, b_wx0)))
        top = max(top, int(max(a_wy0, b_wy0)))
        right = min(right, int(min(a_wx1, b_wx1)))
        bottom = min(bottom, int(min(a_wy1, b_wy1)))
        if left >= right or top >= bottom:
            return False

        aix, aiy = inset_getter(a)
        bix, biy = inset_getter(b)
        for y in range(top, bottom):
            ay = y - a.top
            by = y - b.top
            for x in range(left, right):
                ax = x - a.left
                bx = x - b.left
                if ax < aix or ay < aiy or ax >= aw - aix or ay >= ah - aiy:
                    continue
                if bx < bix or by < biy or bx >= bw - bix or by >= bh - biy:
                    continue
                iax = int(ax)
                iay = int(ay)
                ibx = int(bx)
                iby = int(by)
                if iax < 0 or iay < 0 or iax >= aw or iay >= ah:
                    continue
                if ibx < 0 or iby < 0 or ibx >= bw or iby >= bh:
                    continue
                ca = sa.get_at((iax, iay))
                cb = sb.get_at((ibx, iby))
                if _pixel_is_opaque(ca) and _pixel_is_opaque(cb):
                    return True
    except Exception:
        return a.colliderect(b)
    return False


def pixel_perfect_collide(a, b):
    # Default collide for enemies/obstacles (uses sprite-friendly insets)
    return _pixel_perfect_collide(a, b, _inset_for)


def platform_collide(a, b):
    # Stable collide for platform resolution (low/no inset)
    def small_inset(_):
        return (0, 0)
    return _pixel_perfect_collide(a, b, small_inset)


# Convenience helpers for groups
def first_hit_pixel(a, items):
    """Return the first item from items that collides with a using pixel-perfect check, else None."""
    for it in items:
        if pixel_perfect_collide(a, it):
            return it
    return None


def any_hit_pixel(a, items):
    """Return True if any item collides with a using pixel-perfect check."""
    return first_hit_pixel(a, items) is not None


def first_hit_platform(a, platforms):
    """Return the first platform that collides with a using platform_collide, else None."""
    for p in platforms:
        if platform_collide(a, p):
            return p
    return None


def first_hit_aabb(a, items):
    """Return the first AABB (colliderect) hit item, else None."""
    for it in items:
        if a.colliderect(it):
            return it
    return None
