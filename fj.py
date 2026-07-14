import math
import random
import sys

import pygame


pygame.init()

WIDTH, HEIGHT = 900, 700
FPS = 60
TITLE = "NEBULA STRIKE"

INK = (224, 240, 255)
MUTED = (112, 142, 169)
CYAN = (67, 226, 255)
BLUE = (57, 112, 255)
GREEN = (82, 238, 164)
YELLOW = (255, 216, 92)
ORANGE = (255, 135, 61)
RED = (255, 73, 103)
DEEP = (5, 9, 22)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()


def font(size, bold=False):
    return pygame.font.SysFont("segoeui", size, bold=bold)


FONT_SM = font(18)
FONT_MD = font(26, True)
FONT_LG = font(54, True)
FONT_XL = font(78, True)


def clamp(value, low, high):
    return max(low, min(high, value))


def draw_text(surface, text, typeface, color, pos, anchor="topleft"):
    image = typeface.render(text, True, color)
    rect = image.get_rect()
    setattr(rect, anchor, pos)
    surface.blit(image, rect)
    return rect


class Starfield:
    def __init__(self):
        self.stars = []
        for _ in range(150):
            layer = random.choice((1, 1, 1, 2, 2, 3))
            self.stars.append([random.randrange(WIDTH), random.randrange(HEIGHT), layer])

    def update(self, dt, boost=1.0):
        for star in self.stars:
            star[1] += (18 + star[2] * 28) * dt * boost
            if star[1] > HEIGHT:
                star[0] = random.randrange(WIDTH)
                star[1] = random.uniform(-30, 0)

    def draw(self, surface):
        surface.fill(DEEP)
        pygame.draw.circle(surface, (10, 30, 55), (90, 170), 190)
        pygame.draw.circle(surface, (19, 17, 54), (825, 530), 260)
        for x, y, layer in self.stars:
            colors = ((74, 99, 125), (131, 167, 194), (219, 240, 255))
            pygame.draw.circle(surface, colors[layer - 1], (int(x), int(y)), max(1, layer - 1))
            if layer == 3:
                pygame.draw.line(surface, (77, 130, 164), (x, y - 5), (x, y + 5), 1)


