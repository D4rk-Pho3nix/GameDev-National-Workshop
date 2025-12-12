import pygame
import sys
import time
import math

from minesweeper import Minesweeper, MinesweeperAI

HEIGHT = 16
WIDTH = 16
MINES = 40

# Clean Minimalist Color Palette
BG_PRIMARY = (18, 18, 24)       # Deep dark
BG_SECONDARY = (24, 24, 32)    # Slightly lighter
BG_TERTIARY = (32, 32, 42)     # Panel background

# Cell colors - Clean and minimal
CELL_HIDDEN = (45, 47, 58)
CELL_HIDDEN_HOVER = (55, 58, 72)
CELL_REVEALED = (248, 249, 252)
CELL_BORDER = (38, 40, 50)

# Accent colors - Subtle and modern
ACCENT_BLUE = (88, 166, 255)
ACCENT_GREEN = (82, 196, 126)
ACCENT_RED = (248, 113, 113)
ACCENT_YELLOW = (250, 204, 21)
ACCENT_PURPLE = (168, 132, 252)
ACCENT_CYAN = (94, 234, 212)

# Text colors
TEXT_PRIMARY = (248, 249, 252)
TEXT_SECONDARY = (148, 153, 168)
TEXT_DARK = (24, 24, 32)

# Number colors - Clean, readable
NUM_COLORS = [
    (59, 130, 246),    # 1 - Blue
    (34, 197, 94),     # 2 - Green  
    (239, 68, 68),     # 3 - Red
    (139, 92, 246),    # 4 - Purple
    (249, 115, 22),    # 5 - Orange
    (20, 184, 166),    # 6 - Teal
    (75, 85, 99),      # 7 - Gray
    (107, 114, 128),   # 8 - Light Gray
]

# Initialize pygame
pygame.init()
size = width, height = 900, 650
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Minesweeper AI")

# Fonts
OPEN_SANS = "assets/fonts/OpenSans-Regular.ttf"
fontTiny = pygame.font.Font(OPEN_SANS, 13)
fontSmall = pygame.font.Font(OPEN_SANS, 15)
fontMedium = pygame.font.Font(OPEN_SANS, 18)
fontLarge = pygame.font.Font(OPEN_SANS, 24)
fontTitle = pygame.font.Font(OPEN_SANS, 42)
fontNumber = pygame.font.Font(OPEN_SANS, 20)

# Board layout
BOARD_PADDING = 25
SIDEBAR_WIDTH = 220
board_width = width - SIDEBAR_WIDTH - (BOARD_PADDING * 3)
board_height = height - (BOARD_PADDING * 2)
cell_size = int(min(board_width / WIDTH, board_height / HEIGHT))

# Recalculate actual board dimensions
actual_board_width = cell_size * WIDTH
actual_board_height = cell_size * HEIGHT

