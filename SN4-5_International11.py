import pyb, sensor, time, math, re
from machine import UART
from pyb import LED


# Which robot in use and on which side of the field?
robot = "SN5"
goal_defendu = "bleu"
detection_de_ligne = True

# Variables with specific values depending on the robot
if robot == "SN4":
    offset_x = 170
    offset_y = 129
    Min = 22
    zone_capture = 3

    Kick_duration = 15
    Goal_kick_distance = 100
    goal_defending_distance = 90

    speed_threshold = 1.5
    original_speed_threshold = speed_threshold
    rotation_threshold = speed_threshold

    adder = 1
    multiplier1 = 12    #Ball not detected
    multiplier2 = 8     #Ball aligned under slow_down_distance
    multiplier3 = 8     #Ball aligned under dribbler_dist + 4
    multiplier4 = 4     #Dribbler & goal not found
    multiplier5 = 4     #Dribbler & goal found
    multiplier6 = 4     #Ball not aligned & ball angle negative
    multiplier7 = 12    #Ball not aligned & ball angle positive
    multiplier8 = 3     #Defense move sideways
    multiplier9 = 12    #Defense align goal
    multiplier10 = 2    #Defense move to goal

    Max = int(Min * 7.4)
    dribbler_dist = Min + 5
    slow_down_distance = int(dribbler_dist * 2)

    binary = 140
    threshold_line = 1500
    ball_max_area = 350
    write_reg = 10

    # Color thresholds
    threshold_ball = (0, 100, 44, 127, 17, 127)
    goal_jaune = (0, 100, -1, 22, 16, 127)
    goal_bleu = (0, 38, -128, 127, -128, -17)


elif robot == "SN5":
    offset_x = 162
    offset_y = 114
    Min = 26
    zone_capture = 4

    Kick_duration = 15
    Goal_kick_distance = 100
    goal_defending_distance = 92

    speed_threshold = 1.5
    rotation_threshold = speed_threshold
    original_speed_threshold = speed_threshold

    adder = -1000
    multiplier1 = 16        #Ball not detected
    multiplier2 = 12        #Ball aligned under slow_down_distance
    multiplier3 = 12        #Ball aligned under dribbler_dist + 4
    multiplier4 = 5         #Dribbler & goal not found
    multiplier5 = 5         #Dribbler & goal found
    multiplier6 = 8         #Ball not aligned & ball angle negative
    multiplier7 = 14        #Ball not aligned & ball angle positive
    multiplier8 = 2         #Defense move sideways
    multiplier9 = 12        #Defense align goal
    multiplier10 = 4        #Defense move to goal

    Max = int(Min * 6.5)
    dribbler_dist = Min + 6
    slow_down_distance = int(dribbler_dist * 1.8)

    binary = 140
    threshold_line = 4000
    ball_max_area = 300
    write_reg = 1

    # Color thresholds
    threshold_ball = (0, 100, 55, 127, 0, 127)
    goal_jaune = (0, 100, -6, 42, 20, 127)
    goal_bleu = (0, 40, -128, 127, -128, -15)


if goal_defendu == "jaune":
    threshold_attacked_goal = goal_bleu
    threshold_defended_goal = goal_jaune
elif goal_defendu == "bleu":
    threshold_attacked_goal = goal_jaune
    threshold_defended_goal = goal_bleu


# Camera sensor initialisation
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=800)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
clock = time.clock()

# Image settings
sensor.__write_reg(0, write_reg) # Modifie le deuxième paramètre pour augmenter/diminuer la luminosité
sensor.set_brightness(1) # Entre -3 et 3 pour augmenter/diminuer la luminosité
sensor.set_saturation(-1)
sensor.set_contrast(-3)


# Camera pins initialisation
M1_1 = pyb.Pin('P0', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)
M1_2 = pyb.Pin('P1', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)

M2_1 = pyb.Pin('P2', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)
M2_2 = pyb.Pin('P3', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)

