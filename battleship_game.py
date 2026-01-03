from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math

cam_pos = [0, 500, 500]
cam_angle = 0 
cam_height = 500
cam_mode = "third_person"

p_pos = [0, 0, 0]
p_angle = 0
p_life = 5
p_alive = True
p_moving_forward = False
p_moving_backward = False 

score = 0
missed = 0
gameover = False

missiles = []
missile_speed = 10  #adjust here

# Enemy missiles
enemy_missiles = []
enemy_fire_cooldown = 0

# Enemy ships
enemies = [] 
enemy_size_factor = 1.0
enemy_size_growing = True

cheat_mode = False
cheat_vision = False
auto_rotation = 0

fovY = 80
grid_length = 600
boundary_height = 100

water_time = 0
wave_amplitude = 3
wave_frequency = 0.05

HIGH_SCORE_FILE = "highscores.txt"
TOP_N = 5
high_scores = []

difficulty = "MEDIUM"

DIFFICULTY_SETTINGS = {
    "EASY": {
        "enemy_count": 3,
        "enemy_speed": 0.06,
        "enemy_fire_rate": 120,
        "enemy_missile_speed": 2,
        "max_missed": 15
    },
    "MEDIUM": {
        "enemy_count": 5,
        "enemy_speed": 0.1,
        "enemy_fire_rate": 80,
        "enemy_missile_speed": 3,
        "max_missed": 10
    },
    "HARD": {
        "enemy_count": 8,
        "enemy_speed": 0.18,
        "enemy_fire_rate": 50,
        "enemy_missile_speed": 4,
        "max_missed": 6
    }
}

mines = []  
mine_radius = 150  

def drop_mine():
    if not gameover:
        angle_rad = math.radians(p_angle)
        mine_x = p_pos[0] + 50 * math.cos(angle_rad)
        mine_y = p_pos[1] + 50 * math.sin(angle_rad)
        mine_z = p_pos[2]
        mines.append([mine_x, mine_y, mine_z])

def update_mines():
    global mines, score
    mines_to_remove = []

    for i, mine in enumerate(mines):
        mx, my, mz = mine
        for j, enemy in enumerate(enemies):
            ex, ey, ez = enemy
            distance = math.sqrt((mx - ex)**2 + (my - ey)**2)
            if distance < mine_radius:
                score += 1
                respawn_enemy(j)
                mines_to_remove.append(i)  
                break

    for i in sorted(mines_to_remove, reverse=True):
        if i < len(mines):
            mines.pop(i)

def draw_mine(x, y, z):
    glPushMatrix()

    hover = 10 + math.sin(water_time * 0.1) * 3
    glTranslatef(x, y, z + hover)
    glRotatef(water_time * 2 % 360, 0, 0, 1)

    glow_factor = 0.05 * math.sin(water_time * 0.3)
    glColor3f(0.1 + glow_factor, 0.1 + glow_factor, 0.1 + glow_factor)
    glutSolidSphere(15, 30, 30)

    glPushMatrix()
    glColor3f(0.25, 0.25, 0.25)
    glRotatef(90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 10.5, 10.5, 2, 20, 1)
    glPopMatrix()

    spike_length = 12
    spike_tip_length = 4

    glColor3f(0.1, 0.1, 0.1)
    quad = gluNewQuadric()

    glPushMatrix()
    glTranslatef(0, 0, 15)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(quad, 2, 0, spike_length, 8, 2)  
    glTranslatef(0, 0, spike_length)
    glColor3f(1.0, 0.2 + 0.3*math.sin(water_time*0.2), 0.2)
    gluCylinder(quad, 1.5, 0, spike_tip_length, 8, 2)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, -15)
    glRotatef(90, 1, 0, 0)
    gluCylinder(quad, 2, 0, spike_length, 8, 2)
    glTranslatef(0, 0, spike_length)
    glColor3f(1.0, 0.2 + 0.3*math.sin(water_time*0.2), 0.2)
    gluCylinder(quad, 1.5, 0, spike_tip_length, 8, 2)
    glPopMatrix()

    for angle in [0, 90, 180, 270]:
        glPushMatrix()
        glRotatef(angle + water_time, 0, 0, 1)
        glTranslatef(15, 0, 0)
        glRotatef(90, 0, 1, 0)
        glColor3f(0.1, 0.1, 0.1)
        gluCylinder(quad, 2, 0, spike_length, 8, 2)
        glTranslatef(0, 0, spike_length)
        glColor3f(1.0, 0.2 + 0.3*math.sin(water_time*0.2), 0.2)
        gluCylinder(quad, 1.5, 0, spike_tip_length, 8, 2)
        glPopMatrix()

    glPopMatrix()


