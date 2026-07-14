import pygame
import sys
import random
import math

# --- 初始化 ---
pygame.init()
pygame.mixer.init()

# --- 常量 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 150, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
PURPLE = (200, 50, 255)
DARK_GRAY = (40, 40, 40)
GRAY = (100, 100, 100)

# 玩家
PLAYER_SPEED = 6
PLAYER_COOLDOWN = 15

# 子弹
BULLET_SPEED = 12
ENEMY_BULLET_SPEED = 5

# 屏幕
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Empero AI - Qwythos: Space Shooter")
clock = pygame.time.Clock()
font_small = pygame.font.Font(None, 28)
font_medium = pygame.font.Font(None, 36)
font_large = pygame.font.Font(None, 48)

# --- 星空背景 ---
class StarField:
    def __init__(self):
        self.stars = []
        for _ in range(150):
            layer = random.randint(0, 2)
            if layer == 0:
                speed = 0.5
                size = 1
                color = (150, 150, 150)
            elif layer == 1:
                speed = 1.5
                size = 2
                color = (200, 200, 200)
            else:
                speed = 3.0
                size = 3
                color = (255, 255, 255)
            self.stars.append({
                "x": random.randint(0, SCREEN_WIDTH),
                "y": random.randint(0, SCREEN_HEIGHT),
                "speed": speed,
                "size": size,
                "color": color
            })
    
    def update(self):
        for star in self.stars:
            star["y"] += star["speed"]
            if star["y"] > SCREEN_HEIGHT:
                star["y"] = 0
                star["x"] = random.randint(0, SCREEN_WIDTH)
    
    def draw(self, surface):
        for star in self.stars:
            # 闪烁效果
            brightness = 100 + random.randint(-30, 30)
            c = star["color"]
            color = (
                min(255, max(0, c[0] + brightness - 150)),
                min(255, max(0, c[1] + brightness - 150)),
                min(255, max(0, c[2] + brightness - 150))
            )
            pygame.draw.circle(surface, color, (int(star["x"]), int(star["y"])), star["size"])

# --- 粒子特效 ---
class Particle:
    def __init__(self, x, y, color, lifetime=30):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = random.randint(2, 6)
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        self.vx *= 0.98
        self.vy *= 0.98
        return self.lifetime > 0
    
    def draw(self, surface):
        alpha = self.lifetime / self.max_lifetime
        size = int(self.size * alpha)
        if size > 0:
            color = tuple(int(c * alpha) for c in self.color)
            pygame.draw.circle(surface, color, (int(self.x), int(self.y)), size)

class ParticleSystem:
    def __init__(self):
        self.particles = []
    
    def emit(self, x, y, count, color, lifetime=30):
        for _ in range(count):
            self.particles.append(Particle(x, y, color, lifetime))
    
    def update(self):
        self.particles = [p for p in self.particles if p.update()]
    
    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

# --- 玩家飞机 ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((50, 50), pygame.SRCALPHA)
        self._draw_ship()
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 10
        self.speed_x = 0
        self.speed_y = 0
        self.shield_active = False
        self.shield_timer = 0
        self.rapid_fire = False
        self.rapid_fire_timer = 0
        self.spread_shot = False
        self.spread_timer = 0
        self.cooldown = 0
        self.invincible = 0
    
    def _draw_ship(self):
        # 机身
        pygame.draw.polygon(self.image, BLUE, [
            (25, 0),   # 机头
            (10, 40),  # 左翼根
            (0, 35),   # 左翼尖
            (10, 30),  # 左翼内
            (15, 45),  # 左下
            (25, 38),  # 中下
            (35, 45),  # 右下
            (40, 30),  # 右翼内
            (50, 35),  # 右翼尖
            (40, 40),  # 右翼根
        ])
        # 驾驶舱
        pygame.draw.ellipse(self.image, CYAN, (18, 12, 14, 16))
        # 引擎火焰
        pygame.draw.polygon(self.image, ORANGE, [(20, 45), (25, 52), (30, 45)])
        pygame.draw.polygon(self.image, YELLOW, [(22, 44), (25, 49), (28, 44)])
    
    def update(self):
        self.speed_x = 0
        self.speed_y = 0
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.speed_x = -PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            self.speed_x = PLAYER_SPEED
        if keys[pygame.K_UP]:
            self.speed_y = -PLAYER_SPEED
        if keys[pygame.K_DOWN]:
            self.speed_y = PLAYER_SPEED
        
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y
        
        # 边界检查
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT
        
        # 冷却
        if self.cooldown > 0:
            self.cooldown -= 1
        
        # 道具时限
        if self.shield_active:
            self.shield_timer -= 1
            if self.shield_timer <= 0:
                self.shield_active = False
        if self.rapid_fire:
            self.rapid_fire_timer -= 1
            if self.rapid_fire_timer <= 0:
                self.rapid_fire = False
        if self.spread_shot:
            self.spread_timer -= 1
            if self.spread_timer <= 0:
                self.spread_shot = False
        
        # 无敌时间
        if self.invincible > 0:
            self.invincible -= 1
    
    def shoot(self):
        cd = 5 if self.rapid_fire else PLAYER_COOLDOWN
        if self.cooldown <= 0:
            self.cooldown = cd
            bullets = []
            b = Bullet(self.rect.centerx, self.rect.top, -BULLET_SPEED, YELLOW)
            bullets.append(b)
            if self.spread_shot:
                bl = Bullet(self.rect.centerx - 12, self.rect.top + 5, -BULLET_SPEED, YELLOW)
                br = Bullet(self.rect.centerx + 12, self.rect.top + 5, -BULLET_SPEED, YELLOW)
                bl.vx = -1
                br.vx = 1
                bullets.extend([bl, br])
            return bullets
        return []
    
    def draw_shield(self, surface):
        if self.shield_active:
            pygame.draw.circle(surface, CYAN, self.rect.center, 35, 2)
            alpha = 30 + int(abs(math.sin(pygame.time.get_ticks() * 0.005)) * 30)
            s = pygame.Surface((74, 74), pygame.SRCALPHA)
            pygame.draw.circle(s, (0, 255, 255, alpha), (37, 37), 35, 3)
            surface.blit(s, (self.rect.centerx - 37, self.rect.centery - 37))

