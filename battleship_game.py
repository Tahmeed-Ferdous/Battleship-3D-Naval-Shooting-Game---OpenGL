from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math
cam_pos=[0,500,500]
cam_angle=0 
cam_height=500
cam_mode="third_person"
p_pos=[0,0,0]
p_angle=0
p_life=5
p_alive=True
p_moving_forward=False
p_moving_backward=False 
score=0
missed=0
gameover=False
missiles=[]
missile_speed=10  
enemy_missiles=[]
enemy_fire_cooldown=0
enemies=[] 
enemy_size_factor=1.0
enemy_size_growing=True
cheat_mode=False
cheat_vision=False
auto_rotation=0
fovY=80
grid_length=600
boundary_height=100
water_time=0
wave_amplitude=3
wave_frequency=0.05
HIGH_SCORE_FILE="highscores.txt"
TOP_N=5
high_scores=[]
difficulty="MEDIUM"
DIFFICULTY_SETTINGS={
    "EASY":{
        "enemy_count":3,
        "enemy_speed":0.06,
        "enemy_fire_rate":120,
        "enemy_missile_speed":2,
        "max_missed":15
    },
    "MEDIUM":{
        "enemy_count":5,
        "enemy_speed":0.1,
        "enemy_fire_rate":80,
        "enemy_missile_speed":3,
        "max_missed":10
    },
    "HARD":{
        "enemy_count":8,
        "enemy_speed":0.18,
        "enemy_fire_rate":50,
        "enemy_missile_speed":4,
        "max_missed":6
    }
}

mines=[]  
mine_radius=150  
max_mines=5
current_mines=0
drones=[] 
drone_speed=8
drone_radius=25  
MAX_DRONES=1
wind_active=False
wind_radius=0
WIND_SPREAD_ANGLE=60 
WIND_PUSH_STRENGTH=10
WIND_MAX_RADIUS=400  
WIND_EXPAND_SPEED=3.0  
bonus_pts=[]
life_pts=[]
max_bonus=1
max_life=1
bonus_rad=30
life_rad=30
bonus_delay=0
life_delay=0
bonus_delay_time=300
life_delay_time=300
inv_pts=[]
max_inv=1
inv_rad=30
inv_delay=0
inv_delay_time=1200
inv_active=False
inv_timer=0
inv_duration=280
fire_times=[]
oheat=False
oheat_timer=0
oheat_duration=180
oheat_threshold=180
fuel=10.0
fuel_max=10.0
fuel_consume=0.5
fuel_regen=0.10
fuel_delay=0
fuel_delay_time=120
def draw_wind():
    global wind_radius,wind_active
    if not wind_active:
        return
    glPushMatrix()
    glTranslatef(p_pos[0],p_pos[1],p_pos[2]+15)
    glRotatef(p_angle,0,0,1)
    segments=120
    arc_angle=WIND_SPREAD_ANGLE
    trail_count=60  
    ease_factor=1-(wind_radius/WIND_MAX_RADIUS)
    current_speed=WIND_EXPAND_SPEED*(0.5+0.5*ease_factor)
    for layer in range(3):
        layer_radius=wind_radius-layer*4
        layer_opacity=max(0.0,0.5*(1-layer/3)*(1-wind_radius/WIND_MAX_RADIUS))
        glLineWidth(1.5)
        glBegin(GL_LINE_STRIP)
        for i in range(segments+1):
            angle=math.radians(-arc_angle/2+i*(arc_angle/segments))
            twist=2*math.sin(i*8+water_time*0.3+layer)
            x=(layer_radius+twist)*math.cos(angle)
            y=(layer_radius+twist)*math.sin(angle)
            z=4*math.sin(i/segments*math.pi+water_time*0.2)+layer*1.2
            glColor4f(0.75+0.05*layer,0.8+0.05*layer,1.0,layer_opacity)
            glVertex3f(x,y,z)
        glEnd()
    for _ in range(trail_count):
        angle_offset=math.radians(random.uniform(-arc_angle/2,arc_angle/2))
        radius_offset=random.uniform(max(0,wind_radius-80),wind_radius)
        z_offset=random.uniform(0,8)
        length=random.uniform(30,60)
        glColor4f(0.8,0.85,1.0,0.2)
        glBegin(GL_LINES)
        glVertex3f(radius_offset*math.cos(angle_offset),
                   radius_offset*math.sin(angle_offset),
                   z_offset)
        glVertex3f((radius_offset-length)*math.cos(angle_offset),
                   (radius_offset-length)*math.sin(angle_offset),
                   z_offset+random.uniform(0,5))
        glEnd()
    for layer in range(2):
        offset_radius=wind_radius-8-layer*4
        glLineWidth(1.0)
        glBegin(GL_LINE_STRIP)
        for i in range(segments+1):
            angle=math.radians(-arc_angle/2+i*(arc_angle/segments))
            x=(offset_radius+2*math.sin(i*6+water_time*0.25))*math.cos(angle)
            y=(offset_radius+2*math.sin(i*6+water_time*0.25))*math.sin(angle)
            z=1.5*layer+2*math.sin(i/segments*math.pi+water_time*0.15)
            opacity=max(0.0,0.25*(1-wind_radius/WIND_MAX_RADIUS))
            glColor4f(0.7,0.75,1.0,opacity)
            glVertex3f(x,y,z)
        glEnd()
    glPopMatrix()
    wind_radius+=current_speed
    if wind_radius>WIND_MAX_RADIUS:
        wind_active=False
        wind_radius=0