uart = UART(3, 9600)

M3_1 = pyb.Pin('P6', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)
M3_2 = pyb.Pin('P7', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)

M4_1 = pyb.Pin('P8', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)
M4_2 = pyb.Pin('P9', pyb.Pin.OUT_PP, pyb.Pin.PULL_NONE)


# Global variables
M_1 = 1
M_2 = 2
M_3 = 3
M_4 = 4
sens = 0
ball_x = 0
ball_y = 1000
attacked_goal_x = 0
attacked_goal_y = 1000
defended_goal_x = 0
defended_goal_y = 1000
coefficient = 1
delay_loop = 0
compteurNone = 0
role = 1
logs = ["", "", ""]
is_dribbling = 0
direction_ball = 1
direction_goal = 1
speed_1 = 0
speed_2 = 0
speed_3 = 0
ligne = 0


# Stop all motors
def StopMotors():
    global speed_1
    global speed_2
    global speed_3
    global rotation_threshold
    M1_1.value(0)
    M1_2.value(0)
    M2_1.value(0)
    M2_2.value(0)
    M3_1.value(0)
    M3_2.value(0)
    M4_1.value(0)
    M4_2.value(0)
    speed_1 = 0
    speed_2 = 0
    speed_3 = 0
    rotation_threshold = 0
    MultipleMotors(0, 0, 0)



# Turn a specific motor into a specific direction
def OneMotor(motor, value):

    if value == 0:
        INPUT_1 = 0
        INPUT_2 = 0

    if value > 0:
        INPUT_1 = 1
        INPUT_2 = 0

    if value < 0:
        INPUT_1 = 0
        INPUT_2 = 1

    if motor == M_1:
        M1_1.value(INPUT_2)
        M1_2.value(INPUT_1)

    if motor == M_2:
        M2_1.value(INPUT_2)
        M2_2.value(INPUT_1)

    if motor == M_3:
        M3_1.value(INPUT_2)
        M3_2.value(INPUT_1)

    if motor == M_4:
        M4_1.value(INPUT_2)
        M4_2.value(INPUT_1)



# Turn different motors at different speeds and in different directions
def MultipleMotors(speed1, speed2, speed3):
    global speed_1
    global speed_2
    global speed_3
    speed_1 = speed1
    speed_2 = speed2
    speed_3 = speed3
    #print(f"{speed_1}, {speed_2}, {speed_3}")


i = 1
# Motor movement timer
def tick(timer):

    global i
    PWM1 = 0 if math.fabs(speed_1) == 50 else speed_1
    PWM2 = 0 if math.fabs(speed_2) == 50 else speed_2
    PWM3 = 0 if math.fabs(speed_3) == 50 else speed_3


    if i == 1:
        OneMotor(M_1, PWM1)
        OneMotor(M_2, PWM2)
        OneMotor(M_3, PWM3)
        i = 2

    elif i == 2:
        OneMotor(M_1, speed_1)
        OneMotor(M_2, speed_2)
        OneMotor(M_3, speed_3)
        i = 3

    elif i < speed_threshold:
        OneMotor(M_1, 0)
        OneMotor(M_2, 0)
        OneMotor(M_3, 0)
        i += 1

    elif i < rotation_threshold:
        OneMotor(M_1, -100*coefficient)
        OneMotor(M_2, -100*coefficient)
        OneMotor(M_3, 100*coefficient)
        i += 1

    else:
        OneMotor(M_1, speed_1)
        OneMotor(M_2, speed_2)
        OneMotor(M_3, speed_3)
        i = 1

# Timer initialisation
tim = pyb.Timer(2, freq=1000)
tim.callback(tick)



