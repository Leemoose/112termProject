import libtcodpy as libtcod
import math, textwrap, shelve

DEFAULT_SPEED = 8
DEFAULT_ATTACK_SPEED = 20
wall_tile = 256 
floor_tile = 257
player_tile = 258
orc_tile = 259
troll_tile = 260
scroll_tile = 261
healingpotion_tile = 262
sword_tile = 263
shield_tile = 264
stairsdown_tile = 265
dagger_tile = 266

LIGHTNING_DAMAGE = 20
LIGHTNING_RANGE = 5
CONFUSE_NUM_TURNS = 10
CONFUSE_RANGE = 8
FIREBALL_RADIUS = 3
FIREBALL_DAMAGE = 12

def run():
    data = initGame()
    libtcod.console_set_default_foreground(0, libtcod.light_yellow)
    libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 4, libtcod.BKGND_NONE,
        libtcod.CENTER, "Diablo I?")
    libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT-2, libtcod.BKGND_NONE,
        libtcod.CENTER, "C. Leemhuis")
    main_menu(data)
    # main_menu(data)

def initVar(): #Initialize major variables
    class Struct(object): pass
    data = Struct()
    data.LIMIT_FPS = 20
    data.ROOM_MAX_SIZE = 10
    data.ROOM_MIN_SIZE = 6
    data.MAX_ROOMS = 30
    global FOV_LIGHT_WALLS, FOV_ALGO, MSG_X, BAR_WIDTH, PANEL_HEIGHT, PANEL_Y
    FOV_ALGO = 0 #Default
    FOV_LIGHT_WALLS = True
    data.MAX_ROOM_MONSTERS = 3
    data.player_action = None
    BAR_WIDTH = 20
    PANEL_HEIGHT = 7
    MSG_X = BAR_WIDTH + 2
    data.MAX_ROOMS_ITEMS = 2
    data.INVENTORY_WIDTH = 50
    initColors(data)
    defineGlobals(data)
    PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
    return data

def defineGlobals(data):
    global game_state, player, objects, DEFAULT_SPEED, DEFAULT_ATTACK_SPEED, PLAYER_SPEED
    global panel, MSG_WIDTH, MSG_HEIGHT, game_msgs, mouse, key, inventory, PLAYER_MAXHOLD
    global HEAL_AMOUNT, fov_recompute, TORCH_RADIUS
    defineGlobalSpells()
    defineGlobalScreen()
    HEAL_AMOUNT = 4
    DEFAULT_SPEED = 8
    DEFAULT_ATTACK_SPEED = 20
    PLAYER_SPEED = 2
    game_state = "playing"
    fighter_component = Fighter(hp = 30, defense = 2, power = 5, death_function = player_death)
    player = Object(0, 0, player_tile, "player", libtcod.white, blocks = True, 
        fighter = fighter_component, speed = PLAYER_SPEED)
    objects = [player]
    panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)
    MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
    MSG_HEIGHT = PANEL_HEIGHT - 1
    game_msgs = []
    mouse = libtcod.Mouse()
    key = libtcod.Key()
    PLAYER_MAXHOLD = 26
    inventory = []
    fov_recompute = True
    TORCH_RADIUS = 10

def defineGlobalScreen():
    global SCREEN_WIDTH, SCREEN_HEIGHT, MAP_HEIGHT, MAP_WIDTH
    SCREEN_WIDTH = 80
    SCREEN_HEIGHT = 50
    MAP_WIDTH = 80
    MAP_HEIGHT = 43

def defineGlobalSpells():
    # global LIGHTNING_DAMAGE, LIGHTNING_RANGE, CONFUSE_NUM_TURNS, CONFUSE_RANGE
    # global FIREBALL_RADIUS, FIREBALL_DAMAGE
    # LIGHTNING_DAMAGE = 20
    # LIGHTNING_RANGE = 5
    # CONFUSE_NUM_TURNS = 10
    # CONFUSE_RANGE = 8
    # FIREBALL_RADIUS = 3
    # FIREBALL_DAMAGE = 12
    pass