def spawn_drone():
    global drones
    if gameover:
        return
    angle_rad=math.radians(p_angle)
    drone_x=p_pos[0]+50*math.cos(angle_rad)  
    drone_y=p_pos[1]+50*math.sin(angle_rad)
    drone_z=p_pos[2]+10  
    if len(drones)<MAX_DRONES:
        drones.append([drone_x,drone_y,drone_z])
def update_drones():
    global drones,score
    drones_to_remove=[]
    for i,drone in enumerate(drones):
        if not enemies:
            continue
        nearest_enemy=min(enemies,key=lambda e:math.sqrt((e[0]-drone[0])**2+(e[1]-drone[1])**2))
        dx=nearest_enemy[0]-drone[0]
        dy=nearest_enemy[1]-drone[1]
        distance=math.sqrt(dx**2+dy**2)
        if distance>0:
            drone[0]+=(dx/distance)*drone_speed
            drone[1]+=(dy/distance)*drone_speed
        if distance<drone_radius:
            score+=1
            respawn_enemy(enemies.index(nearest_enemy))
            drones_to_remove.append(i)
    for i in sorted(drones_to_remove,reverse=True):
        drones.pop(i)
def draw_drone(x,y,z,rotation_angle=0,time=0):
    glPushMatrix()
    glTranslatef(x,y,z)
    quad=gluNewQuadric()
    glPushMatrix()
    glow=0.05*math.sin(time*0.3)
    glColor3f(0.9+glow,0.85+glow,0.2) 
    glutSolidSphere(10,20,20)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0,0,10)
    glColor3f(0.75,0.75,0.75)  
    glRotatef(-90,1,0,0)
    gluCylinder(quad,5,0,10,12,1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0,-4,6)
    glow=0.4+0.4*math.sin(time*0.4)
    glColor3f(0.2,0.8+glow*0.2,0.9)
    glutSolidSphere(3,10,10)
    glTranslatef(0,0,-2)
    glColor3f(0.15,0.15,0.15)
    gluCylinder(quad,0.5,0.5,4,8,1)
    glPopMatrix()
    for angle in [20,-20]:
        glPushMatrix()
        glTranslatef(0,0,-12)
        glRotatef(angle,1,0,0)
        glColor3f(0.7,0.7,0.7)
        glScalef(0.5,0.5,1.5)
        glutSolidCube(8)
        glPopMatrix()
    for angle in [45,-45]:
        glPushMatrix()
        glRotatef(angle,0,0,1)
        glTranslatef(7,0,-3)
        glColor3f(0.6,0.6,0.6)
        glScalef(0.3,1.5,0.5)
        glutSolidCube(6)
        glPopMatrix()
    for angle in [0,90,180,270]:
        glPushMatrix()
        glRotatef(angle,0,0,1)
        glTranslatef(12,0,0)
        glColor3f(0.25,0.25,0.25)
        gluCylinder(quad,1,1,12,8,1)
        glTranslatef(12,0,0)
        glRotatef(rotation_angle,1,0,0)
        glColor3f(0.1,0.1,0.1)
        glutSolidSphere(1.5,10,10)
        for blade_angle in [0,45,90,135]:
            glPushMatrix()
            glRotatef(blade_angle,0,0,1)
            glTranslatef(2,0,0)
            glScalef(1,0.1,0.1)
            glColor3f(0.15,0.15,0.15)
            glutSolidCube(4)
            glPopMatrix()
        glPushMatrix()
        glTranslatef(2, 0, 0)
        if angle % 180 == 0:
            glColor3f(1.0, 0.2, 0.2)  
        else:
            glColor3f(0.2, 1.0, 0.2)
        glutSolidSphere(1.2, 8, 8)
        glPopMatrix()
        glPopMatrix()
    for side in [-1, 1]:
        glPushMatrix()
        glTranslatef(side * 4, -2, -10)
        glColor3f(0.2, 0.2, 0.2)
        gluCylinder(quad, 0.8, 0.8, 5, 8, 1)
        glPopMatrix()
    glPopMatrix()