# --- 子弹 ---
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed, color=YELLOW, enemy_bullet=False):
        super().__init__()
        self.image = pygame.Surface((4, 14), pygame.SRCALPHA)
        color_gradient = [
            (color[0], color[1], color[2], 255),
            (color[0], color[1], color[2], 200),
            (color[0]//2, color[1]//2, color[2]//2, 100),
        ]
        for i in range(14):
            alpha = 255 - i * 15
            c = (color[0], color[1], color[2], max(0, alpha))
            pygame.draw.rect(self.image, c, (0, i, 4, 1))
        # 发光效果
        pygame.draw.rect(self.image, WHITE, (1, 0, 2, 6))
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = speed
        self.vx = 0
        self.enemy_bullet = enemy_bullet
    
    def update(self):
        self.rect.y += self.speed
        self.rect.x += self.vx
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

# --- 敌人类型 ---
class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_type="basic"):
        super().__init__()
        self.enemy_type = enemy_type
        
        if enemy_type == "basic":
            self.size = 30
            self.hp = 1
            self.score = 100
            self.speed_y = 2 + random.random() * 2
            self.color = RED
            self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, RED, [
                (self.size//2, self.size), (0, self.size//3), 
                (self.size//4, 0), (self.size*3//4, 0), 
                (self.size, self.size//3)
            ])
            pygame.draw.circle(self.image, YELLOW, (self.size//2, self.size//2), 5)
        
        elif enemy_type == "fast":
            self.size = 22
            self.hp = 1
            self.score = 150
            self.speed_y = 4 + random.random() * 3
            self.color = ORANGE
            self.wobble = random.uniform(-1.5, 1.5)
            self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, ORANGE, [
                (self.size//2, self.size), (0, self.size//2),
                (self.size//4, 0), (self.size*3//4, 0), (self.size, self.size//2)
            ])
        
        elif enemy_type == "tank":
            self.size = 48
            self.hp = 3
            self.score = 300
            self.speed_y = 1 + random.random()
            self.color = PURPLE
            self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, PURPLE, [
                (self.size//2, self.size), (0, self.size//2),
                (self.size//3, 0), (self.size*2//3, 0), (self.size, self.size//2)
            ])
            pygame.draw.rect(self.image, DARK_GRAY, (self.size//3, self.size//4, self.size//3, self.size//2))
            pygame.draw.circle(self.image, RED, (self.size//2, self.size//2), 6)
        
        elif enemy_type == "shooter":
            self.size = 34
            self.hp = 2
            self.score = 250
            self.speed_y = 1.5 + random.random()
            self.color = GREEN
            self.shoot_timer = random.randint(30, 90)
            self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, GREEN, [
                (self.size//2, 0), (0, self.size), 
                (self.size//3, self.size*2//3), (self.size*2//3, self.size*2//3),
                (self.size, self.size)
            ])
            pygame.draw.rect(self.image, YELLOW, (self.size//2-2, self.size-8, 4, 8))
        
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.size)
        self.rect.y = -self.size
    
    def update(self):
        self.rect.y += self.speed_y
        if self.enemy_type == "fast":
            self.rect.x += self.wobble
            self.wobble += random.uniform(-0.3, 0.3)
            self.wobble = max(-3, min(3, self.wobble))
        
        if self.enemy_type == "shooter":
            self.shoot_timer -= 1
        
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

# --- 道具 ---
class PowerUp(pygame.sprite.Sprite):
    TYPES = {
        "shield": ("S", CYAN),
        "rapid": ("R", YELLOW),
        "spread": ("W", ORANGE),
        "heal": ("H", GREEN),
    }
    
    def __init__(self, x, y):
        super().__init__()
        self.power_type = random.choice(list(self.TYPES.keys()))
        label, color = self.TYPES[self.power_type]
        self.image = pygame.Surface((28, 28), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (14, 14), 14)
        pygame.draw.circle(self.image, WHITE, (14, 14), 14, 2)
        text = font_small.render(label, True, BLACK)
        self.image.blit(text, (14 - text.get_width()//2, 14 - text.get_height()//2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 2
        self.bob_offset = random.random() * math.pi * 2
    
    def update(self):
        self.rect.y += self.speed
        self.bob_offset += 0.1
        self.rect.x += math.sin(self.bob_offset) * 0.5
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

# --- 主游戏 ---
def main():
    running = True
    game_over = False
    
    # 游戏状态
    score = 0
    level = 1
    lives = 3
    
    starfield = StarField()
    particles = ParticleSystem()
    
    player = Player()
    all_sprites = pygame.sprite.Group(player)
    bullets = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    enemy_bullets = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    
    # 敌人生成计时器
    spawn_timer = 0
    timer = pygame.time.get_ticks()
    level_kills = 0
    
    # 屏幕震动
    shake_timer = 0
    shake_intensity = 0
    
    # 解决持续射击的声音问题 - 使用音效池
    try:
        shoot_sound = pygame.mixer.Sound(pygame.mixer.Sound(buffer=bytes(40)))
        shoot_sound.set_volume(0.1)
        explosion_sound = pygame.mixer.Sound(pygame.mixer.Sound(buffer=bytes(80)))
        explosion_sound.set_volume(0.2)
    except:
        shoot_sound = None
        explosion_sound = None
    
    while running:
        dt = clock.get_time() / 1000.0
        
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game_over:
                    # 重置
                    game_over = False
                    score = 0
                    level = 1
                    lives = 3
                    level_kills = 0
                    all_sprites.empty()
                    all_sprites.add(player)
                    bullets.empty()
                    enemies.empty()
                    enemy_bullets.empty()
                    powerups.empty()
                    player = Player()
                    all_sprites.add(player)
                    timer = pygame.time.get_ticks()
        
        # 更新
        if not game_over:
            # 手把子弹
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                new_bullets = player.shoot()
                for b in new_bullets:
                    all_sprites.add(b)
                    bullets.add(b)
            
            all_sprites.update()
            
            # 敌人移动 + 射击者开火
            for enemy in enemies:
                if enemy.enemy_type == "shooter" and enemy.shoot_timer <= 0:
                    enemy.shoot_timer = random.randint(40, 100)
                    eb = Bullet(enemy.rect.centerx, enemy.rect.bottom, ENEMY_BULLET_SPEED, RED, True)
                    all_sprites.add(eb)
                    enemy_bullets.add(eb)
            
            # 敌人生成
            spawn_timer = pygame.time.get_ticks() - timer
            spawn_rate = max(400, 3000 - level * 200)
            if spawn_timer >= spawn_rate:
                # 根据等级选择敌人类型
                roll = random.random()
                if level >= 3 and roll < 0.15:
                    enemy = Enemy("tank")
                elif level >= 2 and roll < 0.35:
                    enemy = Enemy("shooter")
                elif level >= 1 and roll < 0.55:
                    enemy = Enemy("fast")
                else:
                    enemy = Enemy("basic")
                all_sprites.add(enemy)
                enemies.add(enemy)
                spawn_timer = 0
                timer = pygame.time.get_ticks()
            
            # 玩家子弹命中敌人
            hits = pygame.sprite.groupcollide(enemies, bullets, False, True)
            for enemy, bullet_list in hits.items():
                enemy.hp -= len(bullet_list)
                particles.emit(enemy.rect.centerx, enemy.rect.centery, 8, WHITE, 15)
                if enemy.hp <= 0:
                    enemy.kill()
                    score += enemy.score
                    level_kills += 1
                    particles.emit(enemy.rect.centerx, enemy.rect.centery, 25, enemy.color, 35)
                    shake_timer = 8
                    shake_intensity = 3
                    # 掉落道具概率
                    if random.random() < 0.12:
                        pu = PowerUp(enemy.rect.centerx, enemy.rect.centery)
                        all_sprites.add(pu)
                        powerups.add(pu)
            
            # 敌人子弹命中玩家
            if player.invincible <= 0:
                hit_by_bullet = pygame.sprite.spritecollideany(player, enemy_bullets)
                hit_by_enemy = pygame.sprite.spritecollideany(player, enemies)
                
                if hit_by_bullet or hit_by_enemy:
                    if hit_by_bullet:
                        hit_by_bullet.kill()
                    if hit_by_enemy and not player.shield_active:
                        hit_by_enemy.kill()
                    
                    if player.shield_active:
                        player.shield_active = False
                        player.shield_timer = 0
                        particles.emit(player.rect.centerx, player.rect.centery, 30, CYAN, 25)
                    else:
                        lives -= 1
                        particles.emit(player.rect.centerx, player.rect.centery, 40, BLUE, 40)
                        shake_timer = 15
                        shake_intensity = 8
                        if lives <= 0:
                            game_over = True
                            particles.emit(player.rect.centerx, player.rect.centery, 60, ORANGE, 50)
                        else:
                            player.invincible = 90  # 1.5秒无敌
            
            # 道具碰撞
            pu_hits = pygame.sprite.spritecollide(player, powerups, True)
            for pu in pu_hits:
                if pu.power_type == "shield":
                    player.shield_active = True
                    player.shield_timer = 480  # 8秒
                elif pu.power_type == "rapid":
                    player.rapid_fire = True
                    player.rapid_fire_timer = 360
                elif pu.power_type == "spread":
                    player.spread_shot = True
                    player.spread_timer = 360
                elif pu.power_type == "heal":
                    lives = min(5, lives + 1)
                particles.emit(pu.rect.centerx, pu.rect.centery, 15, WHITE, 20)
            
            # 关卡升级
            if level_kills >= level * 8:
                level += 1
                level_kills = 0
                particles.emit(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, 80, YELLOW, 60)
            
            particles.update()
            
            # 屏幕震动衰减
            if shake_timer > 0:
                shake_timer -= 1
        
        # 星空更新
        starfield.update()
        
        # 绘制
        shake_x = random.randint(-shake_intensity, shake_intensity) if shake_timer > 0 else 0
        shake_y = random.randint(-shake_intensity, shake_intensity) if shake_timer > 0 else 0
        
        screen.fill(BLACK)
        starfield.draw(screen)
        
        # 应用震动偏移
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        surf.fill(BLACK)
        all_sprites.draw(surf)
        particles.draw(surf)
        # 绘制护盾
        player.draw_shield(surf)
        
        screen.blit(surf, (shake_x, shake_y))
        
        # UI
        score_text = font_small.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        
        level_text = font_small.render(f"Level: {level}", True, YELLOW)
        screen.blit(level_text, (10, 40))
        
        # 生命显示
        for i in range(lives):
            heart_x = SCREEN_WIDTH - 40 - i * 35
            pygame.draw.polygon(screen, RED, [
                (heart_x + 15, 22),  # 顶部
                (heart_x, 10),       # 左上
                (heart_x + 5, 5),    # 左中
                (heart_x + 15, 12),  # 中心
                (heart_x + 25, 5),   # 右中
                (heart_x + 30, 10),  # 右上
            ])
        
        # 道具状态
        status_y = SCREEN_HEIGHT - 30
        if player.shield_active:
            txt = font_small.render(f"Shield: {player.shield_timer//60}s", True, CYAN)
            screen.blit(txt, (10, status_y))
        if player.rapid_fire:
            txt = font_small.render(f"Rapid: {player.rapid_fire_timer//60}s", True, YELLOW)
            screen.blit(txt, (150, status_y))
        if player.spread_shot:
            txt = font_small.render(f"Spread: {player.spread_timer//60}s", True, ORANGE)
            screen.blit(txt, (280, status_y))
        
        if game_over:
            # 半透明遮罩
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            over_text = font_large.render("GAME OVER", True, RED)
            screen.blit(over_text, (SCREEN_WIDTH//2 - over_text.get_width()//2, SCREEN_HEIGHT//2 - 60))
            
            final_score = font_medium.render(f"Final Score: {score}  Level: {level}", True, WHITE)
            screen.blit(final_score, (SCREEN_WIDTH//2 - final_score.get_width()//2, SCREEN_HEIGHT//2))
            
            restart_text = font_medium.render("Press 'R' to Restart", True, YELLOW)
            screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 50))
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