def initColors(data):
    data.color_dark_wall = libtcod.Color(0, 0, 100)
    data.color_dark_ground = libtcod.Color(50, 50, 150)
    data.color_light_wall = libtcod.Color(130, 11, 50)
    data.color_light_ground = libtcod.Color(200, 180, 50)

def initGame():
    data = initVar()
    libtcod.console_set_custom_font('images/tiledFont.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD, 32, 10)
    libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT,
        "python/libtcod tutorial", False)
    load_customfont()
    global con
    con = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)
    return data

def newGame(data):
    libtcod.sys_set_fps(data.LIMIT_FPS)
    make_map(data)
    make_fovMap(data)
    message("Welcome stranger! Prepare to be yeeted upon by my zounds of orcs!",
        libtcod.red)

def playGame(data):
    global key, mouse, player_action
    while not libtcod.console_is_window_closed():
        action = mainLoop(data)
        if action == "exit":
            save_game()
            break

def main_menu(data):
    img = libtcod.image_load("images/menu_background1.png")
    while not libtcod.console_is_window_closed():
        libtcod.image_blit_2x(img, 0, 0, 0)
        choice = menu(data, "", ["Play a new game", "Continue last game", "Quit"], 24)
        if choice == 0: #new game
            data = initGame()
            newGame(data)
            playGame(data)
        if choice == 1:
            try:
                load_game(data)
            except:
                msgbox(data, "\n No saved game\n", 24)
                continue
        elif choice == 2: #quit
            break

def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
    #Render bar, need width
    bar_width = int(float(value) / maximum * total_width)
    #Render background
    libtcod.console_set_default_background(panel, back_color)
    libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)
    #Render bar
    libtcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)
    libtcod.console_set_default_foreground(panel, libtcod.white)
    libtcod.console_print_ex(panel, x + total_width / 2, y, libtcod.BKGND_NONE,
        libtcod.CENTER, name + ": " + str(value) + "/" + str(maximum))

def load_customfont():
    #The index of the first custom tile in the file
    a = 256
 
    #The "y" is the row index, here we load the sixth row in the font file. Increase the "6" to load any new rows from the file
    for y in range(5,6):
        libtcod.console_map_ascii_codes_to_font(a, 32, 0, y)
        a += 32

def save_game():
    file = shelve.open("savegame", "n")
    file["map"] = map1
    file["objects"] = objects
    file["player_index"] = objects.index(player)
    file["inventory"] = inventory
    file["game_msgs"] = game_msgs
    file["game_state"] = game_state
    file.close()

def load_game(data):
    global map1, objects, player, inventory, game_msgs, game_state

    file = shelve.open("savegame", "r")
    map1 = file["map"]
    objects = file["objects"]
    game_state = file["game_state"]
    game_msgs = file["game_msgs"]
    inventory = file["inventory"]
    player = objects[file["player_index"]]
    file.close()
    make_fovMap(data)

def msgbox(data, text, width = 50):
    menu(data, text, [], width)
                    

#############
# RUNNING GAME
############

def mainLoop(data):
    global key, mouse
    libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE, key, mouse)
    render_all()
    libtcod.console_flush()
        #handle keys
    for people in objects:
        people.clear(con)
    player_action = handle_keys(data)
    if player_action == "exit":
        return "exit"
    elif game_state == "playing": # and player_action != "didnt-take-turn":
        for people in objects:
            if people.ai:
                if people.wait > 0:
                    people.wait -= 1
                else:
                    people.ai.take_turn()

def is_blocked(x, y):
    #Test map tile
    if map1[x][y].blocked:
        return True
    for people in objects:
        if people.blocks and people.x == x and people.y == y:
            return True
    return False

def message(new_msg, color = libtcod.white):
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)
    for line in new_msg_lines: #IF full remove
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]
        game_msgs.append((line, color))

###############
#    People functions
##################
def player_move_or_attack(dx, dy, data):
    global fov_recompute
    x = player.x + dx
    y = player.y + dy

    target = None
    for people in objects:
        if people.fighter and people.x == x and people.y == y:
            target = people
            break
    if target is not None:
        player.fighter.attack(target)
    else:
        player.move(dx, dy)
        data.fov_recompute = True

def player_death(player):
    global game_state
    print "You died!"
    game_state = "dead"

    player.char = "%" #Transform player into corpse
    player.color = libtcod.dark_red