def drop_mine():
    global mines, current_mines  
    if not gameover and current_mines < max_mines:
        angle_rad = math.radians(p_angle)
        mine_x = p_pos[0] + 50 * math.cos(angle_rad)
        mine_y = p_pos[1] + 50 * math.sin(angle_rad)
        mine_z = p_pos[2]
        mines.append([mine_x, mine_y, mine_z])
        current_mines += 1 

def update_mines():
    global mines, score, current_mines  
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
            current_mines -= 1 


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

# SHAKIB
def spawn_bonus_pt():
    if len(bonus_pts) < max_bonus:
        x = random.uniform(-grid_length + 150, grid_length - 150)
        y = random.uniform(-grid_length + 150, grid_length - 150)
        bonus_pts.append([x, y, 0])

def spawn_life_pt():
    if len(life_pts) < max_life:
        x = random.uniform(-grid_length + 150, grid_length - 150)
        y = random.uniform(-grid_length + 150, grid_length - 150)
        life_pts.append([x, y, 0])

def draw_bonus_pt(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z + 20)
    
    rot = water_time * 3 % 360
    glRotatef(rot, 0, 0, 1)
    
    glow = 0.2 * math.sin(water_time * 0.1)
    glColor3f(1.0, 0.8 + glow, 0.0)
    glutSolidCube(25)
    
    glRotatef(45, 0, 0, 1)
    glColor3f(1.0, 0.9, 0.2)
    glutSolidCube(20)
    
    glColor3f(1.0, 1.0, 0.5)
    gluSphere(gluNewQuadric(), 15, 10, 10)
    
    glPopMatrix()

def draw_life_pt(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z + 20)
    
    bob = 5 * math.sin(water_time * 0.08)
    glTranslatef(0, 0, bob)
    
    glRotatef(water_time * 2 % 360, 0, 0, 1)
    
    glow = 0.3 * math.sin(water_time * 0.12)
    glColor3f(1.0, 0.1 + glow, 0.1 + glow)
    glutSolidSphere(18, 15, 15)
    
    for ang in [0, 90, 180, 270]:
        glPushMatrix()
        glRotatef(ang, 0, 0, 1)
        glTranslatef(12, 0, 0)
        glColor3f(0.9, 0.0, 0.0)
        glutSolidCube(10)
        glPopMatrix()
    
    glColor3f(1.0, 0.5, 0.5)
    glRotatef(45, 1, 0, 0)
    glutSolidTorus(3, 10, 8, 12)
    
    glPopMatrix()

def update_bonus_pts():
    global bonus_pts, score, bonus_delay
    pts_remove = []
    
    if bonus_delay > 0:
        bonus_delay -= 1
        if bonus_delay == 0 and len(bonus_pts) == 0:
            spawn_bonus_pt()
    
    for i, pt in enumerate(bonus_pts):
        dist = math.sqrt((pt[0] - p_pos[0])**2 + (pt[1] - p_pos[1])**2)
        if dist < bonus_rad:
            score += 1
            pts_remove.append(i)
    
    for i in sorted(pts_remove, reverse=True):
        bonus_pts.pop(i)
        bonus_delay = bonus_delay_time

