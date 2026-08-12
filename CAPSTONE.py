from machine import Pin, I2C, ADC
import time
import random
from ssd1306 import SSD1306_I2C
from ir_rx.nec import NEC_8
from ir_rx.print_error import print_error

i2c_left = I2C(0, scl=Pin(13), sda=Pin(12), freq=400000)
i2c_right = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled_left = SSD1306_I2C(128, 64, i2c_left)
oled_right = SSD1306_I2C(128, 64, i2c_right)
joystick = ADC(27)
ir_pin = Pin(17, Pin.IN)

ir_button = None

def ir_callback(data, addr, ctrl):

    global ir_button

    if data >= 0:
        ir_button = data

def read_ir():
    global ir_button
    
    last_value = ir_button

    ir_button = None
    return last_value

ir = NEC_8(ir_pin, ir_callback)
#ir.error_function(print_error)

MODE = 0x46
OK = 0x45
PLUS = 0x09
MINUS = 0x15
WIDTH = 256
HEIGHT = 64
PADDLE_HEIGHT = 12
PADDLE_WIDTH = 2
BALL_SIZE = 2

game_started = False
ai_mode = False
winner = 0
score1 = 0
score2 = 0
paddle1_y = 26
paddle2_y = 26
ball_x = 128
ball_y = 32
ball_dx = 1
ball_dy = 1

def clear_displays():
    oled_left.fill(0)
    oled_right.fill(0)
    
def draw_pixel(x, y):
    if x < 0 or x >= WIDTH:
        return

    if y < 0 or y >= HEIGHT:
        return

    if x < 128:
        oled_left.pixel(x, y, 1)

    else:
        oled_right.pixel(x - 128, y, 1)
        
def draw_rect(x, y, w, h):
    for yy in range(y, y+h):
        for xx in range(x, x+w):
            draw_pixel(xx, yy)
            
def draw_text(x, y, text):
    if x < 128:
        oled_left.text(text, x, y, 1)

    else:
        oled_right.text(text, x-128, y, 1)
        
def show():
    oled_left.show()
    oled_right.show()

# -----------------------------
# DRAW FULL PLAYFIELD
# -----------------------------
def draw_field():
    clear_displays()
    # middle line
    for y in range(0,64,4):
        draw_pixel(128, y)
        draw_pixel(127, y)

    # paddles
    draw_rect(4, paddle1_y, PADDLE_WIDTH, PADDLE_HEIGHT)

    draw_rect(250, paddle2_y, PADDLE_WIDTH, PADDLE_HEIGHT)
    # ball
    draw_rect(ball_x, ball_y, BALL_SIZE, BALL_SIZE)

    # scores
    draw_text(55, 0, str(score1))
    draw_text(183, 0, str(score2))
    show()


# -----------------------------
# INPUT FUNCTIONS
# -----------------------------


def read_joystick():
    value = joystick.read_u16()
    # joystick centered around ~32768
    if value < 20000:
        return -1

    if value > 45000:
        return 1
    
    return 0

# -----------------------------
# PADDLE CONTROL
# -----------------------------
def move_paddle1():
    global paddle1_y

    direction = read_joystick()
    paddle1_y += direction * 5

    if paddle1_y < 0:
        paddle1_y = 0

    if paddle1_y > HEIGHT - PADDLE_HEIGHT:
        paddle1_y = HEIGHT - PADDLE_HEIGHT
        
        
def move_paddle2_manual():
    #print("move_paddle2_manual() was called")
    global paddle2_y
    code = read_ir()
    #if code is not None:
        #print(f"From paddle2_manual: {code}")
    #if code is None:
     #   return
    
    if code == PLUS:

        #print("Plus detected!")
        paddle2_y -= 5

    elif code == MINUS:

        #print("Minus detected!")
        paddle2_y += 5

    if paddle2_y < 0:
        paddle2_y = 0

    if paddle2_y > HEIGHT - PADDLE_HEIGHT:
        paddle2_y = HEIGHT - PADDLE_HEIGHT
        
    #time.sleep(0.03)
        
