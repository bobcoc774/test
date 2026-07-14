import pygame
import random
import math

# --- 初始化 ---
pygame.init()

# --- 常量 ---
CELL_SIZE = 20
GRID_WIDTH = 30
GRID_HEIGHT = 20
SCREEN_WIDTH = CELL_SIZE * GRID_WIDTH
SCREEN_HEIGHT = CELL_SIZE * GRID_HEIGHT

# 颜色
BLACK = (10, 10, 20)
DARK_GREEN = (0, 40, 0)
GRID_COLOR = (25, 25, 40)
WALL_COLOR = (60, 60, 100)
WHITE = (255, 255, 255)
RED = (255, 60, 60)
GOLD = (255, 215, 0)
GRAY = (150, 150, 150)

# 苹果颜色
APPLE_RED = (255, 50, 50)
APPLE_GREEN = (150, 255, 50)
APPLE_DARK = (180, 20, 20)
APPLE_LIGHT = (255, 130, 130)

# --- 粒子系统 ---
class Particle:
    def __init__(self, x, y, color, lifetime=20):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = random.randint(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        self.vx *= 0.95
        self.vy *= 0.95
        return self.lifetime > 0

    def draw(self, surface):
        alpha = self.lifetime / self.max_lifetime
        size = max(1, int(self.size * alpha))
        c = tuple(int(ch * alpha) for ch in self.color)
        pygame.draw.circle(surface, c, (int(self.x), int(self.y)), size)

class Particles:
    def __init__(self):
        self.items = []

    def emit(self, x, y, count, color, lifetime=20):
        for _ in range(count):
            self.items.append(Particle(x, y, color, lifetime))

    def update(self):
        self.items = [p for p in self.items if p.update()]

    def draw(self, surface):
        for p in self.items:
            p.draw(surface)

# --- 得分弹出 ---
class ScorePopup:
    def __init__(self, x, y, text, color=WHITE):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = 40
        self.max_life = 40
        self.font = pygame.font.SysFont("monospace", 22, bold=True)

    def update(self):
        self.y -= 1.2
        self.life -= 1
        return self.life > 0

    def draw(self, surface):
        alpha = self.life / self.max_life
        s = self.font.render(self.text, True, self.color)
        s.set_alpha(int(255 * alpha))
        surface.blit(s, (self.x - s.get_width() // 2, int(self.y)))

# --- 蛇 ---
class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        cx = GRID_WIDTH // 2
        cy = GRID_HEIGHT // 2
        self.body = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction = "RIGHT"
        self.next_direction = "RIGHT"
        self.grow_pending = 0  # 待增长格数
        self.alive = True

    def set_direction(self, d):
        opposite = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
        if d != opposite.get(self.direction, ""):
            self.next_direction = d

    def move(self):
        if not self.alive:
            return
        self.direction = self.next_direction
        hx, hy = self.body[0]
        if self.direction == "RIGHT":
            nh = (hx + 1, hy)
        elif self.direction == "LEFT":
            nh = (hx - 1, hy)
        elif self.direction == "UP":
            nh = (hx, hy - 1)
        elif self.direction == "DOWN":
            nh = (hx, hy + 1)
        else:
            nh = (hx, hy)

        self.body.insert(0, nh)
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.body.pop()

    def check_death(self):
        hx, hy = self.body[0]
        # 撞墙
        if hx < 0 or hx >= GRID_WIDTH or hy < 0 or hy >= GRID_HEIGHT:
            self.alive = False
            return True
        # 撞自身
        if self.body[0] in self.body[1:]:
            self.alive = False
            return True
        return False

    def grow(self, n=1):
        self.grow_pending += n

    def head_pixel(self):
        hx, hy = self.body[0]
        return (hx * CELL_SIZE + CELL_SIZE // 2, hy * CELL_SIZE + CELL_SIZE // 2)

# --- 苹果 ---
class Apple:
    def __init__(self):
        self.pos = (0, 0)
        self.special = False  # 金苹果，+3分

    def spawn(self, snake):
        while True:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            if (x, y) not in snake.body:
                self.pos = (x, y)
                self.special = random.random() < 0.15  # 15%概率金苹果
                break

    def pixel_center(self):
        return (self.pos[0] * CELL_SIZE + CELL_SIZE // 2,
                self.pos[1] * CELL_SIZE + CELL_SIZE // 2)

# --- 主游戏 ---
def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Snake - Qwythos by Empero AI")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("monospace", 28, bold=True)
    big_font = pygame.font.SysFont("monospace", 48, bold=True)
    small_font = pygame.font.SysFont("monospace", 18)

    snake = Snake()
    apple = Apple()
    apple.spawn(snake)
    particles = Particles()
    popups = []

    running = True
    game_over = False
    paused = False
    score = 0
    high_score = 0
    move_timer = 0
    base_move_interval = 8  # 基础移动间隔（帧）
    shake_timer = 0

    # 金苹果闪烁
    flash_timer = 0

    # 预先绘制网格背景
    grid_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    grid_surf.fill(BLACK)
    for x in range(0, SCREEN_WIDTH, CELL_SIZE):
        pygame.draw.line(grid_surf, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT), 1)
    for y in range(0, SCREEN_HEIGHT, CELL_SIZE):
        pygame.draw.line(grid_surf, GRID_COLOR, (0, y), (SCREEN_WIDTH, y), 1)

    while running:
        dt_sec = clock.get_time() / 1000.0
        flash_timer += 1

        # --- 事件 ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                if game_over:
                    if event.key == pygame.K_r:
                        snake.reset()
                        apple.spawn(snake)
                        particles.items.clear()
                        popups.clear()
                        game_over = False
                        paused = False
                        score = 0
                        move_timer = 0
                        shake_timer = 0
                    continue

                if event.key == pygame.K_p:
                    paused = not paused
                    continue

                if not paused:
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        snake.set_direction("UP")
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        snake.set_direction("DOWN")
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        snake.set_direction("LEFT")
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        snake.set_direction("RIGHT")

        # --- 更新 ---
        if not game_over and not paused:
            move_interval = max(3, base_move_interval - score // 5)
            move_timer += 1
            if move_timer >= move_interval:
                move_timer = 0
                snake.move()

                # 吃苹果
                if snake.body[0] == apple.pos:
                    points = 3 if apple.special else 1
                    snake.grow(points)
                    score += points
                    px, py = apple.pixel_center()
                    color = GOLD if apple.special else RED
                    particles.emit(px, py, 15, color, 25)
                    popups.append(ScorePopup(px, py - 15, f"+{points}", GOLD if apple.special else WHITE))
                    apple.spawn(snake)

                # 死亡检测
                if snake.check_death():
                    game_over = True
                    shake_timer = 15
                    hx, hy = snake.head_pixel()
                    particles.emit(hx, hy, 30, RED, 40)
                    if score > high_score:
                        high_score = score

        # 粒子与弹出更新
        particles.update()
        popups = [p for p in popups if p.update()]

        if shake_timer > 0:
            shake_timer -= 1

        # --- 绘制 ---
        shake_x = random.randint(-4, 4) if shake_timer > 0 else 0
        shake_y = random.randint(-4, 4) if shake_timer > 0 else 0

        screen.blit(grid_surf, (shake_x, shake_y))

        # 墙壁边框高亮
        wall_rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(screen, WALL_COLOR, wall_rect, 3)

        # 绘制苹果
        ax, ay = apple.pos[0] * CELL_SIZE, apple.pos[1] * CELL_SIZE
        if apple.special:
            # 金苹果脉冲
            pulse = 1 + math.sin(flash_timer * 0.15) * 0.2
            r = int(CELL_SIZE // 2 * pulse)
            cx, cy = ax + CELL_SIZE // 2, ay + CELL_SIZE // 2
            pygame.draw.circle(screen, GOLD, (cx, cy), r)
            pygame.draw.circle(screen, (255, 240, 180), (cx, cy), r - 2)
            # 光晕
            glow = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 215, 0, 40), (r * 2, r * 2), r * 2)
            screen.blit(glow, (cx - r * 2, cy - r * 2))
        else:
            # 红苹果带叶子
            pulse = 1 + math.sin(flash_timer * 0.1) * 0.08
            r = int(CELL_SIZE // 2 * pulse) - 1
            cx, cy = ax + CELL_SIZE // 2, ay + CELL_SIZE // 2
            pygame.draw.circle(screen, APPLE_RED, (cx, cy), r)
            # 高光
            pygame.draw.circle(screen, APPLE_LIGHT, (cx - 2, cy - 3), max(1, r // 3))
            # 叶子
            leaf_x, leaf_y = cx, cy - r + 1
            pygame.draw.ellipse(screen, APPLE_GREEN, (leaf_x - 3, leaf_y - 3, 7, 5))

        # 绘制蛇身
        head_color = (80, 255, 80)
        tail_color = (0, 120, 0)
        body_len = len(snake.body)

        for i, (bx, by) in enumerate(snake.body):
            t = i / max(1, body_len - 1)
            base = lerp_color(head_color, tail_color, t)
            dark = lerp_color(
                tuple(max(0, c - 40) for c in head_color),
                tuple(max(0, c - 40) for c in tail_color),
                t
            )

            px = bx * CELL_SIZE + shake_x
            py = by * CELL_SIZE + shake_y
            margin = 2 if i == 0 else 1

            # 圆角蛇身
            inner_rect = pygame.Rect(px + margin, py + margin,
                                     CELL_SIZE - margin * 2, CELL_SIZE - margin * 2)
            pygame.draw.rect(screen, base, inner_rect, border_radius=5)
            # 内部高光
            highlight = pygame.Rect(px + margin + 2, py + margin + 2,
                                    CELL_SIZE - margin * 2 - 4, CELL_SIZE // 2 - margin - 1)
            lighter = tuple(min(255, c + 30) for c in base)
            pygame.draw.rect(screen, lighter, highlight, border_radius=3)

            # 蛇头：画眼睛
            if i == 0:
                eye_r = 4
                if snake.direction == "RIGHT":
                    e1 = (px + CELL_SIZE - 6, py + 5)
                    e2 = (px + CELL_SIZE - 6, py + CELL_SIZE - 7)
                elif snake.direction == "LEFT":
                    e1 = (px + 6, py + 5)
                    e2 = (px + 6, py + CELL_SIZE - 7)
                elif snake.direction == "UP":
                    e1 = (px + 5, py + 6)
                    e2 = (px + CELL_SIZE - 7, py + 6)
                elif snake.direction == "DOWN":
                    e1 = (px + 5, py + CELL_SIZE - 6)
                    e2 = (px + CELL_SIZE - 7, py + CELL_SIZE - 6)
                else:
                    e1 = (px + 6, py + 5)
                    e2 = (px + CELL_SIZE - 6, py + CELL_SIZE - 7)

                pygame.draw.circle(screen, WHITE, e1, eye_r)
                pygame.draw.circle(screen, WHITE, e2, eye_r)
                pygame.draw.circle(screen, BLACK, e1, 2)
                pygame.draw.circle(screen, BLACK, e2, 2)

        # 绘制粒子和弹出
        particles.draw(screen)
        for p in popups:
            p.draw(screen)

        # UI
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        hs_text = small_font.render(f"Best: {high_score}", True, GRAY)
        screen.blit(hs_text, (10, 40))

        # 速度指示器
        speed = max(1, 10 - move_interval)
        speed_text = small_font.render(f"Speed: {speed}/10", True, GRAY)
        screen.blit(speed_text, (SCREEN_WIDTH - 120, 10))

        length_text = small_font.render(f"Length: {len(snake.body)}", True, GRAY)
        screen.blit(length_text, (SCREEN_WIDTH - 120, 30))

        # 暂停提示
        if paused and not game_over:
            pause_text = big_font.render("PAUSED", True, WHITE)
            screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2,
                                     SCREEN_HEIGHT // 2 - pause_text.get_height() // 2))
            hint = small_font.render("Press P to resume", True, GRAY)
            screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2,
                               SCREEN_HEIGHT // 2 + 30))

        # 游戏结束
        if game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))

            over_text = big_font.render("GAME OVER", True, RED)
            screen.blit(over_text, (SCREEN_WIDTH // 2 - over_text.get_width() // 2,
                                    SCREEN_HEIGHT // 2 - 50))

            final_text = font.render(f"Score: {score}   Best: {high_score}", True, WHITE)
            screen.blit(final_text, (SCREEN_WIDTH // 2 - final_text.get_width() // 2,
                                     SCREEN_HEIGHT // 2))

            new_record = ""
            if score >= high_score and score > 0:
                new_record = "  NEW RECORD!"
                nr = font.render("NEW RECORD!", True, GOLD)
                screen.blit(nr, (SCREEN_WIDTH // 2 - nr.get_width() // 2,
                                 SCREEN_HEIGHT // 2 + 30))

            restart = small_font.render("Press R to Restart  |  Esc to Quit", True, GRAY)
            screen.blit(restart, (SCREEN_WIDTH // 2 - restart.get_width() // 2,
                                  SCREEN_HEIGHT // 2 + 60))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
