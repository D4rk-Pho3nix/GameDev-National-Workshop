# made by Dark_Pho3nix
"""
Flappy Bird with AI (MPC Controller)
A Flappy Bird clone featuring both manual play and AI-controlled gameplay
using Model Predictive Control with Mixed Integer Programming.
"""

from itertools import cycle
from mip import solve
import random
import sys

import pygame
from pygame.locals import *


# =============================================================================
# GAME CONSTANTS
# =============================================================================

FPS = 30
SCREENWIDTH = 288
SCREENHEIGHT = 512
PIPEGAPSIZE = 100
BASEY = SCREENHEIGHT * 0.79

# Flappy Bird theme colors (extracted from game sprites)
COLOR_FLAPPY_WHITE = (255, 255, 255)
COLOR_FLAPPY_BLACK = (83, 56, 71)
COLOR_FLAPPY_ORANGE = (224, 109, 60)
COLOR_FLAPPY_YELLOW = (250, 218, 94)
COLOR_FLAPPY_GREEN = (99, 204, 79)
COLOR_FLAPPY_BLUE = (112, 197, 206)
COLOR_FLAPPY_BRONZE = (207, 187, 139)
COLOR_FLAPPY_SILVER = (231, 231, 231)
COLOR_FLAPPY_GOLD = (231, 175, 80)

# Asset paths
PLAYERS_LIST = (
    ('assets/sprites/redbird-upflap.png',
     'assets/sprites/redbird-midflap.png',
     'assets/sprites/redbird-downflap.png'),
    ('assets/sprites/bluebird-upflap.png',
     'assets/sprites/bluebird-midflap.png',
     'assets/sprites/bluebird-downflap.png'),
    ('assets/sprites/yellowbird-upflap.png',
     'assets/sprites/yellowbird-midflap.png',
     'assets/sprites/yellowbird-downflap.png'),
)

BACKGROUNDS_LIST = (
    'assets/sprites/background-day.png',
    'assets/sprites/background-night.png',
)

PIPES_LIST = (
    'assets/sprites/pipe-green.png',
    'assets/sprites/pipe-red.png',
)

# Global resources
IMAGES = {}
SOUNDS = {}
HITMASKS = {}
SCREEN = None
FPSCLOCK = None
HIGH_SCORE = 0


# =============================================================================
# TEXT RENDERING (Flappy Bird Style - outlined text)
# =============================================================================

def draw_text_outlined(surface, text, font_size, x, y, main_color, outline_color=COLOR_FLAPPY_BLACK, center=True):
    """Draw text with outline effect like original Flappy Bird"""
    font = pygame.font.Font(None, font_size)
    
    # Draw outline (render text in 8 directions)
    outline_positions = [(-2, -2), (-2, 0), (-2, 2), (0, -2), (0, 2), (2, -2), (2, 0), (2, 2)]
    outline_surf = font.render(text, True, outline_color)
    
    if center:
        base_rect = outline_surf.get_rect(center=(x, y))
    else:
        base_rect = outline_surf.get_rect(topleft=(x, y))
    
    for dx, dy in outline_positions:
        surface.blit(outline_surf, (base_rect.x + dx, base_rect.y + dy))
    
    # Draw main text
    text_surf = font.render(text, True, main_color)
    surface.blit(text_surf, base_rect)
    
    return base_rect


def draw_score_sprites(surface, score, y_pos=None):
    """Draw score using the game's number sprites"""
    score_digits = [int(x) for x in str(score)]
    total_width = sum(IMAGES['numbers'][d].get_width() for d in score_digits)
    x_offset = (SCREENWIDTH - total_width) / 2
    
    if y_pos is None:
        y_pos = SCREENHEIGHT * 0.1
    
    for digit in score_digits:
        SCREEN.blit(IMAGES['numbers'][digit], (x_offset, y_pos))
        x_offset += IMAGES['numbers'][digit].get_width()


# =============================================================================
# TITLE / MODE SELECTION SCREEN
# =============================================================================