def apply_difficulty():
    global enemy_speed, enemy_fire_rate, enemy_missile_speed
    global max_missed
    settings = DIFFICULTY_SETTINGS[difficulty]
    enemy_speed = settings["enemy_speed"]
    enemy_fire_rate = settings["enemy_fire_rate"]
    enemy_missile_speed = settings["enemy_missile_speed"]
    max_missed = settings["max_missed"]
    enemy_fire_cooldown = 0

def load_high_scores():
    global high_scores
    try:
        with open(HIGH_SCORE_FILE, "r") as f:
            high_scores = [int(line.strip()) for line in f.readlines()]
    except:
        high_scores = []

def save_high_scores():
    with open(HIGH_SCORE_FILE, "w") as f:
        for s in high_scores[:TOP_N]:
            f.write(str(s) + "\n")

def update_high_scores(new_score):
    global high_scores
    high_scores.append(new_score)
    high_scores = sorted(high_scores, reverse=True)[:TOP_N]
    save_high_scores()


def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def initialize_enemies():
    global enemies
    enemies = []

    count = DIFFICULTY_SETTINGS[difficulty]["enemy_count"]

    for i in range(count):
        while True:
            x = random.uniform(-grid_length + 100, grid_length - 100)
            y = random.uniform(-grid_length + 100, grid_length - 100)
            if abs(x) > 150 or abs(y) > 150:
                enemies.append([x, y, 0])
                break


def respawn_enemy(index):
    while True:
        x = random.uniform(-grid_length + 100, grid_length - 100)
        y = random.uniform(-grid_length + 100, grid_length - 100)
        px, py, pz = p_pos
        if math.sqrt((x - px)**2 + (y - py)**2) > 200:
            enemies[index] = [x, y, 0]
            break

def draw_battleship():
    glPushMatrix()
    glTranslatef(p_pos[0], p_pos[1], p_pos[2])
    glRotatef(p_angle, 0, 0, 1)
    
    if gameover:
        glRotatef(90, 0, 1, 0) 
    
    glPushMatrix()
    glTranslatef(0, 0, 5)
    glColor3f(0.3, 0.3, 0.35)
    glScalef(2.5, 0.8, 0.3)
    glutSolidCube(30)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, 20)
    glColor3f(0.5, 0.5, 0.55)
    glScalef(2.0, 0.6, 0.4)
    glutSolidCube(30)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-10, 0, 35)
    glColor3f(0.4, 0.4, 0.45)
    glScalef(0.8, 0.6, 1.0)
    glutSolidCube(25)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-10, 0, 55)
    glColor3f(0.6, 0.6, 0.65)
    glScalef(0.3, 0.3, 0.8)
    glutSolidCube(20)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-10, 0, 65)
    glColor3f(0.7, 0.7, 0.1)
    glRotatef(90, 1, 0, 0)
    glutSolidTorus(3, 8, 8, 12)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(20, 0, 25)
    glColor3f(0.35, 0.35, 0.4)
    gluCylinder(gluNewQuadric(), 12, 12, 15, 12, 1)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(20, 5, 30)
    glRotatef(90, 0, 1, 0)
    glColor3f(0.2, 0.2, 0.25)
    gluCylinder(gluNewQuadric(), 4, 4, 45, 10, 1)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(20, -5, 30)
    glRotatef(90, 0, 1, 0)
    glColor3f(0.2, 0.2, 0.25)
    gluCylinder(gluNewQuadric(), 4, 4, 45, 10, 1)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(0, 18, 22)
    glColor3f(0.3, 0.3, 0.35)
    gluSphere(gluNewQuadric(), 8, 10, 10)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(0, -18, 22)
    glColor3f(0.3, 0.3, 0.35)
    gluSphere(gluNewQuadric(), 8, 10, 10)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-25, 8, 35)
    glColor3f(0.8, 0.3, 0.1)
    gluCylinder(gluNewQuadric(), 5, 4, 25, 10, 1)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-25, -8, 35)
    glColor3f(0.8, 0.3, 0.1)
    gluCylinder(gluNewQuadric(), 5, 4, 25, 10, 1)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(45, 0, 15)
    glRotatef(90, 0, 1, 0)
    glColor3f(0.35, 0.35, 0.4)
    glutSolidCone(12, 25, 10, 10)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-50, 0, 10)
    glColor3f(0.3, 0.3, 0.35)
    glScalef(0.3, 0.8, 0.4)
    glutSolidCube(20)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-40, 0, 35)
    glColor3f(0.6, 0.5, 0.3)
    gluCylinder(gluNewQuadric(), 1, 1, 30, 8, 1)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-40, 0, 60)
    glColor3f(0.9, 0.1, 0.1)
    glScalef(0.3, 0.6, 0.05)
    glutSolidCube(15)
    glPopMatrix()
    
    glPopMatrix()