# Move the robot in a specific direction
def Move(direction, objet_x):
    global speed_1
    global speed_2
    global speed_3

    if direction == 0 or direction == 360 or direction == -360:
        MultipleMotors(-100, 50, -50)

    if direction == 30 or direction == 390 or direction == -330:
        MultipleMotors(-100, 100, 0)

    if direction == 60 or direction == 420 or direction == -300:
        MultipleMotors(-50, 100, 50)

    if direction == 90 or direction == 450 or direction == -270:
        MultipleMotors(0, 100, 100)
        if ball_x > zone_capture: #Angle_objet(ball_x, ball_y) > 100:
            speed_3 = 50
            print("Trop à gauche")
        elif ball_x < -zone_capture: #Angle_objet(ball_x, ball_y) < 80:
            speed_2 = 50
            print("Trop à droite")

    if direction == 120 or direction == 480 or direction == -240:
        MultipleMotors(50, 50, 100)

    if direction == 150 or direction == 510 or direction == -210:
        MultipleMotors(100, 0, 100)

    if direction == 180 or direction == 540 or direction == -180:
        MultipleMotors(100, -50, 50)

    if direction == -30 or direction == 330 or direction == -390:
        MultipleMotors(-100, 0, -100)

    if direction == -60 or direction == 300 or direction == -420:
        MultipleMotors(-50, -50, -100)

    if direction == -90 or direction == 270 or direction == -450:
        MultipleMotors(0, -100, -100)

    if direction == -120 or direction == 240 or direction == -480:
        MultipleMotors(50, -100, -50)

    if direction == -150 or direction == 210 or direction == -510:
        MultipleMotors(100, -100, 0)



# Rotate the robot on its vertical axis
def Rotation(direction, orientation2):
    global coefficient
    global rotation_threshold
    global speed_threshold
    coefficient = orientation2 if direction == "right" else -orientation2
    rotation_threshold = speed_threshold + adder
    MultipleMotors(-100*coefficient, -100*coefficient, 100*coefficient)



# Align the robot on a blob detected by the camera
def Alignement(objet_x, objet_y, orientation1):

    orientation2 = 1 if orientation1 == "forward" else -1

    if objet_x > int(offset_x/16):
        Rotation("left", orientation2)
        return -1

    elif objet_x < int(-offset_x/16):
        Rotation("right", orientation2)
        return 1

    elif orientation2 * objet_y < 0:
        Rotation("right", orientation2)
        return 1



# Turn on or off the robot's dribbler system
def Dribbler(state):
    OneMotor(M_4, state)


# Turn on or off the robot's kicker system
def Kicker():
    OneMotor(M_4, -1)


# Approximate an angle to its closest multiple of 30
def Quantized_angle(angle):

    if -15 <= angle < 15:
        finalAngle = 0
    elif 15 <= angle < 45:
        finalAngle = 30
    elif 45 <= angle < 65:
        finalAngle = 60
    elif 65 <= angle < 115:
        finalAngle = 90
    elif 115 <= angle < 135:
        finalAngle = 120
    elif 135 <= angle < 165:
        finalAngle = 150
    elif 165 <= angle or angle < -165:
        finalAngle = 180
    elif -15 > angle >= -45:
        finalAngle = -30
    elif -45 > angle >= -75:
        finalAngle = -60
    elif -75 > angle >= -105:
        finalAngle = -90
    elif -105 > angle >= -135:
        finalAngle = -120
    elif -135 > angle >= -165:
        finalAngle = -150

    return finalAngle



# Determine the angle of a blob on the image
def Angle_objet(objet_x, objet_y):
    angle = 0
    if objet_y >= 0 and objet_x > 0:
        angle = round(math.atan(objet_y/objet_x)*57.3)
    elif objet_y >= 0 and objet_x < 0:
        angle = round(math.atan(objet_y/objet_x)*57.3) + 180
    elif objet_y <= 0 and objet_x > 0:
        angle = round(math.atan(objet_y/objet_x)*57.3)
    elif objet_y < 0 and objet_x < 0:
        angle = round(math.atan(objet_y/objet_x)*57.3) - 180

    elif objet_x == 0:
        if objet_y > 0:
           angle = 90
        elif objet_y < 0:
           angle = -90

    return angle