def monster_death(monster):
    #Turns into non locking corpse
    print monster.name.capitalize() + " is dead!"
    monster.char = "%"
    monster.color = libtcod.dark_red
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = "remains of " + monster.name
    monster.send_to_back()

def closest_monster(max_range):
    closest_enemy = None
    closest_dist = max_range + 1

    for people in objects:
        if people.fighter and not people == player \
        and libtcod.map_is_in_fov(fov_map, people.x, people.y):
            dist = player.distance_to(people)
            if dist < closest_dist:
                closest_enemy = people
                closest_dist = dist
    return closest_enemy

def target_tile(max_range=None):
    global key, mouse
    while True:
        libtcod.console_flush()
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,key,mouse)
        render_all()

        (x,y) = (mouse.cx, mouse.cy)
        if mouse.lbutton_pressed and libtcod.map_is_in_fov(fov_map, x, y) and \
        (max_range is None or player.distance(x, y) <= max_range):
            return (x,y)
        elif mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
            return (None, None) #Cancelled

def target_monster(max_range = None):
    #Returns clicked monster
    while True:
        (x, y) = target_tile(max_range)
        if x is None:
            return None

        for people in objects:
            if people.x == x and people.y == y and people.fighter and people != player:
                return people

############
#  ITEM FUNCTIONS
#################

def cast_heal():
    if player.fighter.hp == player.fighter.max_hp:
        message("You at full health B!", libtcod.red)
        return "cancelled"

    message("Your wounds begin to close...", libtcod.light_violet)
    player.fighter.heal(HEAL_AMOUNT)

def cast_lightning():
    monster = closest_monster(LIGHTNING_RANGE)
    if monster is None: #No enemy
        message("No enemy within range.", libtcod.purple)
        return "cancelled"
    message("A bolt of lightning zaps the " + monster.name + "with damage " +\
        str(LIGHTNING_DAMAGE), libtcod.light_blue)
    monster.fighter.take_damage(LIGHTNING_DAMAGE)

def cast_confuse():
    message("Left ticket to confuse monster, right click cancel", libtcod.green)
    monster = target_monster(CONFUSE_RANGE)
    if monster is None:
        return "cancelled"
    else:
        old_ai = monster.ai
        monster.ai = ConfusedMonster(old_ai)
        #Tells new component who owns it
        monster.ai.owner = monster
        message("The monster begins to stumble around...", libtcod.light_green)

def cast_fireball():
    #asks player for tile to throw fireball
    message("Left click on tile for fireball or right click cancel.", libtcod.cyan)
    (x, y) = target_tile()
    if x is None: return "cancelled"
    message("A burning mass burns a large area in " + str(FIREBALL_RADIUS) + " tiles!",
        libtcod.orange)
    for people in objects:
        if people.distance(x, y) <= FIREBALL_RADIUS and people.fighter:
            message("The " + people.name + " takes " + str(FIREBALL_DAMAGE) + " fire damage!",
                libtcod.orange)
            people.fighter.take_damage(FIREBALL_DAMAGE)



################
#    KEYS
#################

def handle_keys(data): #Handles player movement
    global key, fov_recompute
    if player.wait > 0:
        player.wait -= 1
        return
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
    elif key.vk == libtcod.KEY_ESCAPE:
        return "exit"
    if game_state == "playing": #Movement
        if key.vk == libtcod.KEY_UP:
            player_move_or_attack(0,-1, data)
            fov_recompute = True
        elif key.vk == libtcod.KEY_DOWN:
            player_move_or_attack(0,1, data)
            fov_recompute = True
        elif key.vk == libtcod.KEY_LEFT:
            player_move_or_attack(-1,0, data)
            fov_recompute = True
        elif key.vk == libtcod.KEY_RIGHT:
            player_move_or_attack(1,0, data)
            fov_recompute = True
        else:
            key_char = chr(key.c)
            if key_char == "g":
                for people in objects:
                    if people.x == player.x and people.y == player.y and people.item:
                        people.item.pick_up()
                        break
            elif key_char == "i":
                chosen_item = inventory_menu(data, "Press the key next to item to use it.")
                if chosen_item is not None:
                    chosen_item.use()
            elif key_char == "d":
                chosen_item = inventory_menu(data, "Press key next to item to drop it.")
                if chosen_item is not None:
                    chosen_item.drop()
            return "didnt-take-turn"