def draw_enemy_ship(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z)
    
    wave_offset = math.sin(water_time * wave_frequency + x * 0.01 + y * 0.01) * wave_amplitude
    glTranslatef(0, 0, wave_offset)
    glPushMatrix()
    glTranslatef(0, 0, 10)
    glColor3f(0.8, 0.1, 0.1)
    glScalef(1.5 * enemy_size_factor, 0.6 * enemy_size_factor, 0.4 * enemy_size_factor)
    glutSolidCube(35)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(0, 0, 22)
    glColor3f(0.6, 0.1, 0.1)
    glScalef(1.0 * enemy_size_factor, 0.4 * enemy_size_factor, 0.3 * enemy_size_factor)
    glutSolidCube(30)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(0, 0, 32)
    glColor3f(0.4, 0.1, 0.1)
    gluSphere(gluNewQuadric(), 12 * enemy_size_factor, 10, 10)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(10 * enemy_size_factor, 0, 25)
    glColor3f(0.3, 0.1, 0.1)
    gluCylinder(gluNewQuadric(), 8 * enemy_size_factor, 8 * enemy_size_factor, 10 * enemy_size_factor, 10, 1)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-10 * enemy_size_factor, 0, 28)
    glColor3f(0.2, 0.2, 0.2)
    gluCylinder(gluNewQuadric(), 4 * enemy_size_factor, 3 * enemy_size_factor, 15 * enemy_size_factor, 8, 1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(-10 * enemy_size_factor, 0, 45 * enemy_size_factor)
    glColor3f(0.5, 0.5, 0.5)
    gluSphere(gluNewQuadric(), 5 * enemy_size_factor, 6, 6)
    glPopMatrix()
    
    glPopMatrix()

def draw_missile(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z + 20)
    
    glColor3f(0.9, 0.9, 0.1)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 3, 3, 15, 8, 1)
    
    glTranslatef(0, 0, 15)
    glColor3f(1.0, 0.5, 0.0)
    glutSolidCone(3, 8, 8, 8)
    
    glPopMatrix()

def draw_enemy_missile(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z + 20)
    
    glColor3f(1.0, 0.2, 0.1)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 3, 3, 15, 8, 1)

    glTranslatef(0, 0, 15)
    glColor3f(0.8, 0.1, 0.0)
    glutSolidCone(3, 8, 8, 8)
    
    glPopMatrix()

def draw_ocean_grid():
    square_size = 60

    for i in range(-30, 30):
        for j in range(-30, 30):
            x_start = i * square_size
            y_start = j * square_size
            wave1 = math.sin(water_time * wave_frequency + x_start * 0.01) * wave_amplitude
            wave2 = math.sin(water_time * wave_frequency + (x_start + square_size) * 0.01) * wave_amplitude
            wave3 = math.sin(water_time * wave_frequency + y_start * 0.01) * wave_amplitude
            wave4 = math.sin(water_time * wave_frequency + (y_start + square_size) * 0.01) * wave_amplitude
            if (i + j) % 2 == 0:
                glColor3f(0.0, 0.4, 0.7)
            else:
                glColor3f(0.1, 0.5, 0.8) 
            glBegin(GL_QUADS)
            glVertex3f(x_start, y_start, wave1)
            glVertex3f(x_start + square_size, y_start, wave2)
            glVertex3f(x_start + square_size, y_start + square_size, wave4)
            glVertex3f(x_start, y_start + square_size, wave3)
            glEnd()
            if abs(wave1) > wave_amplitude * 0.7 or abs(wave2) > wave_amplitude * 0.7:
                glColor3f(0.7, 0.85, 0.95)
                glPointSize(2)
                glBegin(GL_POINTS)
                glVertex3f(x_start, y_start, wave1 + 1)
                glVertex3f(x_start + square_size, y_start, wave2 + 1)
                glEnd()