# -----------------------------
# AI PADDLE
# -----------------------------
def move_paddle2_ai():

    global paddle2_y

    target = ball_y - (PADDLE_HEIGHT // 2)
    
    if paddle2_y < target:
        paddle2_y += 2

    elif paddle2_y > target:
        paddle2_y -= 2

    if paddle2_y < 0:
        paddle2_y = 0

    if paddle2_y > HEIGHT - PADDLE_HEIGHT:
        paddle2_y = HEIGHT - PADDLE_HEIGHT
# -----------------------------
# MENU SCREEN
# -----------------------------
def draw_menu():

    clear_displays()
    draw_text(50, 9, "PING")
    draw_text(178, 9, "PONG")

    if ai_mode:
        draw_text(5, 30, "VS BOT")
        
    else:
        draw_text(5, 30, "VS PLAYER")
        
    draw_text(5, 50, "POWER TO START")
    draw_text(130, 30, "'MODE' TO CHANGE")
    draw_text(130, 50, "GAMEMODE (P2/AI)")

    show()
    
def menu():

    global ai_mode
    global game_started

    draw_menu()

    while not game_started:

        code = read_ir()
    
        if code == MODE:
            #print("MODE matched!")
            ai_mode = not ai_mode
            draw_menu()

        elif code == OK:
            #print("OK matched!")
            game_started = True
            
        time.sleep(1)
        
        # -----------------------------
# BALL FUNCTIONS
# -----------------------------

def reset_ball():

    global ball_x
    global ball_y
    global ball_dx
    global ball_dy
    
    ball_x = 128
    ball_y = 32

    ball_dx = random.choice([-1, 1])
    ball_dy = random.choice([-1, 1])

def reset_game():

    global score1
    global score2
    global paddle1_y
    global paddle2_y
    global winner

    score1 = 0
    score2 = 0
    paddle1_y = 26
    paddle2_y = 26
    winner = 0
    reset_ball()
# -----------------------------
# BALL COLLISION
# -----------------------------
def move_ball():

    global ball_x
    global ball_y
    global ball_dx
    global ball_dy

    ball_x += ball_dx * 2
    ball_y += ball_dy * 2
    # Top and bottom walls

    if ball_y <= 0:
        ball_y = 0
        ball_dy *= -1

    if ball_y >= HEIGHT - BALL_SIZE:
        ball_y = HEIGHT - BALL_SIZE
        ball_dy *= -1
    # Player 1 paddle

    if ball_x <= 6:
        if (paddle1_y <= ball_y <= paddle1_y + PADDLE_HEIGHT):
            ball_x = 6
            ball_dx *= -1

    # Player 2 paddle
    if ball_x >= 246:
        if (paddle2_y <= ball_y <= paddle2_y + PADDLE_HEIGHT):

            ball_x = 246
            ball_dx *= -1
# -----------------------------
# SCORE HANDLING
# -----------------------------
def check_score():

    global score1
    global score2
    global winner

    if ball_x < 0:
        score2 += 1
        reset_ball()
        
    if ball_x > WIDTH:
        score1 += 1
        reset_ball()

    if score1 >= 5:
        winner = 1
    if score2 >= 5:
        winner = 2
# -----------------------------
# WIN SCREEN
# -----------------------------
def draw_winner():
    clear_displays()
    if winner == 1:
        draw_text(20, 25, "P1 WINS")
        
    else:
        draw_text(150, 25, "P2 WINS")

    show()
    

# -----------------------------
# MAIN GAME LOOP
# -----------------------------

def main():
    global game_started

    while True:        
        game_started = False
        menu()
        reset_game()
        
        while game_started and winner == 0:

            # Player 1
            move_paddle1()
            
            # Player 2
            if ai_mode:
                move_paddle2_ai()
                x = 0.01
            else:
                move_paddle2_manual()
                x = 0.15

            move_ball()
            check_score()
            draw_field()
            time.sleep(x)
            
        if winner != 0:
            draw_winner()
            time.sleep(5)
            reset_game()
            game_started = False

if __name__ == "__main__":
    main()
