import pygame
import sys
import random
import math

# --- 初始化 Pygame ---
pygame.init()

# --- 常量定义 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 150, 255)
YELLOW = (255, 255, 0)

# 玩家属性
PLAYER_SIZE = 40
PLAYER_SPEED = 5
PLAYER_COLOR = GREEN

# 子弹属性
BULLET_SIZE = 6
BULLET_SPEED = 10
BULLET_COLOR = YELLOW
BULLET_COOLDOWN = 20  # 冷却帧数

# 敌机属性
ENEMY_SIZE = 30
ENEMY_SPEED = 3
ENEMY_COLOR = RED
ENEMY_SPAWN_RATE = 3000  # 每 N 毫秒生成一个敌机（1秒一个）

# --- 屏幕设置 ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Empero AI - Qwythos: Space Shooter")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

# --- 类定义 ---

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE))
        self.image.fill(PLAYER_COLOR)
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 10
        self.speed_x = 0

    def update(self):
        # 左右移动
        self.speed_x = 0
        if pygame.key.get_pressed()[pygame.K_LEFT]:
            self.speed_x = -PLAYER_SPEED
        if pygame.key.get_pressed()[pygame.K_RIGHT]:
            self.speed_x = PLAYER_SPEED
        
        self.rect.x += self.speed_x
        
        # 边界检查
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

class Bullet(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((BULLET_SIZE, BULLET_SIZE * 2))
        self.image.fill(BULLET_COLOR)
        self.rect = self.image.get_rect()
        self.rect.centerx = 0  # 初始位置，稍后由玩家设置
        self.rect.bottom = 0
    
    def update(self):
        self.rect.y -= BULLET_SPEED
        if self.rect.bottom < 0:
            self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((ENEMY_SIZE, ENEMY_SIZE))
        self.image.fill(ENEMY_COLOR)
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - ENEMY_SIZE)
        self.rect.y = -ENEMY_SIZE  # 从屏幕上方出现
        self.speed = ENEMY_SPEED + random.random() * 2  # 随机速度
    
    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

# --- 游戏逻辑 ---

def main():
    running = True
    game_over = False
    score = 0
    player = Player()
    all_sprites = pygame.sprite.Group(player)
    bullets = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    
    # 敌人生成计时器
    spawn_timer = 0
    timer = pygame.time.get_ticks()

    while running:
        # 1. 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_over:
                    # 发射子弹
                    bullet = Bullet()
                    bullet.rect.centerx = player.rect.centerx
                    bullet.rect.bottom = player.rect.top
                    all_sprites.add(bullet)
                    bullets.add(bullet)
                
                if event.key == pygame.K_r and game_over:
                    # 重置游戏
                    game_over = False
                    score = 0
                    all_sprites.empty()
                    all_sprites.add(player)
                    bullets.empty()
                    enemies.empty()
                    timer = pygame.time.get_ticks()

        # 2. 更新逻辑
        if not game_over:
            all_sprites.update()
            
            # 敌人生成
            spawn_timer = pygame.time.get_ticks() - timer
            if spawn_timer >= ENEMY_SPAWN_RATE:
                enemy = Enemy()
                all_sprites.add(enemy)
                enemies.add(enemy)
                spawn_timer = 0
                timer = pygame.time.get_ticks()

            # 子弹击中敌机
            hits = pygame.sprite.groupcollide(enemies, bullets, True, True)
            for enemy, bullet_list in hits.items():
                score += 100
                print(f"Enemy hit! Score: {score}")

            # 敌机击中玩家
            if pygame.sprite.spritecollideany(player, enemies):
                game_over = True

        # 3. 绘制
        screen.fill(BLACK)
        
        # 绘制星空背景 (简单的效果)
        # 这里为了代码简洁省略了复杂的星空生成，保持黑色背景
        all_sprites.draw(screen)
        
        # 绘制 UI
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        
        if game_over:
            over_text = font.render("GAME OVER - Press 'R' to Restart", True, RED)
            screen.blit(over_text, (SCREEN_WIDTH // 2 - over_text.get_width() // 2, SCREEN_HEIGHT // 2))
            # 简单的闪烁效果
            blink = int(pygame.time.get_ticks() / 500) % 2
            if blink:
                screen.fill(BLACK) # 闪黑屏

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()