def update_life_pts():
    global life_pts, p_life, life_delay
    pts_remove = []
    
    if life_delay > 0:
        life_delay -= 1
        if life_delay == 0 and len(life_pts) == 0:
            spawn_life_pt()
    
    for i, pt in enumerate(life_pts):
        dist = math.sqrt((pt[0] - p_pos[0])**2 + (pt[1] - p_pos[1])**2)
        if dist < life_rad:
            p_life += 1
            pts_remove.append(i)
    
    for i in sorted(pts_remove, reverse=True):
        life_pts.pop(i)
        life_delay = life_delay_time

def spawn_inv_pt():
    if len(inv_pts) < max_inv:
        x = random.uniform(-grid_length + 150, grid_length - 150)
        y = random.uniform(-grid_length + 150, grid_length - 150)
        inv_pts.append([x, y, 0])

def draw_inv_pt(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z + 25)
    
    pulse = 5 * math.sin(water_time * 0.15)
    glTranslatef(0, 0, pulse)
    
    glRotatef(water_time * 4 % 360, 0, 0, 1)
    glRotatef(water_time * 2 % 360, 1, 0, 0)
    
    glow = 0.4 * math.sin(water_time * 0.2)
    glColor3f(0.5 + glow, 0.9 + glow*0.5, 1.0)
    glutSolidSphere(20, 20, 20)
    
    glColor3f(0.8, 1.0, 1.0)
    glutSolidTorus(3, 25, 12, 16)
    
    glRotatef(90, 1, 0, 0)
    glColor3f(0.6, 0.95, 1.0)
    glutSolidTorus(3, 25, 12, 16)
    
    for i in range(4):
        glPushMatrix()
        glRotatef(i * 90, 0, 0, 1)
        glTranslatef(15, 0, 0)
        glColor3f(0.9, 1.0, 1.0)
        glutSolidCube(8)
        glPopMatrix()
    
    glPopMatrix()

def update_inv_pts():
    global inv_pts, inv_delay, inv_active, inv_timer
    pts_remove = []
    
    if inv_delay > 0:
        inv_delay -= 1
        if inv_delay == 0 and len(inv_pts) == 0:
            spawn_inv_pt()
    
    for i, pt in enumerate(inv_pts):
        dist = math.sqrt((pt[0] - p_pos[0])**2 + (pt[1] - p_pos[1])**2)
        if dist < inv_rad:
            inv_active = True
            inv_timer = inv_duration
            pts_remove.append(i)
    
    for i in sorted(pts_remove, reverse=True):
        inv_pts.pop(i)
        inv_delay = inv_delay_time
    
    if inv_active:
        inv_timer -= 1
        if inv_timer <= 0:
            inv_active = False
            inv_timer = 0
# SHAKIB

def check_oheat():
    global fire_times, oheat, oheat_timer
    if len(fire_times) >= 5:
        time_diff = water_time - fire_times[0]
        if time_diff <= oheat_threshold:
            oheat = True
            oheat_timer = oheat_duration
            fire_times.clear()

def update_oheat():
    global oheat, oheat_timer, fire_times
    # SHAKIB
    if cheat_mode:
        oheat = False
        oheat_timer = 0
        fire_times = []
        return
    # SHAKIB
    if oheat:
        oheat_timer -= 1
        if oheat_timer <= 0:
            oheat = False
            oheat_timer = 0
    
    curr = water_time
    fire_times = [t for t in fire_times if curr - t <= oheat_threshold]

def draw_oheat_indicator():
    if not oheat:
        return
    
    remain = oheat_timer / float(oheat_duration)
    pulse = 0.3 * math.sin(water_time * 0.2)
    
    glColor3f(1.0, 0.0 + pulse, 0.0)
    draw_text(400, 500, "OVERHEATED!", GLUT_BITMAP_TIMES_ROMAN_24)
    
    bar_w = 200
    bar_h = 20
    bar_x = 400
    bar_y = 460
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glColor3f(0.3, 0.0, 0.0)
    glBegin(GL_QUADS)
    glVertex2f(bar_x, bar_y)
    glVertex2f(bar_x + bar_w, bar_y)
    glVertex2f(bar_x + bar_w, bar_y + bar_h)
    glVertex2f(bar_x, bar_y + bar_h)
    glEnd()
    
    glColor3f(1.0, 0.2, 0.0)
    glBegin(GL_QUADS)
    glVertex2f(bar_x, bar_y)
    glVertex2f(bar_x + bar_w * remain, bar_y)
    glVertex2f(bar_x + bar_w * remain, bar_y + bar_h)
    glVertex2f(bar_x, bar_y + bar_h)
    glEnd()
    
    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(2)
    glBegin(GL_LINE_LOOP)
    glVertex2f(bar_x, bar_y)
    glVertex2f(bar_x + bar_w, bar_y)
    glVertex2f(bar_x + bar_w, bar_y + bar_h)
    glVertex2f(bar_x, bar_y + bar_h)
    glEnd()
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def update_fuel():
    global fuel, fuel_delay
    if fuel_delay > 0:
        fuel_delay -= 1
        return
    
    if not p_moving_forward and not p_moving_backward:
        fuel += fuel_regen
        if fuel > fuel_max:
            fuel = fuel_max