def get_names_under_mouse():
    global mouse
    #Return obj under mouse
    (x, y) = (mouse.cx, mouse.cy)
    #Get list of all objects under key
    names = [obj.name for obj in objects
        if obj.x == x and obj.y == y and libtcod.map_is_in_fov(fov_map, obj.x, obj.y)]
    names = ", ".join(names)
    return names.capitalize()

####################
#     SCREENS
#####################

def menu(data, header, options, width):
    global key, mouse
    if len(options) > 26: raise ValueError("Cannot > 26 options.")
    header_height = libtcod.console_get_height_rect(con, 0, 0, width, 
        SCREEN_HEIGHT, header)
    if header == "":
        header_height = 0
    height = len(options) + header_height
    window = libtcod.console_new(width, height)
    #print header with auto wrap
    libtcod.console_set_default_foreground(window, libtcod.white)
    libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE,
        libtcod.LEFT, header)
    y = header_height
    letter_index = ord("a")
    for option_text in options:
        text = "(" + chr(letter_index) + ")" + option_text
        libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE,
            libtcod.LEFT, text)
        y += 1
        letter_index += 1
    x = SCREEN_WIDTH/2 - width/2
    y = SCREEN_HEIGHT/2 - height/2
    libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)
    libtcod.console_flush()
    key = libtcod.console_wait_for_keypress(True)
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
    index = key.c - ord("a")
    if index >= 0 and index < len(options): return index
    return None

def inventory_menu(data, header):
    #Menu with each item of inve as option
    if len(inventory) == 0:
        options = ["Inventory is empty."]
    else:
        options = [item.name for item in inventory]
    index = menu(data, header, options, data.INVENTORY_WIDTH)
    if index is None or len(inventory) == 0: return None
    return inventory[index].item


#####################
#    MAPS + PLACEMENT
####################
        # MAPS
def make_map(data): #Makes global map 
    global map1, player
    map1 = [[Tile(True)
        for y in range(MAP_HEIGHT)]
            for x in range(MAP_WIDTH)]
    #create room list
    rooms = []
    num_rooms = 0
    for r in range(data.MAX_ROOMS): #Random rooms
        w = libtcod.random_get_int(0, data.ROOM_MIN_SIZE, data.ROOM_MAX_SIZE)
        h = libtcod.random_get_int(0, data.ROOM_MIN_SIZE, data.ROOM_MAX_SIZE)
        x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
        y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)

        new_room = Rect(x, y, w, h)
        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break
        if not failed: #No intersections
            create_room(new_room)
            (new_x, new_y) = new_room.center()
            if num_rooms == 0:
                player.x = new_x
                player.y = new_y
            else: #all other rooms, connect to previous
                (prev_x, prev_y) = rooms[num_rooms - 1].center()
                if libtcod.random_get_int(0, 0, 1) == 1: #hor, then vert
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                else: #vert than horz
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)
            # room_no = Object(new_x, new_y, chr(65+num_rooms), "room number", libtcod.white, False)
            # objects.insert(0, room_no)
            place_objects(new_room, data) #Add stuff to room
            rooms.append(new_room)
            num_rooms += 1

def make_fovMap(data):
    global fov_map
    libtcod.console_clear(con)
    fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            libtcod.map_set_properties(fov_map, x, y,
                not map1[x][y].block_sight, not map1[x][y].blocked)

def create_room(room):
    global map1
    #makes passable room
    for x in range(room.x1 + 1 , room.x2):
        for y in range(room.y1 + 1, room.y2):
            map1[x][y].blocked = False
            map1[x][y].block_sight = False

def create_h_tunnel(x1, x2, y): #Makes passable tunnel
    global map1
    for x in range(min(x1, x2), max(x1, x2) + 1):
        map1[x][y].blocked = False
        map1[x][y].block_sight = False

def create_v_tunnel(y1, y2, x): #Vert tunnel
    global map1
    for y in range(min(y1, y2), max(y1, y2) + 1):
        map1[x][y].blocked = False
        map1[x][y].block_sight = False

        # MONSTERS