# Center the board vertically
board_origin = (BOARD_PADDING, (height - actual_board_height) // 2)

# Load images
flag = pygame.image.load("assets/images/flag.png")
flag = pygame.transform.scale(flag, (cell_size - 10, cell_size - 10))
mine = pygame.image.load("assets/images/mine.png")
mine = pygame.transform.scale(mine, (cell_size - 10, cell_size - 10))

# Game state
game = Minesweeper(height=HEIGHT, width=WIDTH, mines=MINES)
ai = MinesweeperAI(height=HEIGHT, width=WIDTH)
revealed = set()
flags = set()
lost = False
instructions = True
start_time = None
elapsed_time = 0
animation_time = 0


def draw_rounded_rect(surface, color, rect, radius=8):
    """Draw a simple rounded rectangle"""
    pygame.draw.rect(surface, color, rect, border_radius=radius)


def draw_cell(surface, rect, is_revealed, is_hover=False):
    """Draw a clean, minimal cell"""
    x, y, w, h = rect
    gap = 2
    inner_rect = (x + gap, y + gap, w - gap * 2, h - gap * 2)
    
    if is_revealed:
        # Clean white revealed cell
        pygame.draw.rect(surface, CELL_REVEALED, inner_rect, border_radius=4)
    else:
        # Subtle hidden cell
        color = CELL_HIDDEN_HOVER if is_hover else CELL_HIDDEN
        pygame.draw.rect(surface, color, inner_rect, border_radius=4)


def draw_panel(surface, rect, alpha=255):
    """Draw a subtle, clean panel"""
    x, y, w, h = rect
    
    # Simple background
    panel_surface = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(panel_surface, (*BG_TERTIARY, alpha), (0, 0, w, h), border_radius=12)
    
    # Very subtle border
    pygame.draw.rect(panel_surface, (255, 255, 255, 8), (0, 0, w, h), 1, border_radius=12)
    
    surface.blit(panel_surface, (x, y))


def draw_button(surface, rect, text, font, is_hover=False, accent_color=None):
    """Draw a sleek, minimal button"""
    x, y, w, h = rect
    
    if accent_color:
        if is_hover:
            # Brighter on hover
            color = tuple(min(c + 30, 255) for c in accent_color)
        else:
            color = accent_color
        text_color = TEXT_PRIMARY
    else:
        color = (52, 54, 68) if not is_hover else (62, 65, 82)
        text_color = TEXT_PRIMARY
    
    # Button background
    pygame.draw.rect(surface, color, rect, border_radius=8)
    
    # Text
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=(x + w // 2, y + h // 2))
    surface.blit(text_surf, text_rect)


def draw_number(surface, number, center):
    """Draw clean, legible number"""
    color = NUM_COLORS[number - 1]
    
    # Main number
    text = fontNumber.render(str(number), True, color)
    text_rect = text.get_rect(center=center)
    surface.blit(text, text_rect)


def draw_glow_circle(surface, center, radius, color, intensity=0.5):
    """Draw subtle glow effect"""
    glow_surf = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
    
    for i in range(int(radius), 0, -1):
        alpha = int((i / radius) * 40 * intensity)
        pygame.draw.circle(glow_surf, (*color, alpha), (radius * 2, radius * 2), i + radius // 2)
    
    surface.blit(glow_surf, (center[0] - radius * 2, center[1] - radius * 2))


def draw_mine_cell(surface, rect, anim_time):
    """Draw mine with subtle glow"""
    x, y, w, h = rect
    center = (x + w // 2, y + h // 2)
    gap = 2
    inner_rect = (x + gap, y + gap, w - gap * 2, h - gap * 2)
    
    # Subtle pulse
    pulse = (math.sin(anim_time * 4) + 1) / 2
    
    # Subtle glow
    draw_glow_circle(surface, center, cell_size // 2, ACCENT_RED, 0.3 + pulse * 0.2)
    
    # Red background
    pygame.draw.rect(surface, (180, 60, 70), inner_rect, border_radius=4)
    
    # Mine image
    mine_rect = mine.get_rect(center=center)
    surface.blit(mine, mine_rect)


def format_time(seconds):
    """Format time as MM:SS"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


# Main game loop
clock = pygame.time.Clock()

while True:
    mouse_pos = pygame.mouse.get_pos()
    dt = clock.get_time() / 1000.0
    animation_time += dt
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()

    # Background
    screen.fill(BG_PRIMARY)

    # Instructions screen
    if instructions:
        # Center panel
        panel_w, panel_h = 420, 380
        panel_x = (width - panel_w) // 2
        panel_y = (height - panel_h) // 2
        
        draw_panel(screen, (panel_x, panel_y, panel_w, panel_h))
        
        # Title
        title = fontTitle.render("Minesweeper", True, TEXT_PRIMARY)
        title_rect = title.get_rect(center=(width // 2, panel_y + 55))
        screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = fontSmall.render("with AI Assistant", True, TEXT_SECONDARY)
        subtitle_rect = subtitle.get_rect(center=(width // 2, panel_y + 95))
        screen.blit(subtitle, subtitle_rect)
        
        # Divider
        pygame.draw.line(screen, (255, 255, 255, 20), 
                        (panel_x + 40, panel_y + 130), 
                        (panel_x + panel_w - 40, panel_y + 130), 1)
        
        # Instructions
        instructions_list = [
            ("Left Click", "Reveal cell"),
            ("Right Click", "Flag mine"),
            ("AI Move", "Auto play"),
        ]
        
        for i, (key, desc) in enumerate(instructions_list):
            y_pos = panel_y + 165 + i * 40
            
            key_text = fontMedium.render(key, True, ACCENT_BLUE)
            key_rect = key_text.get_rect(midleft=(panel_x + 50, y_pos))
            screen.blit(key_text, key_rect)
            
            desc_text = fontSmall.render(desc, True, TEXT_SECONDARY)
            desc_rect = desc_text.get_rect(midleft=(panel_x + 180, y_pos))
            screen.blit(desc_text, desc_rect)

        # Play button
        btn_w, btn_h = 160, 48
        btn_rect = pygame.Rect((width - btn_w) // 2, panel_y + panel_h - 75, btn_w, btn_h)
        btn_hover = btn_rect.collidepoint(mouse_pos)
        draw_button(screen, btn_rect, "Start Game", fontMedium, btn_hover, ACCENT_GREEN)

        # Handle click
        if pygame.mouse.get_pressed()[0] and btn_hover:
            instructions = False
            start_time = time.time()
            time.sleep(0.15)

        pygame.display.flip()
        clock.tick(60)
        continue

    # Update timer
    if start_time and not lost and game.mines != flags:
        elapsed_time = time.time() - start_time

    # Board panel
    board_panel = (
        board_origin[0] - 12,
        board_origin[1] - 12,
        actual_board_width + 24,
        actual_board_height + 24
    )
    draw_panel(screen, board_panel)

    # Draw cells
    cells = []
    for i in range(HEIGHT):
        row = []
        for j in range(WIDTH):
            rect = pygame.Rect(
                board_origin[0] + j * cell_size,
                board_origin[1] + i * cell_size,
                cell_size, cell_size
            )
            
            is_revealed = (i, j) in revealed
            is_hover = rect.collidepoint(mouse_pos) and not is_revealed and not lost
            
            draw_cell(screen, rect, is_revealed, is_hover)

            # Content
            if game.is_mine((i, j)) and lost:
                draw_mine_cell(screen, rect, animation_time)
            elif (i, j) in flags:
                flag_rect = flag.get_rect(center=rect.center)
                screen.blit(flag, flag_rect)
            elif is_revealed:
                nearby = game.nearby_mines((i, j))
                if nearby:
                    draw_number(screen, nearby, rect.center)

            row.append(rect)
        cells.append(row)

    # Sidebar
    sidebar_x = width - SIDEBAR_WIDTH - BOARD_PADDING
    
    # Status panel
    status_y = board_origin[1]
    draw_panel(screen, (sidebar_x, status_y, SIDEBAR_WIDTH, 100))
    
    # Status text
    if lost:
        status_text, status_color = "Game Over", ACCENT_RED
    elif game.mines == flags:
        status_text, status_color = "You Won!", ACCENT_GREEN
    else:
        status_text, status_color = "Playing", ACCENT_BLUE
    
    status = fontLarge.render(status_text, True, status_color)
    status_rect = status.get_rect(center=(sidebar_x + SIDEBAR_WIDTH // 2, status_y + 35))
    screen.blit(status, status_rect)
    
    # Timer & Mines
    timer_text = fontSmall.render(f"Time: {format_time(elapsed_time)}", True, TEXT_SECONDARY)
    screen.blit(timer_text, (sidebar_x + 15, status_y + 70))
    
    mines_left = MINES - len(flags)
    mines_text = fontSmall.render(f"Mines: {mines_left}", True, ACCENT_YELLOW)
    mines_rect = mines_text.get_rect(topright=(sidebar_x + SIDEBAR_WIDTH - 15, status_y + 70))
    screen.blit(mines_text, mines_rect)

    # Buttons
    btn_y = status_y + 120
    btn_h = 44
    btn_gap = 12
    
    # AI Move button
    ai_btn = pygame.Rect(sidebar_x, btn_y, SIDEBAR_WIDTH, btn_h)
    ai_hover = ai_btn.collidepoint(mouse_pos) and not lost
    draw_button(screen, ai_btn, "AI Move", fontMedium, ai_hover, ACCENT_BLUE)
    
    # New Game button
    new_btn = pygame.Rect(sidebar_x, btn_y + btn_h + btn_gap, SIDEBAR_WIDTH, btn_h)
    new_hover = new_btn.collidepoint(mouse_pos)
    draw_button(screen, new_btn, "New Game", fontMedium, new_hover)

    # How to play panel
    help_y = btn_y + (btn_h + btn_gap) * 2 + 20
    draw_panel(screen, (sidebar_x, help_y, SIDEBAR_WIDTH, 120))
    
    help_title = fontMedium.render("How to Play", True, TEXT_PRIMARY)
    help_title_rect = help_title.get_rect(center=(sidebar_x + SIDEBAR_WIDTH // 2, help_y + 22))
    screen.blit(help_title, help_title_rect)
    
    help_lines = ["Left click to reveal", "Right click to flag", "Find all mines to win!"]
    for i, line in enumerate(help_lines):
        text = fontTiny.render(line, True, TEXT_SECONDARY)
        screen.blit(text, (sidebar_x + 15, help_y + 48 + i * 22))

    # AI Knowledge panel
    ai_y = help_y + 140
    draw_panel(screen, (sidebar_x, ai_y, SIDEBAR_WIDTH, 70))
    
    ai_title = fontSmall.render("AI Knowledge", True, TEXT_SECONDARY)
    screen.blit(ai_title, (sidebar_x + 15, ai_y + 15))
    
    safe_count = len(ai.safes - ai.moves_made)
    mine_count = len(ai.mines)
    ai_stats = fontSmall.render(f"Safe: {safe_count}  |  Mines: {mine_count}", True, ACCENT_GREEN)
    screen.blit(ai_stats, (sidebar_x + 15, ai_y + 42))

    # Handle input
    move = None
    left, _, right = pygame.mouse.get_pressed()

    if right and not lost:
        for i in range(HEIGHT):
            for j in range(WIDTH):
                if cells[i][j].collidepoint(mouse_pos) and (i, j) not in revealed:
                    if (i, j) in flags:
                        flags.remove((i, j))
                    else:
                        flags.add((i, j))
                    time.sleep(0.12)

    elif left:
        if ai_hover:
            move = ai.make_safe_move()
            if move is None:
                move = ai.make_random_move()
                if move is None:
                    flags = ai.mines.copy()
            time.sleep(0.12)

        elif new_hover:
            game = Minesweeper(height=HEIGHT, width=WIDTH, mines=MINES)
            ai = MinesweeperAI(height=HEIGHT, width=WIDTH)
            revealed = set()
            flags = set()
            lost = False
            start_time = time.time()
            elapsed_time = 0
            continue

        elif not lost:
            for i in range(HEIGHT):
                for j in range(WIDTH):
                    if (cells[i][j].collidepoint(mouse_pos)
                            and (i, j) not in flags
                            and (i, j) not in revealed):
                        move = (i, j)

    # Process move
    def make_move(move):
        if game.is_mine(move):
            return True
        nearby = game.nearby_mines(move)
        revealed.add(move)
        ai.add_knowledge(move, nearby)
        if not nearby:
            for i in range(move[0] - 1, move[0] + 2):
                for j in range(move[1] - 1, move[1] + 2):
                    if (i, j) != move and 0 <= i < HEIGHT and 0 <= j < WIDTH:
                        if (i, j) not in revealed:
                            make_move((i, j))
        return False

    if move and make_move(move):
        lost = True

    pygame.display.flip()
    clock.tick(60)