def draw_boundaries():
    far_distance = grid_length * 5
    sky_height = boundary_height * 4
    # Front
    glBegin(GL_QUADS)
    glColor3f(0.02, 0.02, 0.15)
    glVertex3f(-far_distance, far_distance, 0)
    glVertex3f(far_distance, far_distance, 0)
    glColor3f(0.0, 0.0, 0.05) 
    glVertex3f(far_distance, far_distance, sky_height)
    glVertex3f(-far_distance, far_distance, sky_height)
    glEnd()
    
    # Right
    glBegin(GL_QUADS)
    glColor3f(0.02, 0.02, 0.15)
    glVertex3f(far_distance, -far_distance, 0)
    glVertex3f(far_distance, far_distance, 0)
    glColor3f(0.0, 0.0, 0.05)
    glVertex3f(far_distance, far_distance, sky_height)
    glVertex3f(far_distance, -far_distance, sky_height)
    glEnd()
    
    # Back
    glBegin(GL_QUADS)
    glColor3f(0.02, 0.02, 0.15)
    glVertex3f(-far_distance, -far_distance, 0)
    glVertex3f(far_distance, -far_distance, 0)
    glColor3f(0.0, 0.0, 0.05)
    glVertex3f(far_distance, -far_distance, sky_height)
    glVertex3f(-far_distance, -far_distance, sky_height)
    glEnd()
    
    # Left
    glBegin(GL_QUADS)
    glColor3f(0.02, 0.02, 0.15)
    glVertex3f(-far_distance, -far_distance, 0)
    glVertex3f(-far_distance, far_distance, 0)
    glColor3f(0.0, 0.0, 0.05)
    glVertex3f(-far_distance, far_distance, sky_height)
    glVertex3f(-far_distance, -far_distance, sky_height)
    glEnd()
    
    glColor3f(1.0, 1.0, 1.0)
    glPointSize(2)
    glBegin(GL_POINTS)
    for i in range(50):
        star_x = (i * 123) % int(far_distance * 2) - far_distance
        star_y = (i * 456) % int(far_distance * 2) - far_distance
        star_z = boundary_height + (i * 78) % int(sky_height - boundary_height)
        glVertex3f(star_x, far_distance - 100, star_z)
        glVertex3f(star_x, -far_distance + 100, star_z)
        glVertex3f(far_distance - 100, star_y, star_z)
        glVertex3f(-far_distance + 100, star_y, star_z)
    glEnd()

def fire_missile():
    if not gameover:
        angle_rad = math.radians(p_angle)
        missile_x = p_pos[0] + 60 * math.cos(angle_rad)
        missile_y = p_pos[1] + 60 * math.sin(angle_rad)
        missile_z = p_pos[2]
        missiles.append([missile_x, missile_y, missile_z, p_angle])

def update_missiles():
    global missiles, missed, score, gameover
    missiles_to_remove = []
    
    for i, missile in enumerate(missiles):
        angle_rad = math.radians(missile[3])
        missile[0] += missile_speed * math.cos(angle_rad)
        missile[1] += missile_speed * math.sin(angle_rad)
        if (abs(missile[0]) > grid_length or abs(missile[1]) > grid_length):
            missiles_to_remove.append(i)
            if not cheat_mode:
                missed += 1
                if missed >= max_missed:
                    gameover = True
                    update_high_scores(score)
            continue
        for j, enemy in enumerate(enemies):
            distance = math.sqrt((missile[0] - enemy[0])**2 + (missile[1] - enemy[1])**2)
            if distance < 40:
                missiles_to_remove.append(i)
                score += 1
                respawn_enemy(j)
                break
    
    for i in sorted(missiles_to_remove, reverse=True):
        if i < len(missiles):
            missiles.pop(i)