def show_title_screen():
    """Show title screen with mode selection - Flappy Bird style"""
    # Animation state
    player_index = 0
    player_index_gen = cycle([0, 1, 2, 1])
    loop_iter = 0
    bird_shm = {'val': 0, 'dir': 1}
    
    player_x = SCREENWIDTH // 2 - IMAGES['player'][0].get_width() // 2
    player_y = SCREENHEIGHT // 2 - 60
    
    base_x = 0
    base_shift = IMAGES['base'].get_width() - IMAGES['background'].get_width()
    
    # Selection state
    selected = 0  # 0 = manual, 1 = ai
    blink_timer = 0
    
    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            
            if event.type == KEYDOWN:
                if event.key == K_m:
                    SOUNDS['swoosh'].play()
                    return 'manual'
                elif event.key == K_a:
                    SOUNDS['swoosh'].play()
                    return 'ai'
                elif event.key in (K_UP, K_w):
                    selected = (selected - 1) % 2
                    SOUNDS['swoosh'].play()
                elif event.key in (K_DOWN, K_s):
                    selected = (selected + 1) % 2
                    SOUNDS['swoosh'].play()
                elif event.key in (K_RETURN, K_SPACE):
                    SOUNDS['wing'].play()
                    return 'manual' if selected == 0 else 'ai'
        
        # Update animations
        loop_iter += 1
        blink_timer += 1
        
        if loop_iter % 5 == 0:
            player_index = next(player_index_gen)
        
        # Bird bobbing
        if abs(bird_shm['val']) == 8:
            bird_shm['dir'] *= -1
        bird_shm['val'] += bird_shm['dir']
        
        # Scrolling base
        base_x = -((-base_x + 2) % base_shift)
        
        # === RENDERING ===
        SCREEN.blit(IMAGES['background'], (0, 0))
        
        # Title using message sprite position area
        draw_text_outlined(SCREEN, "FLAPPY BIRD", 52, SCREENWIDTH // 2, 80, 
                          COLOR_FLAPPY_YELLOW)
        draw_text_outlined(SCREEN, "AI Edition", 32, SCREENWIDTH // 2, 115, 
                          COLOR_FLAPPY_WHITE)
        
        # Bird mascot
        bird_y = player_y + bird_shm['val']
        SCREEN.blit(IMAGES['player'][player_index], (player_x, bird_y))
        
        # Mode selection
        manual_color = COLOR_FLAPPY_YELLOW if selected == 0 else COLOR_FLAPPY_WHITE
        ai_color = COLOR_FLAPPY_BLUE if selected == 1 else COLOR_FLAPPY_WHITE
        
        # Selection arrow (blinking)
        show_arrow = (blink_timer // 10) % 2 == 0
        
        draw_text_outlined(SCREEN, "SELECT MODE", 28, SCREENWIDTH // 2, 280, 
                          COLOR_FLAPPY_ORANGE)
        
        # Manual option
        if selected == 0 and show_arrow:
            draw_text_outlined(SCREEN, ">", 32, 45, 320, COLOR_FLAPPY_YELLOW)
        draw_text_outlined(SCREEN, "[M] MANUAL", 32, SCREENWIDTH // 2, 320, manual_color)
        
        # AI option  
        if selected == 1 and show_arrow:
            draw_text_outlined(SCREEN, ">", 32, 65, 360, COLOR_FLAPPY_BLUE)
        draw_text_outlined(SCREEN, "[A] AI", 32, SCREENWIDTH // 2, 360, ai_color)
        
        # High score
        if HIGH_SCORE > 0:
            draw_text_outlined(SCREEN, f"BEST: {HIGH_SCORE}", 24, SCREENWIDTH // 2, 420, 
                              COLOR_FLAPPY_GOLD)
        
        # Base
        SCREEN.blit(IMAGES['base'], (base_x, BASEY))
        
        pygame.display.update()
        FPSCLOCK.tick(FPS)


# =============================================================================
# GET READY SCREEN
# =============================================================================

def show_get_ready_screen(game_mode):
    """Show get ready screen before gameplay"""
    player_index = 0
    player_index_gen = cycle([0, 1, 2, 1])
    loop_iter = 0
    
    player_x = int(SCREENWIDTH * 0.2)
    player_y = int((SCREENHEIGHT - IMAGES['player'][0].get_height()) / 2)
    
    message_x = int((SCREENWIDTH - IMAGES['message'].get_width()) / 2)
    message_y = int(SCREENHEIGHT * 0.12)
    
    base_x = 0
    base_shift = IMAGES['base'].get_width() - IMAGES['background'].get_width()
    
    player_shm = {'val': 0, 'dir': 1}
    
    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and event.key in (K_SPACE, K_UP, K_w):
                SOUNDS['wing'].play()
                return {
                    'playery': player_y + player_shm['val'],
                    'basex': base_x,
                    'playerIndexGen': player_index_gen,
                }
        
        # Animations
        if (loop_iter + 1) % 5 == 0:
            player_index = next(player_index_gen)
        loop_iter = (loop_iter + 1) % 30
        base_x = -((-base_x + 4) % base_shift)
        
        # Bird bobbing
        if abs(player_shm['val']) == 8:
            player_shm['dir'] *= -1
        player_shm['val'] += player_shm['dir']
        
        # === RENDERING ===
        SCREEN.blit(IMAGES['background'], (0, 0))
        SCREEN.blit(IMAGES['player'][player_index],
                   (player_x, player_y + player_shm['val']))
        SCREEN.blit(IMAGES['message'], (message_x, message_y))
        
        # Mode indicator (small, top corner)
        if game_mode == 'ai':
            draw_text_outlined(SCREEN, "AI", 28, 30, 20, COLOR_FLAPPY_BLUE, center=False)
        else:
            draw_text_outlined(SCREEN, "MANUAL", 22, 10, 20, COLOR_FLAPPY_YELLOW, center=False)
        
        SCREEN.blit(IMAGES['base'], (base_x, BASEY))
        
        pygame.display.update()
        FPSCLOCK.tick(FPS)


# =============================================================================
# MAIN GAME LOOP
# =============================================================================

def main_game(movement_info, game_mode='ai'):
    """Main gameplay loop"""
    score = 0
    player_index = 0
    loop_iter = 0
    player_index_gen = movement_info['playerIndexGen']
    player_x = int(SCREENWIDTH * 0.2)
    player_y = movement_info['playery']
    
    base_x = movement_info['basex']
    base_shift = IMAGES['base'].get_width() - IMAGES['background'].get_width()
    
    # Generate pipes
    new_pipe1 = get_random_pipe()
    new_pipe2 = get_random_pipe()
    
    upper_pipes = [
        {'x': SCREENWIDTH, 'y': new_pipe1[0]['y']},
        {'x': SCREENWIDTH + SCREENWIDTH / 2, 'y': new_pipe2[0]['y']},
    ]
    lower_pipes = [
        {'x': SCREENWIDTH, 'y': new_pipe1[1]['y']},
        {'x': SCREENWIDTH + SCREENWIDTH / 2, 'y': new_pipe2[1]['y']},
    ]
    
    pipe_vel_x = -4
    
    # Physics
    player_vel_y = -9
    player_max_vel_y = 10
    player_min_vel_y = -8
    player_acc_y = 1
    player_rot = 45
    player_vel_rot = 3
    player_rot_thr = 20
    player_flap_acc = -14
    player_flapped = False
    
    traj = []
    
    while True:
        # === INPUT ===
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            
            if game_mode == 'manual':
                if event.type == KEYDOWN and event.key in (K_SPACE, K_UP, K_w):
                    if player_y > -2 * IMAGES['player'][0].get_height():
                        player_vel_y = player_flap_acc
                        player_flapped = True
                        SOUNDS['wing'].play()
        
        # === AI CONTROL ===
        if game_mode == 'ai':
            flap, traj = solve(player_y, player_vel_y, lower_pipes)
            if flap:
                player_vel_y += player_flap_acc
                player_flapped = True
                SOUNDS['wing'].play()
        else:
            traj = []
        
        # === PHYSICS ===
        if player_rot > -90:
            player_rot -= player_vel_rot
        
        if not player_flapped:
            player_vel_y += player_acc_y
        
        if player_flapped:
            player_flapped = False
            player_rot = 45
        
        player_vel_y = max(player_min_vel_y, min(player_max_vel_y, player_vel_y))
        player_height = IMAGES['player'][player_index].get_height()
        player_y += player_vel_y
        
        # === COLLISIONS ===
        if player_y + player_height >= BASEY:
            player_y = BASEY - player_height
            return create_crash_info(player_y, True, base_x, upper_pipes, 
                                    lower_pipes, score, 0, player_rot)
        
        if player_y <= 0:
            player_y = 0
            player_vel_y = 0
        
        crash = check_crash({'x': player_x, 'y': player_y, 'index': player_index},
                           upper_pipes, lower_pipes)
        if crash[0]:
            return create_crash_info(player_y, crash[1], base_x, upper_pipes,
                                    lower_pipes, score, player_vel_y, player_rot)
        
        # === SCORING ===
        player_mid = player_x + IMAGES['player'][0].get_width() / 2
        for pipe in upper_pipes:
            pipe_mid = pipe['x'] + IMAGES['pipe'][0].get_width() / 2
            if pipe_mid <= player_mid < pipe_mid + 4:
                score += 1
                SOUNDS['point'].play()
        
        # === UPDATE STATE ===
        if (loop_iter + 1) % 3 == 0:
            player_index = next(player_index_gen)
        loop_iter = (loop_iter + 1) % 30
        base_x = -((-base_x + 100) % base_shift)
        
        for uPipe, lPipe in zip(upper_pipes, lower_pipes):
            uPipe['x'] += pipe_vel_x
            lPipe['x'] += pipe_vel_x
        
        if 0 < upper_pipes[0]['x'] < 5:
            new_pipe = get_random_pipe()
            upper_pipes.append(new_pipe[0])
            lower_pipes.append(new_pipe[1])
        
        if upper_pipes[0]['x'] < -IMAGES['pipe'][0].get_width():
            upper_pipes.pop(0)
            lower_pipes.pop(0)
        
        # === RENDERING ===
        SCREEN.blit(IMAGES['background'], (0, 0))
        
        for uPipe, lPipe in zip(upper_pipes, lower_pipes):
            SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
            SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))
        
        SCREEN.blit(IMAGES['base'], (base_x, BASEY))
        
        # Score (using sprite numbers)
        draw_score_sprites(SCREEN, score)
        
        # Mode indicator (minimal, top-left)
        if game_mode == 'ai':
            draw_text_outlined(SCREEN, "AI", 24, 20, 15, COLOR_FLAPPY_BLUE, center=False)
        else:
            draw_text_outlined(SCREEN, "YOU", 20, 10, 15, COLOR_FLAPPY_YELLOW, center=False)
        
        # Player
        visible_rot = min(player_rot_thr, player_rot)
        player_surface = pygame.transform.rotate(IMAGES['player'][player_index], visible_rot)
        SCREEN.blit(player_surface, (player_x, player_y))
        
        # AI trajectory (subtle red line)
        if game_mode == 'ai' and traj and len(traj) > 1:
            offset_x = IMAGES['player'][0].get_width() / 2
            offset_y = IMAGES['player'][0].get_height() / 2
            points = [(x + offset_x, y + offset_y) for (x, y) in traj]
            pygame.draw.lines(SCREEN, (255, 80, 80), False, points, 2)
        
        pygame.display.update()
        FPSCLOCK.tick(FPS)


# =============================================================================
# GAME OVER SCREEN
# =============================================================================

def show_game_over_screen(crash_info, game_mode):
    """Show game over screen - Flappy Bird style"""
    global HIGH_SCORE
    
    score = crash_info['score']
    is_new_high = score > HIGH_SCORE
    if is_new_high:
        HIGH_SCORE = score
    
    player_x = SCREENWIDTH * 0.2
    player_y = crash_info['y']
    player_height = IMAGES['player'][0].get_height()
    player_vel_y = crash_info['playerVelY']
    player_acc_y = 2
    player_rot = crash_info['playerRot']
    player_vel_rot = 7
    
    base_x = crash_info['basex']
    upper_pipes = crash_info['upperPipes']
    lower_pipes = crash_info['lowerPipes']
    
    SOUNDS['hit'].play()
    if not crash_info['groundCrash']:
        SOUNDS['die'].play()
    
    blink_timer = 0
    show_restart = False
    
    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and event.key in (K_SPACE, K_UP, K_w):
                if show_restart:
                    SOUNDS['swoosh'].play()
                    return
            if event.type == MOUSEBUTTONDOWN and show_restart:
                SOUNDS['swoosh'].play()
                return
        
        blink_timer += 1
        
        # Bird falling animation
        if player_y + player_height < BASEY - 1:
            player_y += min(player_vel_y, BASEY - player_y - player_height)
            if player_vel_y < 15:
                player_vel_y += player_acc_y
            if not crash_info['groundCrash'] and player_rot > -90:
                player_rot -= player_vel_rot
        else:
            show_restart = True
        
        # === RENDERING ===
        SCREEN.blit(IMAGES['background'], (0, 0))
        
        for uPipe, lPipe in zip(upper_pipes, lower_pipes):
            SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
            SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))
        
        SCREEN.blit(IMAGES['base'], (base_x, BASEY))
        
        # Bird
        player_surface = pygame.transform.rotate(IMAGES['player'][1], player_rot)
        SCREEN.blit(player_surface, (player_x, player_y))
        
        # Game over sprite
        SCREEN.blit(IMAGES['gameover'], (50, 180))
        
        # Score display
        draw_text_outlined(SCREEN, "SCORE", 28, SCREENWIDTH // 2, 240, COLOR_FLAPPY_WHITE)
        draw_text_outlined(SCREEN, str(score), 56, SCREENWIDTH // 2, 280, COLOR_FLAPPY_YELLOW)
        
        # Best score
        draw_text_outlined(SCREEN, f"BEST: {HIGH_SCORE}", 28, SCREENWIDTH // 2, 330, 
                          COLOR_FLAPPY_GOLD)
        
        # New high score (blinking)
        if is_new_high and (blink_timer // 12) % 2 == 0:
            draw_text_outlined(SCREEN, "NEW!", 32, SCREENWIDTH // 2, 365, COLOR_FLAPPY_GREEN)
        
        # Mode played
        if game_mode == 'ai':
            draw_text_outlined(SCREEN, "AI Mode", 22, SCREENWIDTH // 2, 400, COLOR_FLAPPY_BLUE)
        else:
            draw_text_outlined(SCREEN, "Manual Mode", 22, SCREENWIDTH // 2, 400, COLOR_FLAPPY_YELLOW)
        
        # Restart prompt (blinking)
        if show_restart and (blink_timer // 20) % 2 == 0:
            draw_text_outlined(SCREEN, "TAP TO RESTART", 24, SCREENWIDTH // 2, 450, 
                              COLOR_FLAPPY_WHITE)
        
        pygame.display.update()
        FPSCLOCK.tick(FPS)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_crash_info(player_y, ground_crash, base_x, upper_pipes, lower_pipes,
                      score, player_vel_y, player_rot):
    return {
        'y': player_y,
        'groundCrash': ground_crash,
        'basex': base_x,
        'upperPipes': upper_pipes,
        'lowerPipes': lower_pipes,
        'score': score,
        'playerVelY': player_vel_y,
        'playerRot': player_rot
    }


def get_random_pipe():
    gap_y = random.randrange(0, int(BASEY * 0.6 - PIPEGAPSIZE))
    gap_y += int(BASEY * 0.2)
    pipe_height = IMAGES['pipe'][0].get_height()
    pipe_x = SCREENWIDTH + 10
    return [
        {'x': pipe_x, 'y': gap_y - pipe_height},
        {'x': pipe_x, 'y': gap_y + PIPEGAPSIZE},
    ]


def check_crash(player, upper_pipes, lower_pipes):
    pi = player['index']
    player['w'] = IMAGES['player'][0].get_width()
    player['h'] = IMAGES['player'][0].get_height()
    
    player_rect = pygame.Rect(player['x'], player['y'], player['w'], player['h'])
    pipe_w = IMAGES['pipe'][0].get_width()
    pipe_h = IMAGES['pipe'][0].get_height()
    
    for uPipe, lPipe in zip(upper_pipes, lower_pipes):
        u_rect = pygame.Rect(uPipe['x'], uPipe['y'], pipe_w, pipe_h)
        l_rect = pygame.Rect(lPipe['x'], lPipe['y'], pipe_w, pipe_h)
        
        if pixel_collision(player_rect, u_rect, HITMASKS['player'][pi], HITMASKS['pipe'][0]):
            return [True, False]
        if pixel_collision(player_rect, l_rect, HITMASKS['player'][pi], HITMASKS['pipe'][1]):
            return [True, False]
    
    return [False, False]


def pixel_collision(rect1, rect2, hitmask1, hitmask2):
    rect = rect1.clip(rect2)
    if rect.width == 0 or rect.height == 0:
        return False
    
    x1, y1 = rect.x - rect1.x, rect.y - rect1.y
    x2, y2 = rect.x - rect2.x, rect.y - rect2.y
    
    for x in range(rect.width):
        for y in range(rect.height):
            if hitmask1[x1 + x][y1 + y] and hitmask2[x2 + x][y2 + y]:
                return True
    return False


def get_hitmask(image):
    mask = []
    for x in range(image.get_width()):
        mask.append([])
        for y in range(image.get_height()):
            mask[x].append(bool(image.get_at((x, y))[3]))
    return mask


# =============================================================================
# INITIALIZATION
# =============================================================================

def load_assets():
    """Load static game assets"""
    IMAGES['numbers'] = tuple(
        pygame.image.load(f'assets/sprites/{i}.png').convert_alpha() 
        for i in range(10)
    )
    IMAGES['gameover'] = pygame.image.load('assets/sprites/gameover.png').convert_alpha()
    IMAGES['message'] = pygame.image.load('assets/sprites/message.png').convert_alpha()
    IMAGES['base'] = pygame.image.load('assets/sprites/base.png').convert_alpha()
    
    sound_ext = '.wav' if 'win' in sys.platform else '.ogg'
    SOUNDS['die'] = pygame.mixer.Sound(f'assets/audio/die{sound_ext}')
    SOUNDS['hit'] = pygame.mixer.Sound(f'assets/audio/hit{sound_ext}')
    SOUNDS['point'] = pygame.mixer.Sound(f'assets/audio/point{sound_ext}')
    SOUNDS['swoosh'] = pygame.mixer.Sound(f'assets/audio/swoosh{sound_ext}')
    SOUNDS['wing'] = pygame.mixer.Sound(f'assets/audio/wing{sound_ext}')


def load_random_sprites():
    """Load randomized visual assets"""
    # Background
    bg_idx = random.randint(0, len(BACKGROUNDS_LIST) - 1)
    IMAGES['background'] = pygame.image.load(BACKGROUNDS_LIST[bg_idx]).convert()
    
    # Player
    player_idx = random.randint(0, len(PLAYERS_LIST) - 1)
    IMAGES['player'] = tuple(
        pygame.image.load(PLAYERS_LIST[player_idx][i]).convert_alpha()
        for i in range(3)
    )
    
    # Pipes
    pipe_idx = random.randint(0, len(PIPES_LIST) - 1)
    IMAGES['pipe'] = (
        pygame.transform.flip(
            pygame.image.load(PIPES_LIST[pipe_idx]).convert_alpha(), False, True
        ),
        pygame.image.load(PIPES_LIST[pipe_idx]).convert_alpha(),
    )
    
    # Hitmasks
    HITMASKS['pipe'] = (get_hitmask(IMAGES['pipe'][0]), get_hitmask(IMAGES['pipe'][1]))
    HITMASKS['player'] = tuple(get_hitmask(IMAGES['player'][i]) for i in range(3))


def main():
    """Main entry point"""
    global SCREEN, FPSCLOCK
    
    pygame.init()
    pygame.display.set_caption('Flappy Bird - AI Edition')
    SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
    FPSCLOCK = pygame.time.Clock()
    
    load_assets()
    
    while True:
        load_random_sprites()
        game_mode = show_title_screen()
        movement_info = show_get_ready_screen(game_mode)
        crash_info = main_game(movement_info, game_mode)
        show_game_over_screen(crash_info, game_mode)


if __name__ == '__main__':
    main()