# SHAKIB

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
    # SHAKIB
    if inv_active and (water_time % 10 < 5):
        return
    # SHAKIB
    
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
    # SHAKIB
    if oheat and not cheat_mode:
        return
    # SHAKIB
    if not gameover:
        angle_rad = math.radians(p_angle)
        missile_x = p_pos[0] + 60 * math.cos(angle_rad)
        missile_y = p_pos[1] + 60 * math.sin(angle_rad)
        missile_z = p_pos[2]
        missiles.append([missile_x, missile_y, missile_z, p_angle])
        # SHAKIB
        if not cheat_mode:
            fire_times.append(water_time)
            check_oheat()
        # SHAKIB

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
    global wind_active, wind_radius
    if wind_active:
        wind_radius += 10 
        for enemy in enemies:
            dx = enemy[0] - p_pos[0]
            dy = enemy[1] - p_pos[1]
            distance = math.sqrt(dx**2 + dy**2)
            if distance < wind_radius:
                angle_to_enemy = math.degrees(math.atan2(dy, dx))
                angle_diff = (angle_to_enemy - p_angle + 360) % 360
                if angle_diff > 180:
                    angle_diff -= 360
                if abs(angle_diff) < WIND_SPREAD_ANGLE/2:
                    angle_rad = math.radians(p_angle)
                    enemy[0] += math.cos(angle_rad) * WIND_PUSH_STRENGTH
                    enemy[1] += math.sin(angle_rad) * WIND_PUSH_STRENGTH

        if wind_radius > WIND_MAX_RADIUS:
            wind_active = False  

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
            # SHAKIB
            if not inv_active:
                p_life -= 1
                if p_life <= 0:
                    gameover = True
                    update_high_scores(score)
            # SHAKIB
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
            # SHAKIB
            if not inv_active:
                p_life -= 1
                if p_life <= 0:
                    gameover = True
                    update_high_scores(score)
            # SHAKIB
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
    global p_moving_forward, p_moving_backward, cheat_mode, cheat_vision, gameover, p_life, score, missed, missiles, p_alive, p_angle
    global difficulty, max_mines, current_mines 
    global wind_active, wind_radius
    # SHAKIB
    global fire_times, oheat, oheat_timer, fuel, fuel_delay
    # SHAKIB 

    if key==b'w' and not gameover and not cheat_mode:
        p_moving_forward = True
    if key==b's' and not gameover and not cheat_mode:
        p_moving_backward = True
    if key==b'a' and not gameover and not cheat_mode:
        p_angle+=5
    if key==b'd' and not gameover and not cheat_mode:
        p_angle-=5
    # cheat mode
    if key == b'c' and not gameover:
        # SHAKIB - Clear overheat when toggling cheat mode
        oheat = False
        oheat_timer = 0
        fire_times = []
        # SHAKIB
        cheat_mode=not cheat_mode
        # SHAKIB
        if cheat_mode:
            fuel = fuel_max
            fuel_delay = 0
        # SHAKIB
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
        max_mines = 5
        current_mines = 0
        drones.clear()
        mines.clear()
        # SHAKIB
        bonus_pts.clear()
        life_pts.clear()
        inv_pts.clear()
        bonus_delay = 0
        life_delay = 0
        inv_delay = 0
        inv_active = False
        inv_timer = 0
        # SHAKIB
        fire_times = []
        oheat = False
        oheat_timer = 0
        fuel = 10.0
        fuel_delay = 0
        # SHAKIB
        for i in range(max_bonus):
            spawn_bonus_pt()
        for i in range(max_life):
            spawn_life_pt()
        for i in range(max_inv):
            spawn_inv_pt()
        # SHAKIB
        apply_difficulty()

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

    if key == b'n' and not gameover:
        spawn_drone()

    if key == b'b' and not gameover:
        if not wind_active:
            wind_active = True
            wind_radius = 0  