def place_objects(room, data):
    num_monsters = libtcod.random_get_int(0, 0, data.MAX_ROOM_MONSTERS)

    for i in range(num_monsters):#place monsters
        x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
        y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)
        if not is_blocked(x, y):
            if libtcod.random_get_int(0, 0, 100) < 80: #Create orc
                fighter_component = Fighter(hp = 10, defense = 0, power = 3, death_function =monster_death)
                ai_component = BasicMonster()
                monster = Object(x, y, orc_tile, "orc", libtcod.white, blocks = True,
                    fighter = fighter_component, ai = ai_component)

            else: #Create troll
                fighter_component = Fighter(hp = 16, defense = 1, power = 4, death_function = monster_death)
                ai_component = BasicMonster()
                monster = Object(x, y, troll_tile, "troll", libtcod.white, fighter = fighter_component,
                    ai = ai_component)

            objects.append(monster)

    num_items = libtcod.random_get_int(0, 0, data.MAX_ROOMS_ITEMS)

    for i in range(num_items):
        x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
        y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)

        if not is_blocked(x, y):
            dice = libtcod.random_get_int(0, 0, 100)
            if dice< 70:
                #create healing potion
                item_component = Item(use_function = cast_heal)
                item = Object(x, y, healingpotion_tile, "healing potion", libtcod.white, item = item_component)
            elif dice < 70 + 10:
                item_component = Item(use_function = cast_lightning)
                item = Object(x, y, "#", "scroll of lightning bolt", 
                    libtcod.light_yellow, item = item_component)
            elif dice < 70 + 10 + 10:
                #Confuse scroll
                item_component = Item(use_function = cast_confuse)
                item = Object(x, y, "#", "scroll of confusion", libtcod.light_yellow, item = item_component)
            else:#Fireball scroll
                item_component = Item(use_function = cast_fireball)
                item = Object(x, y, "#", "scroll of fireball", libtcod.light_yellow, item = item_component)

            objects.append(item)
            item.send_to_back()

#############
# DRAW
############

def render_all():
    global fov_recompute

    if fov_recompute: #Recomute FOV
        fov_recompute = False
        libtcod.map_compute_fov(fov_map, player.x, player.y,
            TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)

    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            visible = libtcod.map_is_in_fov(fov_map, x, y)
            wall = map1[x][y].block_sight
            if not visible:
                if map1[x][y].explored:
                    if wall:
                        libtcod.console_put_char_ex(con, x, y, wall_tile, libtcod.grey, libtcod.black)
                    else:
                        libtcod.console_put_char_ex(con, x, y, floor_tile, libtcod.grey, libtcod.black)
            else:
                #it's visible
                if wall:
                    libtcod.console_put_char_ex(con, x, y, wall_tile, libtcod.white, libtcod.black)
                else:
                    libtcod.console_put_char_ex(con, x, y, floor_tile, libtcod.white, libtcod.black)
                        #since it's visible, explore it

    for people in objects:
        if people != player:
            people.draw(con)
    player.draw(con)
    #pt cons to root console
    libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT,
            0, 0, 0)

    libtcod.console_set_default_background(panel, libtcod.black)
    libtcod.console_clear(panel)
    #Show player stats
    y = 1
    for (line, color) in game_msgs:
        libtcod.console_set_default_foreground(panel, color)
        libtcod.console_print_ex(panel, MSG_X, y, libtcod.BKGND_NONE,
            libtcod.LEFT, line)
        y += 1
    #Health
    render_bar(1, 1, BAR_WIDTH, "HP", player.fighter.hp, player.fighter.max_hp,
        libtcod.light_red, libtcod.darker_red)


    libtcod.console_set_default_foreground(con, libtcod.light_gray)
    #Objects under mouse

    libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse())
    libtcod.console_blit(panel, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 
        0, PANEL_Y)
    



#######################
#     OBJECTS
######################