# Determine the distance from the origin of a blob on the image
def Distance(objet_x, objet_y):
    Distance = int(math.sqrt((objet_x * objet_x) + (objet_y * objet_y)))
    return Distance



# Find the white borders of the field
def Find_lines(img, reach, restriction):
    if detection_de_ligne:
        pass
    else:
        return []

    new_min = int(Min*1.3)
    img.draw_circle(offset_x, offset_y, new_min, fill = True, color = (0,0,0))
    img.draw_circle(offset_x, offset_y, (new_min * 5) + reach, fill = False, color = (0,0,0), thickness = new_min * 10)
    if restriction:
        img.draw_rectangle(0, offset_y - 25, img.width(), img.height() - offset_y, color = (0,0,0), fill = True)
        img.draw_rectangle(0, 0, offset_x - 25, img.height(), color = (0,0,0), fill = True)
        img.draw_rectangle(offset_x + 25, 0, offset_x, img.height(), color = (0,0,0), fill = True)

    img.to_grayscale()
    img.binary([(binary, 255)])

    # Copier les img.draw du dessus ici et changer la couleur pour afficher les zones

    zones = []

    segments = img.find_lines(theta_margin = 5, rho_margin = 10, threshold = threshold_line, x_stride=1, y_stride=1)
    if len(segments) > 0:
        for i in range(len(segments)):
            ligne = segments[i]
            line_angle = ligne.theta()
            if 40 <= line_angle and line_angle <= 140:
                img.draw_line(ligne.line(), color = (255, 200, 0))
                zones.append(line_angle)

    if zones != None and len(zones) > 0: # Line detection
        print("3bis. Ligne détectée")
        StopMotors()

    return zones