class Particle:
    def __init__(self, pos, color, speed=180, life=0.55, size=4, direction=None):
        angle = random.uniform(0, math.tau) if direction is None else direction + random.uniform(-0.35, 0.35)
        force = random.uniform(speed * 0.35, speed)
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * force
        self.color = color
        self.life = self.max_life = random.uniform(life * 0.55, life)
        self.size = random.uniform(size * 0.5, size)

    def update(self, dt):
        self.life -= dt
        self.pos += self.velocity * dt
        self.velocity *= 0.96
        return self.life > 0

    def draw(self, surface, offset):
        ratio = clamp(self.life / self.max_life, 0, 1)
        radius = max(1, int(self.size * ratio))
        color = tuple(int(channel * ratio) for channel in self.color)
        pygame.draw.circle(surface, color, self.pos + offset, radius)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, velocity, friendly=True, damage=1):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(velocity)
        self.friendly = friendly
        self.damage = damage
        w, h = (7, 23) if friendly else (10, 18)
        self.image = pygame.Surface((w + 8, h + 8), pygame.SRCALPHA)
        glow = CYAN if friendly else RED
        pygame.draw.rect(self.image, (*glow, 55), (1, 1, w + 6, h + 6), border_radius=5)
        pygame.draw.rect(self.image, glow, (5, 4, w - 2, h), border_radius=3)
        pygame.draw.rect(self.image, (245, 255, 255), (7, 5, max(2, w - 6), h - 5), border_radius=2)
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt):
        self.pos += self.velocity * dt
        self.rect.center = self.pos
        if self.rect.bottom < -30 or self.rect.top > HEIGHT + 30 or self.rect.right < -30 or self.rect.left > WIDTH + 30:
            self.kill()


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((58, 76), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, BLUE, [(29, 2), (49, 57), (37, 52), (29, 72), (21, 52), (9, 57)])
        pygame.draw.polygon(self.image, CYAN, [(29, 2), (36, 51), (29, 60), (22, 51)])
        pygame.draw.polygon(self.image, (202, 244, 255), [(29, 12), (34, 37), (29, 43), (24, 37)])
        pygame.draw.polygon(self.image, (28, 58, 130), [(9, 57), (3, 65), (21, 62), (21, 52)])
        pygame.draw.polygon(self.image, (28, 58, 130), [(49, 57), (55, 65), (37, 62), (37, 52)])
        self.rect = self.image.get_rect(midbottom=(WIDTH // 2, HEIGHT - 42))
        self.pos = pygame.Vector2(self.rect.center)
        self.speed = 410
        self.health = 100
        self.invulnerable = 0
        self.fire_timer = 0
        self.rapid_timer = 0
        self.shield_timer = 0

    def update(self, dt):
        keys = pygame.key.get_pressed()
        move = pygame.Vector2(keys[pygame.K_RIGHT] - keys[pygame.K_LEFT], keys[pygame.K_DOWN] - keys[pygame.K_UP])
        move += pygame.Vector2(keys[pygame.K_d] - keys[pygame.K_a], keys[pygame.K_s] - keys[pygame.K_w])
        if move.length_squared():
            move = move.normalize()
        self.pos += move * self.speed * dt
        self.pos.x = clamp(self.pos.x, 34, WIDTH - 34)
        self.pos.y = clamp(self.pos.y, HEIGHT * 0.48, HEIGHT - 40)
        self.rect.center = self.pos
        self.invulnerable = max(0, self.invulnerable - dt)
        self.fire_timer = max(0, self.fire_timer - dt)
        self.rapid_timer = max(0, self.rapid_timer - dt)
        self.shield_timer = max(0, self.shield_timer - dt)

    def shoot(self):
        if self.fire_timer > 0:
            return []
        self.fire_timer = 0.105 if self.rapid_timer else 0.21
        if self.rapid_timer:
            return [Bullet((self.pos.x - 15, self.rect.top + 10), (-45, -680)),
                    Bullet((self.pos.x + 15, self.rect.top + 10), (45, -680))]
        return [Bullet((self.pos.x, self.rect.top), (0, -650))]

    def draw_effects(self, surface):
        flame = random.randint(11, 22)
        pygame.draw.polygon(surface, ORANGE, [(self.pos.x - 7, self.rect.bottom - 7),
                                              (self.pos.x, self.rect.bottom + flame),
                                              (self.pos.x + 7, self.rect.bottom - 7)])
        pygame.draw.polygon(surface, YELLOW, [(self.pos.x - 3, self.rect.bottom - 5),
                                              (self.pos.x, self.rect.bottom + flame - 7),
                                              (self.pos.x + 3, self.rect.bottom - 5)])
        if self.shield_timer:
            pulse = 4 + int(math.sin(pygame.time.get_ticks() * 0.009) * 2)
            pygame.draw.circle(surface, CYAN, self.rect.center, 42 + pulse, 2)


class Enemy(pygame.sprite.Sprite):
    TYPES = {
        "scout": (34, 1, 135, 100, RED),
        "striker": (46, 2, 95, 240, ORANGE),
        "tank": (62, 5, 55, 500, (186, 82, 255)),
    }

    def __init__(self, kind, level):
        super().__init__()
        size, hp, speed, value, color = self.TYPES[kind]
        self.kind, self.hp, self.max_hp, self.value = kind, hp, hp, value
        self.speed = speed + level * 5
        self.pos = pygame.Vector2(random.randint(size, WIDTH - size), -size)
        self.phase = random.uniform(0, math.tau)
        self.age = 0
        self.shoot_timer = random.uniform(0.8, 2.2)
        self.image = pygame.Surface((size + 12, size + 14), pygame.SRCALPHA)
        w, h = self.image.get_size()
        pygame.draw.polygon(self.image, color, [(w // 2, h - 3), (4, 14), (w // 2, 4), (w - 4, 14)])
        pygame.draw.polygon(self.image, (48, 35, 72), [(w // 2, h - 10), (13, 16), (w // 2, 12), (w - 13, 16)])
        pygame.draw.circle(self.image, (255, 221, 225), (w // 2, 16), max(3, size // 10))
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt):
        self.age += dt
        drift = math.sin(self.age * (2.4 if self.kind == "scout" else 1.3) + self.phase)
        self.pos.x += drift * (85 if self.kind == "scout" else 42) * dt
        self.pos.y += self.speed * dt
        self.rect.center = self.pos
        self.shoot_timer -= dt

    def try_shoot(self):
        if self.kind == "scout" or self.shoot_timer > 0 or self.pos.y < 40:
            return None
        self.shoot_timer = random.uniform(1.5, 2.8)
        return Bullet((self.pos.x, self.rect.bottom), (0, 280), friendly=False)


class PowerUp(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.kind = random.choice(("rapid", "shield", "heal"))
        color = {"rapid": YELLOW, "shield": CYAN, "heal": GREEN}[self.kind]
        self.image = pygame.Surface((34, 34), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (*color, 45), (17, 17), 16)
        pygame.draw.circle(self.image, color, (17, 17), 12, 2)
        symbol = {"rapid": "R", "shield": "S", "heal": "+"}[self.kind]
        label = font(17, True).render(symbol, True, color)
        self.image.blit(label, label.get_rect(center=(17, 16)))
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(pos)

    def update(self, dt):
        self.pos.y += 120 * dt
        self.pos.x += math.sin(pygame.time.get_ticks() * 0.004) * 35 * dt
        self.rect.center = self.pos
        if self.rect.top > HEIGHT:
            self.kill()


class Game:
    def __init__(self):
        self.starfield = Starfield()
        self.best = 0
        self.state = "menu"
        self.reset()

    def reset(self):
        self.player = Player()
        self.enemies = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.particles = []
        self.score = 0
        self.combo = 1
        self.combo_timer = 0
        self.elapsed = 0
        self.spawn_timer = 0.6
        self.shake = 0
        self.level_flash = 0
        self.last_level = 1

    @property
    def level(self):
        return 1 + int(self.elapsed // 22)

    def start(self):
        self.reset()
        self.state = "playing"

    def burst(self, pos, color, count=16, speed=220):
        for _ in range(count):
            self.particles.append(Particle(pos, color, speed=speed))

    def damage_player(self, amount):
        if self.player.invulnerable > 0:
            return
        if self.player.shield_timer > 0:
            self.player.shield_timer = max(0, self.player.shield_timer - 2.5)
            self.burst(self.player.pos, CYAN, 10)
            self.shake = 5
            return
        self.player.health -= amount
        self.player.invulnerable = 0.8
        self.combo = 1
        self.shake = 12
        self.burst(self.player.pos, RED, 18, 280)
        if self.player.health <= 0:
            self.best = max(self.best, self.score)
            self.burst(self.player.pos, CYAN, 48, 420)
            self.state = "gameover"

    def spawn_enemy(self):
        roll = random.random()
        if self.level >= 3 and roll < 0.14:
            kind = "tank"
        elif self.level >= 2 and roll < 0.43:
            kind = "striker"
        else:
            kind = "scout"
        self.enemies.add(Enemy(kind, self.level))

    def update(self, dt):
        self.starfield.update(dt, 1.4 if self.state == "playing" else 0.45)
        self.particles = [p for p in self.particles if p.update(dt)]
        if self.state != "playing":
            return

        self.elapsed += dt
        self.combo_timer -= dt
        self.level_flash = max(0, self.level_flash - dt)
        if self.combo_timer <= 0:
            self.combo = 1
        if self.level != self.last_level:
            self.last_level = self.level
            self.level_flash = 2.0

        self.player.update(dt)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] or pygame.mouse.get_pressed()[0]:
            for bullet in self.player.shoot():
                self.player_bullets.add(bullet)
                self.particles.append(Particle(bullet.rect.center, CYAN, 55, 0.18, 3, math.pi / 2))

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_enemy()
            base = max(0.28, 0.84 - self.level * 0.055)
            self.spawn_timer = random.uniform(base * 0.7, base * 1.25)

        self.enemies.update(dt)
        self.player_bullets.update(dt)
        self.enemy_bullets.update(dt)
        self.powerups.update(dt)

        for enemy in self.enemies:
            shot = enemy.try_shoot()
            if shot:
                self.enemy_bullets.add(shot)
            if enemy.rect.top > HEIGHT:
                enemy.kill()
                self.damage_player(12)

        hits = pygame.sprite.groupcollide(self.enemies, self.player_bullets, False, True)
        for enemy, bullets in hits.items():
            enemy.hp -= sum(b.damage for b in bullets)
            self.burst(enemy.rect.center, ORANGE, 5, 110)
            if enemy.hp <= 0:
                enemy.kill()
                self.score += enemy.value * self.combo
                self.combo = min(8, self.combo + 1)
                self.combo_timer = 2.3
                self.shake = min(10, 3 + enemy.max_hp)
                color = Enemy.TYPES[enemy.kind][4]
                self.burst(enemy.rect.center, color, 14 + enemy.max_hp * 4, 230)
                if random.random() < 0.09:
                    self.powerups.add(PowerUp(enemy.rect.center))

        if pygame.sprite.spritecollide(self.player, self.enemies, True):
            self.damage_player(28)
        if pygame.sprite.spritecollide(self.player, self.enemy_bullets, True):
            self.damage_player(16)

        for power in pygame.sprite.spritecollide(self.player, self.powerups, True):
            if power.kind == "rapid":
                self.player.rapid_timer = 8
            elif power.kind == "shield":
                self.player.shield_timer = 9
            else:
                self.player.health = min(100, self.player.health + 30)
            self.burst(power.rect.center, GREEN, 18)

        self.shake = max(0, self.shake - 24 * dt)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE) and self.state in ("menu", "gameover"):
                self.start()
            elif event.key == pygame.K_ESCAPE:
                if self.state == "playing":
                    self.state = "paused"
                elif self.state == "paused":
                    self.state = "playing"
            elif event.key == pygame.K_p and self.state in ("playing", "paused"):
                self.state = "paused" if self.state == "playing" else "playing"
            elif event.key == pygame.K_r and self.state == "gameover":
                self.start()

    def draw_hud(self, surface):
        pygame.draw.rect(surface, (7, 16, 31), (20, 18, 256, 62), border_radius=6)
        pygame.draw.rect(surface, (31, 55, 75), (20, 18, 256, 62), 1, border_radius=6)
        draw_text(surface, "HULL", FONT_SM, MUTED, (34, 29))
        pygame.draw.rect(surface, (37, 48, 61), (92, 33, 164, 12), border_radius=6)
        health_width = int(164 * max(0, self.player.health) / 100)
        health_color = GREEN if self.player.health > 45 else (YELLOW if self.player.health > 22 else RED)
        pygame.draw.rect(surface, health_color, (92, 33, health_width, 12), border_radius=6)
        status = "SHIELD" if self.player.shield_timer else ("RAPID FIRE" if self.player.rapid_timer else "SYSTEMS NOMINAL")
        draw_text(surface, status, font(14, True), CYAN if status != "SYSTEMS NOMINAL" else MUTED, (34, 55))

        draw_text(surface, f"{self.score:07d}", FONT_MD, INK, (WIDTH - 24, 22), "topright")
        draw_text(surface, f"SECTOR {self.level:02d}", FONT_SM, MUTED, (WIDTH - 24, 54), "topright")
        if self.combo > 1:
            draw_text(surface, f"x{self.combo} COMBO", FONT_MD, YELLOW, (WIDTH // 2, 27), "midtop")

    def draw_overlay(self, surface, title, subtitle, accent=CYAN):
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((3, 7, 18, 178))
        surface.blit(veil, (0, 0))
        draw_text(surface, title, FONT_LG, accent, (WIDTH // 2, HEIGHT // 2 - 55), "center")
        draw_text(surface, subtitle, FONT_SM, INK, (WIDTH // 2, HEIGHT // 2 + 9), "center")

    def draw(self):
        self.starfield.draw(screen)
        offset = pygame.Vector2(random.uniform(-self.shake, self.shake), random.uniform(-self.shake, self.shake)) if self.shake else pygame.Vector2()

        if self.state != "menu":
            world = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            if self.state != "gameover" or self.player.health > 0:
                self.player.draw_effects(world)
                if not (self.player.invulnerable and int(self.player.invulnerable * 14) % 2):
                    world.blit(self.player.image, self.player.rect)
            self.enemies.draw(world)
            self.player_bullets.draw(world)
            self.enemy_bullets.draw(world)
            self.powerups.draw(world)
            for enemy in self.enemies:
                if enemy.max_hp > 1 and enemy.hp < enemy.max_hp:
                    width = enemy.rect.width - 10
                    pygame.draw.rect(world, (44, 37, 58), (enemy.rect.left + 5, enemy.rect.top - 7, width, 3))
                    pygame.draw.rect(world, RED, (enemy.rect.left + 5, enemy.rect.top - 7, width * enemy.hp / enemy.max_hp, 3))
            for particle in self.particles:
                particle.draw(world, (0, 0))
            screen.blit(world, offset)
            self.draw_hud(screen)

        if self.state == "menu":
            draw_text(screen, "NEBULA", FONT_XL, INK, (WIDTH // 2, 180), "center")
            draw_text(screen, "STRIKE", FONT_XL, CYAN, (WIDTH // 2, 256), "center")
            pygame.draw.line(screen, BLUE, (WIDTH // 2 - 170, 305), (WIDTH // 2 + 170, 305), 2)
            draw_text(screen, "ARROW KEYS / WASD TO MOVE", FONT_SM, MUTED, (WIDTH // 2, 358), "center")
            draw_text(screen, "HOLD SPACE OR MOUSE TO FIRE", FONT_SM, MUTED, (WIDTH // 2, 389), "center")
            if int(pygame.time.get_ticks() / 550) % 2:
                draw_text(screen, "PRESS ENTER TO LAUNCH", FONT_MD, YELLOW, (WIDTH // 2, 474), "center")
            draw_text(screen, "ESC / P  PAUSE", font(15), MUTED, (WIDTH // 2, HEIGHT - 46), "center")
        elif self.state == "paused":
            self.draw_overlay(screen, "PAUSED", "PRESS P OR ESC TO RESUME")
        elif self.state == "gameover":
            self.draw_overlay(screen, "MISSION FAILED", f"SCORE  {self.score:07d}     BEST  {self.best:07d}", RED)
            draw_text(screen, "PRESS R OR ENTER TO REDEPLOY", FONT_SM, YELLOW, (WIDTH // 2, HEIGHT // 2 + 58), "center")
        elif self.level_flash:
            alpha = int(255 * min(1, self.level_flash))
            label = FONT_LG.render(f"SECTOR {self.level:02d}", True, (*INK, alpha))
            label.set_alpha(alpha)
            screen.blit(label, label.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

        pygame.display.flip()


def main():
    game = Game()
    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000, 0.034)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                game.handle_event(event)
        game.update(dt)
        game.draw()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