def update_enemies():
    global p_life, gameover, enemy_size_factor, enemy_size_growing, enemy_fire_cooldown
    
    if gameover:
        return
    if enemy_size_growing:
        enemy_size_factor += 0.01
        if enemy_size_factor >= 1.2:
            enemy_size_growing = False
    else:
        enemy_size_factor -= 0.01
        if enemy_size_factor <= 0.8:
            enemy_size_growing = True

    enemy_fire_cooldown += 1

    for enemy in enemies:
        dx = p_pos[0] - enemy[0]
        dy = p_pos[1] - enemy[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            enemy[0] += (dx / distance) * enemy_speed
            enemy[1] += (dy / distance) * enemy_speed
    
        if enemy_fire_cooldown >= enemy_fire_rate and distance < 400:
            if dx == 0:
                if dy > 0:
                    fire_angle = 90
                else:
                    fire_angle = 270
            else:
                angle_rad = math.atan(dy / dx)
                fire_angle = math.degrees(angle_rad)
                if dx < 0:
                    fire_angle += 180
            angle_rad = math.radians(fire_angle)
            missile_x = enemy[0] + 40 * math.cos(angle_rad)
            missile_y = enemy[1] + 40 * math.sin(angle_rad)
            missile_z = enemy[2]
            enemy_missiles.append([missile_x, missile_y, missile_z, fire_angle])
        if distance < 50:
            p_life -= 1
            if p_life <= 0:
                gameover = True
                update_high_scores(score)
            respawn_enemy(enemies.index(enemy))
    if enemy_fire_cooldown >= enemy_fire_rate:
        enemy_fire_cooldown = 0

def update_enemy_missiles():
    global enemy_missiles, p_life, gameover
    missiles_to_remove = []
    
    for i, missile in enumerate(enemy_missiles):
        angle_rad = math.radians(missile[3])
        missile[0] += enemy_missile_speed * math.cos(angle_rad)
        missile[1] += enemy_missile_speed * math.sin(angle_rad)
        if (abs(missile[0]) > grid_length or abs(missile[1]) > grid_length):
            missiles_to_remove.append(i)
            continue
        distance = math.sqrt((missile[0] - p_pos[0])**2 + (missile[1] - p_pos[1])**2)
        if distance < 40:
            missiles_to_remove.append(i)
            p_life -= 1
            if p_life <= 0:
                gameover = True
                update_high_scores(score)
    for i in sorted(missiles_to_remove, reverse=True):
        if i < len(enemy_missiles):
            enemy_missiles.pop(i)

def update_cheat_mode():
    global p_angle, auto_rotation
    
    if cheat_mode and not gameover:
        auto_rotation += 1
        
        if len(enemies) > 0:
            # Find nearest enemy
            nearest_enemy = None
            min_distance = float('inf')
            
            for enemy in enemies:
                dx = enemy[0] - p_pos[0]
                dy = enemy[1] - p_pos[1]
                distance = math.sqrt(dx**2 + dy**2)
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_enemy = enemy
            
            if nearest_enemy:
                # Aim at nearest enemy
                dx = nearest_enemy[0] - p_pos[0]
                dy = nearest_enemy[1] - p_pos[1]
                
                if dx == 0:
                    if dy > 0:
                        p_angle = 90
                    else:
                        p_angle = 270
                else:
                    angle_rad = math.atan(dy / dx)
                    p_angle = math.degrees(angle_rad)
                    if dx < 0:
                        p_angle += 180
                
                # Auto-fire periodically
                if int(auto_rotation) % 30 == 0:
                    fire_missile()

def keyboardListener(key,x,y):
    global p_moving_forward, p_moving_backward, cheat_mode, cheat_vision, gameover, p_life, score, missed, missiles, p_alive, p_angle, difficulty
    if key==b'w' and not gameover:
        p_moving_forward = True
    if key==b's' and not gameover:
        p_moving_backward = True
    if key==b'a' and not gameover and not cheat_mode:
        p_angle+=5
    if key==b'd' and not gameover and not cheat_mode:
        p_angle-=5
    # cheat mode
    if key == b'c' and not gameover:
        cheat_mode=not cheat_mode
    # cheat
    if key == b'v' and cheat_mode and not gameover:
        cheat_vision=not cheat_vision
    # Reset
    if key==b'r':
        gameover=False
        p_life=5
        score=0
        missed=0
        p_pos[0]=0
        p_pos[1]=0
        p_pos[2]=0
        p_angle=0
        p_alive=True
        missiles.clear()
        enemy_missiles.clear()
        initialize_enemies()
        cheat_mode=False
        cheat_vision=False
        mines.clear()
        apply_difficulty()
    # Difficulty selection (only before game over)
    if key == b'1' and not gameover:
        difficulty = "EASY"
        apply_difficulty()
        initialize_enemies()

    if key == b'2'and not gameover:
        difficulty = "MEDIUM"
        apply_difficulty()
        initialize_enemies()

    if key == b'3' and not gameover:
        difficulty = "HARD"
        apply_difficulty()
        initialize_enemies()

    if key == b'm' and not gameover:
        drop_mine()

def keyboardUpListener(key, x, y):
    global p_moving_forward, p_moving_backward
    if key==b'w':
        p_moving_forward=False
    if key==b's':
        p_moving_backward=False

def update_player_movement():
    global p_pos
    if gameover:
        return
    if p_moving_forward:
        angle_rad=math.radians(p_angle)
        new_x=p_pos[0]+15*math.cos(angle_rad)
        new_y=p_pos[1]+15*math.sin(angle_rad)
        if abs(new_x)<grid_length-50 and abs(new_y)<grid_length-50:
            p_pos[0]=new_x
            p_pos[1]=new_y
    if p_moving_backward:
        angle_rad=math.radians(p_angle)
        new_x=p_pos[0]-15*math.cos(angle_rad)
        new_y=p_pos[1]-15*math.sin(angle_rad)
        if abs(new_x)<grid_length-50 and abs(new_y)<grid_length-50:
            p_pos[0]=new_x
            p_pos[1]= new_y

def specialKeyListener(key, x, y): # arrow keys
    global cam_angle, cam_height
    if key == GLUT_KEY_UP:
        cam_height += 10
        if cam_height > 800:
            cam_height = 800
    if key == GLUT_KEY_DOWN:
        cam_height -= 10
        if cam_height < 100:
            cam_height = 100
    if key == GLUT_KEY_LEFT:
        cam_angle += 5
    if key==GLUT_KEY_RIGHT:
        cam_angle-=5
def mouseListener(button,state,x,y):
    global cam_mode
    if button==GLUT_LEFT_BUTTON and state==GLUT_DOWN:
        if not gameover and not cheat_mode:
            fire_missile()
    if button==GLUT_RIGHT_BUTTON and state==GLUT_DOWN:
        if cam_mode=="third_person":
            cam_mode="first_person"
        else:
            cam_mode="third_person"
def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    if cam_mode=="first_person" or (cheat_vision and cheat_mode):
        # First person view from ship
        angle_rad =math.radians(p_angle)
        cam_x=p_pos[0]-80 *math.cos(angle_rad)
        cam_y=p_pos[1]-80 *math.sin(angle_rad)
        cam_z=p_pos[2]+200
        look_x=p_pos[0]+300 *math.cos(angle_rad)
        look_y=p_pos[1]+300 *math.sin(angle_rad)
        look_z=p_pos[2]
        gluLookAt(cam_x, cam_y, cam_z,
                  look_x, look_y, look_z,
                  0, 0, 1)
    else:
        # Third person view
        angle_rad=math.radians(cam_angle)
        radius=700
        cam_x=radius*math.cos(angle_rad)
        cam_y=radius*math.sin(angle_rad)
        cam_z=cam_height
        gluLookAt(cam_x,cam_y,cam_z,
                  0,0,0,
                  0,0,1)
def idle():
    global water_time
    water_time+=1
    update_player_movement()
    update_missiles()
    update_enemy_missiles()
    update_enemies()
    update_cheat_mode()
    update_mines()
    glutPostRedisplay()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0,0,1000,800)
    setupCamera()
    draw_ocean_grid()
    draw_boundaries()
    draw_battleship()
    
    for enemy in enemies:
        draw_enemy_ship(enemy[0],enemy[1],enemy[2])

    for missile in missiles:
        draw_missile(missile[0],missile[1],missile[2])
    
    for missile in enemy_missiles:
        draw_enemy_missile(missile[0],missile[1],missile[2])

    for mine in mines:
        draw_mine(mine[0], mine[1], mine[2])
        
    draw_text(10,770,f"Life Remaining: {p_life}")
    draw_text(10,740,f"Ships Destroyed: {score}")
    draw_text(10,710,f"Missiles Missed: {missed}")
    if high_scores:
        draw_text(10, 680, f"High Score: {high_scores[0]}")
    draw_text(10, 650, f"Difficulty: {difficulty}")

    if gameover:
        draw_text(350,400,"BATTLESHIP SUNK! Press R to Restart",GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(380, 360, "HIGH SCORES")
        y = 330
        for i, s in enumerate(high_scores):
            draw_text(380, y, f"{i+1}. {s}")
            y -= 25
    if cheat_mode:
        draw_text(10,680,"AUTO-AIM ENGAGED")
    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    wind = glutCreateWindow(b"Battleship - 3D Naval Combat")

    glEnable(GL_DEPTH_TEST)
    apply_difficulty()
    initialize_enemies()

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    load_high_scores()
    glutMainLoop()

if __name__ == "__main__":
    main()