# Robot is defined a an attacker
def Attaque(angle_ball, ball_x, ball_y, angle_attacked_goal, attacked_goal_x, attacked_goal_y):

    global speed_1
    global speed_2
    global speed_3
    global speed_threshold
    global rotation_threshold
    global is_dribbling
    global direction_ball
    global direction_goal
    global ligne
    speed_threshold = original_speed_threshold
    rotation_threshold = speed_threshold
    ligne = 0

    if angle_ball == -1 and is_dribbling == 0: # Ball not detected
        StopMotors()
        speed_threshold = multiplier1
        if direction_ball == 1:
            Rotation("right", 1)
        elif direction_ball == -1:
            Rotation("left", 1)
        print("1. Balle non détectée")


    elif angle_attacked_goal - 90 <= angle_ball and angle_ball <= angle_attacked_goal + 90 and not attacked_goal_y == 1000 and Distance(attacked_goal_x, attacked_goal_y) > goal_defending_distance - 3 and not (Distance(ball_x, ball_y) < int(dribbler_dist * 1.4) and angle_ball == 90):
        # Line detection
        reach = int(dribbler_dist * 1.4)
        ligne = Find_lines(img, reach, False)

        Move((angle_ball * 2) - angle_attacked_goal, 0)
        print("2. bis FONCE MON POTE")


    elif Distance(attacked_goal_x, attacked_goal_y) < goal_defending_distance - 3 and not attacked_goal_y == 1000 :
        Move(angle_attacked_goal - (180 * math.copysign(1, angle_attacked_goal)), 0)
        print("2. bis RECULE MON POTE")


    else:

        if (angle_ball == 90 and ball_y > int(dribbler_dist * 1.2)) or (-zone_capture*2 < ball_x and ball_x < zone_capture*2 and ball_y > 0) or is_dribbling == 1: # Ball straight forward

            if Distance(ball_x, ball_y) > dribbler_dist and not ball_y == 1000: # Ball too far away
                is_dribbling = 0
                reach = int(dribbler_dist * 1.4)

                if Distance(ball_x, ball_y) < slow_down_distance: # Slow down if the ball is close enough
                    speed_threshold = multiplier2 - int( (math.fabs(Distance(ball_x, ball_y) - dribbler_dist) / (10*speed_threshold)))
                    print("Ball under slow_down_distance")

                if Distance(ball_x, ball_y) < int(dribbler_dist * 1.4):
                    reach = Distance(ball_x, ball_y) + 5

                if Distance(ball_x, ball_y) < dribbler_dist + 4: # Determine if the robot is dribbling or not
                    is_dribbling = 1
                    speed_threshold = multiplier3
                    reach = dribbler_dist + 8

                    """if attacked_goal_x > 0:
                        speed_1 = 50
                    else:
                        speed_1 = -50"""

                    print("Ball under dribbler_dist + 4")

                # Line detection
                ligne = Find_lines(img, reach, True)

                if ligne == []: # Forward movement for capturing the ball
                    Dribbler(1)
                    if Distance(defended_goal_x, defended_goal_y) < goal_defending_distance + 5 and 0 < angle_defended_goal and angle_defended_goal < 180:
                        speed_threshold = original_speed_threshold * 4
                        print("goal defendu en face")
                        StopMotors()
                        speed_1 = math.copysign(1, angle_defended_goal - 90) * 50
                    else:
                        Move(90, ball_x)

                print("3. Déplacement vers l'avant pour capture de la balle")

            else: # Ball captured by the dribbler

                # Goal is straight ahead
                if Angle_objet(attacked_goal_x, attacked_goal_y) > 80 and Angle_objet(attacked_goal_x, attacked_goal_y) < 100 and not attacked_goal_y == 1000:

                    if Distance(attacked_goal_x, attacked_goal_y) > Goal_kick_distance: # Goal too far away
                        Move(90, attacked_goal_x)
                        Dribbler(1)
                        print("5. Déplacement vers le goal")

                    else: # Goal close enough for kicking
                        # Forward movement
                        print("6. Kick")
                        StopMotors()
                        Dribbler(0)
                        speed_threshold = 0
                        rotation_threshold = 0
                        #speed_3 = 50
                        Move(90, 0)
                        if Distance(attacked_goal_x, attacked_goal_y) >= 65:
                            pyb.delay(Kick_duration  * (Distance(attacked_goal_x, attacked_goal_y) - 65))
                        StopMotors()

                        # Solenoïd kick
                        Kicker()
                        pyb.delay(1000)
                        StopMotors()

                        # Backward movement
                        Move(-90, 0)
                        pyb.delay(300)
                        is_dribbling = 0
                        StopMotors()

                elif attacked_goal_y == 1000: # Goal not detected
                    speed_threshold = multiplier4 * 3
                    speed_threshold *= 3
                    direction_goal = Alignement(attacked_goal_x, attacked_goal_y, "forward")
                    print("4. Orientation et déplacement vers le goal (not found)")

                else: # Goal is not straight ahead

                    # Speed management
                    speed_threshold = original_speed_threshold * multiplier4
                    if angle_attacked_goal >= 0:
                        speed_threshold = original_speed_threshold * multiplier5 - int( (math.fabs(Angle_objet(attacked_goal_x, attacked_goal_y) - 90) / (10*speed_threshold)))

                    # Line detection
                    reach = int(dribbler_dist * 1.4)
                    ligne = Find_lines(img, reach, False)

                    # Rotates the robot towards the goal
                    StopMotors()
                    if ligne == []:
                        if attacked_goal_x > 0:
                            speed_1 = 50
                        else:
                            speed_1 = -50
                    else:
                        speed_threshold *= 3
                        direction_goal = Alignement(attacked_goal_x, attacked_goal_y, "forward")

                    # Moves the robot towards the goal
                    """if angle_attacked_goal >= 0 and Distance(attacked_goal_x, attacked_goal_y) > goal_defending_distance:
                        speed_threshold = multiplier6
                        Move(angle_attacked_goal, 0)"""

                    Dribbler(1)
                    print("4. Orientation et déplacement vers le goal")

        else: # Ball is not straight ahead

            is_dribbling = 0

            if Distance(ball_x, ball_y) < slow_down_distance: # Rotates the robot towards the ball
                if angle_ball >= 0:
                    speed_threshold = multiplier7 - int( (math.fabs(Angle_objet(ball_x, ball_y) - 90) / (15*speed_threshold)))
                    print("dynamic slow down")
                else:
                    speed_threshold = multiplier6
                    print("non dynamic slow down")
                direction_ball = Alignement(ball_x, ball_y, "forward")

            else: # Move towards the ball if it is too far away

                # Move
                speed_threshold = original_speed_threshold
                Move(angle_ball, 0)
                print("Move")

            Dribbler(0)
            print("2. Orientation et déplacement vers la balle")



