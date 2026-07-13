import pygame
import random

# --- 初始化 ---
pygame.init()

# --- 常量定义 ---
CELL_SIZE = 20
GRID_WIDTH = 40
GRID_HEIGHT = 25
SCREEN_WIDTH = CELL_SIZE * GRID_WIDTH
SCREEN_HEIGHT = CELL_SIZE * GRID_HEIGHT
FPS = 10

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# --- 类定义 ---

class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        # 初始蛇头位置
        self.body = [(10, 10)]
        self.direction = 'RIGHT'
        self.grow_pending = False

    def move(self):
        # 计算新头部位置
        head_x, head_y = self.body[0]
        if self.direction == 'RIGHT':
            new_x, new_y = head_x + CELL_SIZE, head_y
        elif self.direction == 'LEFT':
            new_x, new_y = head_x - CELL_SIZE, head_y
        elif self.direction == 'UP':
            new_x, new_y = head_x, head_y - CELL_SIZE
        elif self.direction == 'DOWN':
            new_x, new_y = head_x, head_y + CELL_SIZE
        
        new_head = (new_x, new_y)
        
        # 移动逻辑：将新头加入，如果不需要增长则移除尾部
        self.body.insert(0, new_head)
        if not self.grow_pending:
            self.body.pop()
        else:
            self.grow_pending = False

    def grow(self):
        self.grow_pending = True

    def check_collision(self):
        head = self.body[0]
        # 撞墙检测
        if head[0] < 0 or head[0] >= SCREEN_WIDTH or head[1] < 0 or head[1] >= SCREEN_HEIGHT:
            return True
        # 撞自身检测
        if head in self.body[1:]:
            return True
        return False

class Apple:
    def __init__(self, snake):
        # 生成随机位置，确保不与蛇身重叠
        while True:
            x = random.randint(0, SCREEN_WIDTH - CELL_SIZE)
            y = random.randint(0, SCREEN_HEIGHT - CELL_SIZE)
            if (x, y) not in snake.body:
                self.body = (x, y)
                break

# --- 主游戏循环 ---
def main():
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("贪食蛇 - Qwythos by Empero AI")
    
    font = pygame.font.SysFont("monospace", 35)
    big_font = pygame.font.SysFont("monospace", 50)
    
    snake = Snake()
    apple = Apple(snake)
    
    running = True
    game_over = False
    
    while running:
        # 1. 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if game_over:
                    if event.key == pygame.K_r:
                        snake.reset()
                        apple = Apple(snake)
                        game_over = False
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                    continue
                
                if event.key == pygame.K_UP:
                    if snake.direction != 'DOWN':
                        snake.direction = 'UP'
                elif event.key == pygame.K_DOWN:
                    if snake.direction != 'UP':
                        snake.direction = 'DOWN'
                elif event.key == pygame.K_LEFT:
                    if snake.direction != 'RIGHT':
                        snake.direction = 'LEFT'
                elif event.key == pygame.K_RIGHT:
                    if snake.direction != 'LEFT':
                        snake.direction = 'RIGHT'

        if not game_over:
            snake.move()
            
            # 吃苹果
            if snake.body[0] == apple.body:
                snake.grow()
                apple = Apple(snake)
            
            # 检测碰撞
            if snake.check_collision():
                game_over = True

        # 2. 渲染画面
        screen.fill(BLACK)
        
        # 绘制苹果
        pygame.draw.rect(screen, RED, (*apple.body, CELL_SIZE, CELL_SIZE))
        
        # 绘制蛇
        for i, segment in enumerate(snake.body):
            color = GREEN if i == 0 else (0, 255, 0) # 蛇头颜色略深
            pygame.draw.rect(screen, color, (*segment, CELL_SIZE, CELL_SIZE))
        
        # 绘制分数
        score_text = font.render(f"Score: {len(snake.body)-1}", True, WHITE)
        screen.blit(score_text, (5, 5))
        
        # 绘制游戏结束文字
        if game_over:
            over_text = big_font.render("GAME OVER", True, WHITE)
            text_rect = over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            screen.blit(over_text, text_rect)
            
            restart_text = font.render("Press 'R' to Restart or 'ESC' to Quit", True, WHITE)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40))
            screen.blit(restart_text, restart_rect)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()