def keyboardUpListener(key, x, y):
    global p_moving_forward, p_moving_backward
    if key==b'w':
        p_moving_forward=False
    if key==b's':
        p_moving_backward=False

def update_player_movement():
    global p_pos, fuel, fuel_delay
    if gameover:
        return
    if p_moving_forward:
        # SHAKIB
        if fuel <= 0 and not cheat_mode:
            return
        # SHAKIB
        angle_rad=math.radians(p_angle)
        new_x=p_pos[0]+15*math.cos(angle_rad)
        new_y=p_pos[1]+15*math.sin(angle_rad)
        if abs(new_x)<grid_length-50 and abs(new_y)<grid_length-50:
            p_pos[0]=new_x
            p_pos[1]=new_y
            # SHAKIB
            if not cheat_mode:
                fuel -= fuel_consume
                if fuel <= 0:
                    fuel = 0
                    fuel_delay = fuel_delay_time
            # SHAKIB
    if p_moving_backward:
        # SHAKIB
        if fuel <= 0 and not cheat_mode:
            return
        # SHAKIB
        angle_rad=math.radians(p_angle)
        new_x=p_pos[0]-15*math.cos(angle_rad)
        new_y=p_pos[1]-15*math.sin(angle_rad)
        if abs(new_x)<grid_length-50 and abs(new_y)<grid_length-50:
            p_pos[0]=new_x
            p_pos[1]= new_y
            # SHAKIB
            if not cheat_mode:
                fuel -= fuel_consume
                if fuel <= 0:
                    fuel = 0
                    fuel_delay = fuel_delay_time
            # SHAKIB

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
    update_drones()
    # SHAKIB
    update_bonus_pts()
    update_life_pts()
    update_inv_pts()
    update_oheat()
    update_fuel()
    # SHAKIB
    glutPostRedisplay()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0,0,1000,800)
    setupCamera()
    draw_ocean_grid()
    draw_boundaries()
    draw_battleship()
    draw_wind()

    for enemy in enemies:
        draw_enemy_ship(enemy[0],enemy[1],enemy[2])

    for missile in missiles:
        draw_missile(missile[0],missile[1],missile[2])
    
    for missile in enemy_missiles:
        draw_enemy_missile(missile[0],missile[1],missile[2])

    for mine in mines:
        draw_mine(mine[0],mine[1],mine[2])
    for drone in drones:
        draw_drone(drone[0],drone[1],drone[2])
    # SHAKIB
    for pt in bonus_pts:
        draw_bonus_pt(pt[0], pt[1], pt[2])
    for pt in life_pts:
        draw_life_pt(pt[0],pt[1],pt[2])
    for pt in inv_pts:
        draw_inv_pt(pt[0],pt[1],pt[2])
    # SHAKIB
   
    draw_text(10,770,f"Life Remaining: {p_life}")
    draw_text(10,740,f"Ships Destroyed: {score}")
    draw_text(10,710,f"Missiles Missed: {missed}")
    draw_text(10,680,f"Mines Remaining: {max_mines - current_mines}")
    draw_text(10,650,f"Drones Remaining: {MAX_DRONES - len(drones)}")
    draw_text(10, 620, f"Difficulty: {difficulty}")
    # SHAKIB
    draw_text(10, 590, f"Fuel: {int(fuel)}")
    # SHAKIB  

    if gameover:
        draw_text(350,400,"BATTLESHIP SUNK! Press R to Restart", GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(350, 360, "HIGH SCORES")
        y = 330
        for i, s in enumerate(high_scores):
            draw_text(350, y, f"{i+1}. {s}")
            y -= 25
    if cheat_mode:
        draw_text(10,560,"AUTO-AIM ENGAGED")
    # SHAKIB
    draw_oheat_indicator()
    # SHAKIB
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
    # SHAKIB
    for i in range(max_bonus):
        spawn_bonus_pt()
    for i in range(max_life):
        spawn_life_pt()
    for i in range(max_inv):
        spawn_inv_pt()
    # SHAKIB

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