# Robot is defined as the goalie
def Defense(angle_defended_goal, defended_goal_x, defended_goal_y, angle_ball, ball_x, ball_y):

    global speed_threshold
    global rotation_threshold
    speed_threshold = original_speed_threshold
    rotation_threshold = speed_threshold

    # Goal is too far away
    if Distance(defended_goal_x, defended_goal_y) > goal_defending_distance and not defended_goal_y == 1000:
        speed_threshold = multiplier10
        Move(angle_defended_goal, 0)
        print("1. Approche du goal défendu")

    elif Distance(defended_goal_x, defended_goal_y) < 80:
        speed_threshold = multiplier10
        Move(angle_defended_goal - (180 * math.copysign(1, angle_defended_goal)), 0)

    # Goal is close enough
    elif Angle_objet(defended_goal_x, defended_goal_y) > -120 and Angle_objet(defended_goal_x, defended_goal_y) < -60 and not angle_ball == angle_defended_goal:

        # Robot moves between the ball and the goal
        speed_threshold = multiplier8
        if Angle_objet(ball_x, ball_y) > 105:
            Move(180, 0)
            print("Balle trop à droite")
        elif 0 <= Angle_objet(ball_x, ball_y) and Angle_objet(ball_x, ball_y) < 75:
            Move(0, 0)
            print("Balle trop à droite")
        else:
            StopMotors()
            print("3. Aligné avec la balle")

    else: # Alignement with the goal
        speed_threshold = multiplier9 #- int( (math.fabs(Distance(ball_x, ball_y) - dribbler_dist) / (10*speed_threshold)))

        Alignement(defended_goal_x, defended_goal_y, "backward")
        print("2. Alignement arrière avec le goal")



# XBee communication between the 2 robots
def Communication():

    global compteurNone
    global role

    if robot == "SN4":

        # Sends its distance to the ball to the other robot
        uart.write("cha" + str(Distance(ball_x, ball_y)) + "ptal")

        # Receives the other robot's order
        read_text = uart.read()
        #print(read_text)

        del logs[0]
        logs.append(read_text)

        # Determines if it should be attacker or goalie depending on the received order
        if "SN4_DEFENSEUR" in str(logs[1]) and "SN4_DEFENSEUR" in str(logs[2]): # Goalie
           role = 0
        elif "SN4_ATTAQUANT" in str(logs[1]) and "SN4_ATTAQUANT" in str(logs[2]): # Attaquant
           role = 1
        elif logs[0] == None and logs[1] == None and logs[2] == None:
           role = 1


    elif robot == "SN5":

        # Receives the other robot's distance to the ball
        regex = re.compile("cha(\d+)ptal")
        read_text = uart.read()
        #print(read_text)

        del logs[0]
        logs.append(read_text)

        for i in range(len(logs)):

            if logs[i] is not None:

                # Checks if data was correctly received
                match = regex.match(logs[i])
                if match is not None and (not int(match.group(1)) == 1000 or i == 2):

                    distance_SN4 = match.group(1)
                    if Distance(ball_x, ball_y) > int(distance_SN4): # Orders the other robot to be attacker
                        uart.write("SN4_ATTAQUANT")
                        role = 0
                        break
                    else: # Orders the other robot to be attacker, sets itself as goalie
                        uart.write("SN4_DEFENSEUR")
                        role = 1
                        break

            elif logs[0] == None and logs[1] == None and logs[2] == None: # Orders the other robot to be goalie
                role == 1
                uart.write("SN4_DEFENSEUR")
                break

    return role