class Object:
    #Super generic
    def __init__(self, x, y, char, name, color, blocks = False, fighter = None, 
        ai = None, speed = DEFAULT_SPEED, item = None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.speed = speed
        self.wait = 0
        self.blocks = blocks

        self.fighter = fighter
        if self.fighter:
            self.fighter.owner = self

        self.ai = ai
        if self.ai:
            self.ai.owner = self

        self.item = item
        if self.item:
            self.item.owner = self

    def send_to_back(self): #will be drawn first
        global objects
        objects.remove(self)
        objects.insert(0, self)

    def move(self, dx, dy):
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy
            self.wait = self.speed

    def draw(self, con):
        if libtcod.map_is_in_fov(fov_map, self.x, self.y):
            libtcod.console_set_default_foreground(con, self.color)
            libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)

    def clear(self, con):
        libtcod.console_put_char(con, self.x, self.y, " ", libtcod.BKGND_NONE)

    def distance_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def move_towards(self, target_x, target_y): #vectors to target
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy)

    def distance(self, x, y):
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

class Tile:
    def __init__(self, blocked, block_sight = None):
        self.blocked = blocked
        self.explored = False
        if block_sight is None: block_sight = blocked
        self.block_sight = block_sight

class Rect:
    #Rectangle on map to make room
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self):
        center_x = (self.x1 + self.x2) / 2
        center_y = (self.y1 + self.y2) / 2
        return (center_x, center_y)

    def intersect(self, other): #If intersect, return T
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and \
            self.y1 <= other.y2 and self.y2 >= other.y1)

class Fighter: #All combat related props
    def __init__(self, hp, defense, power, death_function = None,
        attack_speed = DEFAULT_ATTACK_SPEED):
        self.attack_speed = attack_speed
        self.max_hp = hp
        self.death_function = death_function
        self.hp = hp
        self.defense = defense
        self.power = power

    def take_damage(self, damage): #apply damage
        if damage > 0:
            self.hp -= damage
        if self.hp <= 0:
            function = self.death_function
            if function is not None:
                function(self.owner)

    def attack(self, target): #Finds attack damage
        damage = self.power - target.fighter.defense

        if damage > 0: #Take damage
            if self.owner.name == "player":
                message ("The player yeeted for " + str(damage) + " hit points.", libtcod.dark_red)
            else:
                message (self.owner.name.capitalize() + " attacks" +\
                " for " + str(damage) + " hit points.", libtcod.dark_pink)
            target.fighter.take_damage(damage)
        else:
            message(self.owner.name.capitalize() + " attacks " + target.name + \
            " but it has no effect!")
        self.owner.wait = self.attack_speed

    def heal(self, amount):
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp

class BasicMonster:
    def take_turn(self): #You see it, it sees you
        monster = self.owner
        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
            #Move towards player
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.x, player.y)
            elif player.fighter.hp > 0:
                monster.fighter.attack(player)

class ConfusedMonster:
    def __init__(self, old_ai, num_turns = CONFUSE_NUM_TURNS):
        self.old_ai = old_ai
        self.num_turns = num_turns
        
    def take_turn(self):
        if self.num_turns > 0:
            self.owner.move(libtcod.random_get_int(0, -1, 1), 
                libtcod.random_get_int(0, -1, 1))
            self.num_turns -= 1
        else:
            self.owner.ai = self.old_ai
            message("The " + self.owner.name + " loses its confusion!", libtcod.white)

class Item:
    def __init__(self, use_function = None):
        self.use_function = use_function
    #Item that can be picked up
    def pick_up(self):
        #Add to inv, remove from map
        if len(inventory) >= PLAYER_MAXHOLD:
            message("Your inventory is full! Haha says the " +\
             self.owner.name + ".", libtcod.red)
        else:
            inventory.append(self.owner)
            objects.remove(self.owner)
            message("You picked up a " + self.owner.name + "!", libtcod.green)

    def use(self):
        #If use function, use
        if self.use_function is None:
            message("The " + self.owner.name + " cannot be used.")
        else:
            if self.use_function() != "cancelled":
                inventory.remove(self.owner) #destroyed after use

    def drop(self):
        #add to map. remove from inventory
        objects.append(self.owner)
        inventory.remove(self.owner)
        self.owner.x = player.x
        self.owner.y = player.y
        message("You dropped a " + self.owner.name, libtcod.yellow)


run()