# Color detection on the image
def Detection_blob(threshold_blob, setting, pixels_min, min_distance, max_area):

    global is_dribbling
    global ligne

    Angle = -1
    blob_x = 0
    if is_dribbling == 1 and threshold_blob == threshold_ball:
        blob_y = dribbler_dist
    else:
        blob_y = 1000

    maxRoundness = 0
    maxBlob = None

    # Checks every blob detected
    for blob in img.find_blobs([threshold_blob], pixels_threshold=pixels_min, merge=True):
        if setting == "roundness":
            maxSetting = blob.roundness()
        elif setting == "area":
            maxSetting = blob.area()
        #print(blob)
        #img.draw_rectangle(blob.rect())

        # Checks if the blob's parameters are within an established range
        if maxSetting > maxRoundness and Distance(blob.cx() - offset_x, -blob.cy() + offset_y) > min_distance and blob.area() < max_area and blob.compactness() > 0:
            maxRoundness = maxSetting
            maxBlob = blob

    # Filtered detected blob
    if maxBlob is not None:

        # Object coordinates and parameters
        blob_x = maxBlob.cx() - offset_x
        blob_y = -maxBlob.cy() + offset_y
        Angle = Quantized_angle(Angle_objet(blob_x, blob_y))
        #print(maxBlob.density(), maxBlob.compactness(), maxBlob.solidity())

        # Blob representation on screen
        if ligne == 0 or ligne == None or detection_de_ligne == False:
            img.draw_rectangle(maxBlob.rect())
        else:
            pass

    return [Angle, blob_x, blob_y]




StopMotors()

# Main loop
while(True):

    # Clock and image capture
    begin = time.ticks_ms()
    clock.tick()
    img = sensor.snapshot()

    # Hide non-interesting areas of the image
    img.draw_circle(offset_x, offset_y, Min, fill = True, color = (0,0,0))
    img.draw_circle(offset_x, offset_y, int(Max*1.25), fill = False, color = (0,0,0), thickness = Max)


    # Ball detection
    detected_blob = Detection_blob(threshold_ball, setting="roundness", pixels_min=2, min_distance=Min, max_area=ball_max_area)
    angle_ball = detected_blob[0]
    ball_x = detected_blob[1]
    ball_y = detected_blob[2]

    # Attacked goal detection
    detected_blob = Detection_blob(threshold_attacked_goal, setting="area", pixels_min=40, min_distance=40, max_area=15000)
    angle_attacked_goal = detected_blob[0]
    attacked_goal_x = detected_blob[1]
    attacked_goal_y = detected_blob[2]

    # Defended goal detection
    detected_blob = Detection_blob(threshold_defended_goal, setting="area", pixels_min=40, min_distance=40, max_area=15000)
    angle_defended_goal = detected_blob[0]
    defended_goal_x = detected_blob[1]
    defended_goal_y = detected_blob[2]


    # Determines if the robot should be an attacker or a goalie
    role = Communication()

    if role == 1: # Attacker
        Attaque(angle_ball, ball_x, ball_y, angle_attacked_goal, attacked_goal_x, attacked_goal_y)
    elif role == 0: # Goalie
        Defense(angle_defended_goal, defended_goal_x, defended_goal_y, angle_ball, ball_x, ball_y)


    # Determines how much time a full loop takes
    time_diff = time.ticks_ms() - begin
    #print(f'temps total: {time_diff}ms')




