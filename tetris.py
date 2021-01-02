import random
from math import ceil
from time import sleep
import getch
import tkinter as tk


ENTER = chr(10)
SPACE = ' '
RIGHT = chr(67)
LEFT = chr(68)
DOWN = chr(66)
ANOMALOUS_RIGHT = chr(65)
IGNORE1 = chr(27)
IGNORE2 = chr(91)
CLOCK = 'x'
COUNTER = 'q'

def clear():
    print(chr(27) + "[2J")

def remove_piece():
    Shapes.screen = Shapes.screen_no_piece.copy()

def update_pieceless():
    Shapes.screen_no_piece = Shapes.screen.copy()

shapes = []

class ShapeTypes:
    
    probs = []
        
    def __init__(self,squares,character,mid_point,probability=1):
        self.squares = squares
        self.cx_squares = [complex(*square) for square in squares]
        self.char = character
        self.mid_pt = complex(*mid_point)
        self.prob = probability
        shapes.append(self)
        ShapeTypes.probs.append(self.prob)
        
    def __rep__(self):
        return self.char


# --- Coordinates of squares of each shape ---
# (0,0) gets mapped to start_point, so each square of a shape has to 
# be of the form (x,y) where 0 <= x < width, -height < y <= 0

B = ShapeTypes([(0,0),
                (0,-1),
                (0,-2),
                (0,-3)], 'B', (0,-1.5))
        
S = ShapeTypes([(0,0), (1,0),
                (0,-1), (1,-1)], 'S', (0.5,-0.5))
        
L = ShapeTypes([(0,0),
                (0,-1),
                (0,-2), (1,-2)], 'L', (0,-1), probability=0.5)

L_b = ShapeTypes([(0,0),
                  (0,-1),
         (-1,-2), (0,-2)], 'L', (0,-1), probability=0.5)
        
T = ShapeTypes([(0,0),
               (0,-1), (1,-1),
               (0,-2)], 'T', (0,-1))
        
Z_s = ShapeTypes([(0,0), (1,0),
         (-1,-1), (0,-1)], 'Z', (0,-0.5), probability=0.5)
        
Z_z = ShapeTypes([(-1,0), (0,0),
                          (0,-1), (1,-1)], 'Z', (0,-0.5), probability=0.5)

orientations = {0,90,180,270}

# Playable screen size
width = 10
height = 20

# 'Next piece' screen size
next_width = 10
next_height = 6

start_point = (ceil(width/2),height-1)
pieces = []

def score_screen(y):
    num = f'{Shapes.score:,}'
    txt = 'Score:'
    if y == height-5:
        return f'{txt: ^10}'
    elif y == height-6:
        return f'{num: ^10}'
    elif y in range(height) or y == 'blank':
        return '          '
    
def add_score(amount):
    Shapes.score += amount

def random_shape():
    """Returns a random shape"""
    rand_shapes = random.choices(shapes,ShapeTypes.probs)
    return rand_shapes[0]

def bottom_msg(args=None):
    """Given appropriate arguments, changes the message underneath the
    screen.
    
    Otherwise, outputs the current state of the message.
    """
    if args == '':
        Shapes.msg = ''
    elif args == 'start':
        Shapes.msg = """Movement: A, S, D or arrow keys \nDrop: Space \nRotation: Q and E\nExit: Enter"""
    # elif args == 'default':
    #     Shapes.msg = 'Press a button to move:'
    elif args == 'default':
        Shapes.msg = ''
    elif args == 'wrong key':
        Shapes.msg = """Incorrect input. Press A, S, D, Space, or Q and E. Pressing Enter exits the game."""
    elif args == 'game over':
        Shapes.msg = """Game over. Press anything to continue or press 'R' to play again."""
    else:
        return Shapes.msg + ' '



def dont_displace(square):
    """Leaves the coordinates of a piece unmoved."""
    return square

def right(square):
    """Moves the coordinates of a piece one pixel to the right."""
    return (square[0]+1,square[1])

def left(square):
    """Moves the coordinates of a piece one pixel to the left."""
    return (square[0]-1,square[1])

def down(square):
    """Moves the coordinates of a piece one pixel down."""
    return (square[0],square[1]-1)

def up(square):
    """Moves the coordinates of a piece one pixel up."""
    return (square[0],square[1]+1)

def spawn(square):
    """Moves the coordinates of a piece to the spawn point."""
    return start_point
    
def dont_rotate(orientation):
    """Leaves the orientation of a piece unchanged."""
    return orientation
                           
def counter_clockwise(orientation):
    """Rotates the orientation of a piece 90 degrees counter-clockwise."""
    return (orientation + 90) % 360 # Ensuring orientation is modulo 360
    
def clockwise(orientation):
    """Rotates the orientation of a piece 90 degrees clockwise."""
    return (orientation - 90) % 360 # Ensuring orientation is modulo 360

def power(x,n):
    """A simple x^n function, to be used on complex numbers."""
    if n > 0:
        y = x
        for _ in range(n-1):
            x = x * y
    elif n == 0:
        x = 1
    else:
        y = x
        for _ in range(-(n-1)):
            x = x / y
    return x

# @lru_cache(maxsize=200)
# def tuple_(z):
#     return (z.real,z.imag)

class Shapes:
    
    screen = {}
    screen_no_piece = {}
    next_screen = {}
    
    msg = 'Press a button to move:'
    score = 0
    smart_rotation = True
    
    time_out = 1
    
    def __init__(self,shape,orientation=0,position=start_point):
        self.shape = shape
        self.char = self.shape.char
        self.ori = orientation
        self.pos = position
        self.reached_bottom = False
        
    def __repr__(self):
        return f'{repr(self.shape)} piece'
        
    def squares(self,movement=dont_displace,
                rotation=dont_rotate,
                position=None):
        """Yields all the squares of the piece on the screen.  
        Input is taken as functions of position, and of orientation.
        If a position is given, the function yields squares if the piece
        were there."""
        if position is None:
            position = self.pos
        
        pos = complex(*movement(position))
        # Number of quarter rotations
        qua_rots = int(rotation(self.ori)/90) 
        # e^(qua_rots*pi/2)
        cmx_rotation = power(complex(0,1),qua_rots)
        
        for square in self.shape.cx_squares:
            cmx_sq = (self.shape.mid_pt + pos 
                      + (square - self.shape.mid_pt) * cmx_rotation)
            yield (ceil(cmx_sq.real),ceil(cmx_sq.imag))
            
    def place(self,state=None,character=None):
        """Places (or removes) the piece on the screen.
        Displays the character of the shape, or a specified one."""
        if character is None:
            character = self.char

        if state == 'remove':
            for square in self.squares():
                Shapes.screen[square] = ' '
        elif state == 'force place':
            for square in self.squares():
                try:
                    Shapes.screen[square] = character
                except KeyError:
                    pass
        elif state == None:
            for square in self.squares():
                Shapes.screen[square] = character
        elif isinstance(state,Shapes):
            for square in self.squares():
                if square not in state.squares():
                    Shapes.screen[square] = character
                
    def push_up(self):
        """Pushes the piece above (and out of the border) and places it.
        
        Only invoked after the player has lost and the piece does not 
        have space to spawn.
        """
        i = 0
        
        def iteration():
            nonlocal i
            if all(square not in Shapes.screen_no_piece \
                   for square in self.squares()):
                # All squares are out of the border
                return
            elif i == 5:
                raise Exception("Unexpectedly iterated 5 times.")
            else:
                in_border = \
                    set(Shapes.screen_no_piece).intersection(self.squares())
                if all(Shapes.screen_no_piece[square] == ' ' \
                       for square in in_border):
                    # Of the squares in the border, if they are no longer
                    # touching any other piece, display them
                    self.place('force place')
                    return
                else:
                    i += 1
                    self.pos = up(self.pos)
                    iteration()
        iteration()
            
    def can_move(self,movement,rotation=dont_rotate,custom_pos=None):
        """Checks whether there is an empty space in the desired direction
        or orientation of movement, in the shape of the object.
        If movement=spawn, checks if piece can spawn (with orientation
        as rotation(self.ori).)
        If a custom position is given, checks if move is possible from that
        point."""
        if custom_pos is None:
            custom_pos = self.pos
        # If all of the squares are empty, there is a free space
        return all(square in Shapes.screen_no_piece and \
                   Shapes.screen_no_piece[square] == ' ' \
                   for square \
                   in self.squares(movement,rotation,custom_pos))
            
    def move(self, movement=dont_displace, rotation=dont_rotate):
        """Given movement and rotation, as functions of position and
        orientation, changes the position and orientation of the piece
        to the corresponding values."""
        self.pos = movement(self.pos)
        self.ori = rotation(self.ori)
        remove_piece() # Removes the old piece before move was made
        assert self.pos in Shapes.screen
        self.place() # Replaces the piece in the new position
        
    def drop(self):
        """Moves the piece down on the screen until there is no more free
        space below."""
        i = 1
        if self.can_move(down):
            x, y = self.pos
            while self.can_move(movement=down,custom_pos=(x,y-i)):
                assert i < 21, "unexpectedly reached too many repetitions"
                i += 1
            
        return lambda square: (square[0],square[1]-i)
            
                
    def input_output(self):
        """Defines the Dictionary of possible game inputs and 
        corresponding outcomes as a tuple of functions of position and
        orientation."""
        return {'s':(down, dont_rotate),
                DOWN:(down, dont_rotate), 
                'd':(right, dont_rotate),
                RIGHT:(right, dont_rotate),
                'a':(left, dont_rotate),
                LEFT:(left, dont_rotate),
                'q':(dont_displace, counter_clockwise),
                'e':(dont_displace, clockwise),
                SPACE:(self.drop(),dont_rotate)}
    
    def iterate_move(self,inp):
        """Attempts to move the piece given input 'inp' and its 
        corresponding outcomes determined by self.input_output().
        
        If it cannot move and is going down, it has reached the bottom.
        Otherwise, the function does nothing.
        """
        if inp == ENTER:
            pass
        elif inp in {IGNORE1, IGNORE2}:
            pass
        elif inp == ANOMALOUS_RIGHT:
            bottom_msg('wrong key')
        elif inp in self.input_output():
            bottom_msg('default')
            move_fn, rot_fn = self.input_output()[inp]

            if self.can_move(move_fn,rot_fn):
                self.move(move_fn,rot_fn)
            elif rot_fn != dont_rotate and Shapes.smart_rotation:
                # If cannot rotate, try rotating and moving
                for direction in [down,right,left]:
                    if self.can_move(direction,rot_fn):
                        self.move(direction,rot_fn)
                        break
            elif inp in {DOWN, 's', SPACE}:
                # If no empty space AND going down -ie- reached bottom
                self.reached_bottom = True
                update_pieceless()
            else:
                # If no empty space in desired move and not going down,
                # do nothing
                pass 
        # If input was incorrect
        elif inp.lower() in self.input_output():
            self.iterate_move(inp.lower())
        else:
            bottom_msg('wrong key')

    def place_ghost(self):
        drop_down = self.drop()
        ghost_piece = Shapes(self.shape,self.ori,drop_down(self.pos))
        if self.can_move(drop_down):
            ghost_piece.place(self,character='·')

    def auto_move(self,inp=None):
        sleep(1)
        self.iterate_move(DOWN)
        self.auto_move()

    @staticmethod        
    def current(args=-3):
        """Defines what is considered the 'playable' piece, the one
        moving on the screen."""
        return pieces[args]

# ---- INITIALIZE SCREEN ----


# Playable screen coordinates are x = 0 ... width-1 
# and y = 0 ... height-1
def initialize():
    """Resets the dictionaries Shapes.screen and Shapes.next_screen to
    make sure the screens don't unexpectedly change before replaying
    the game. Also resets the score."""
    Shapes.score = 0
    Shapes.screen = {(x,y): ' ' for x in range(width) \
                          for y in range(height)}
    Shapes.next_screen = {(x,y): ' ' for x in range(next_width) \
                          for y in range(next_height)}

def empty():
    """Clears all the existing pieces and sets all the pixels on 
    the screen to be blank."""
    # Clear the list of ingame pieces
    pieces.clear()
    for square in Shapes.next_screen:
        Shapes.next_screen[square] = ' '
    
    # Empty pixels on game screen
    for square in Shapes.screen:
        Shapes.screen[square] = ' '
    
    # Empty pixels on secondary screen (used to keep track of screen
    # without the current piece)
    update_pieceless()
    
empty()

def spawn_piece(piece_type=None,
          orientation=0,
          position=start_point):
    """Spawns a Tetris shape with random type and orientation, 
    and with starting position as the spawn point."""
    # list 'pieces' keeps track of pieces in game, index corresponding
    # to ID
    if piece_type == None:
        piece_type = random_shape()
    pieces.append(
        Shapes(piece_type,orientation,position))
    
    
    
def line_clear():
    """Checks if any horizontal line has been filled with squares of 
    pieces. If yes, animates the removing of the line and drops the rest
    of the squares through newly created space."""
    cleared_lines = []
    for y in range(height):
        for x in range(width):
            if Shapes.screen[x,y] == ' ':
                break
        else:
            cleared_lines.append(y)
    
    
    def edit_line(lines,character):
        for y in lines:
            for x in range(width):
                Shapes.screen[x,y] = character
    
    if cleared_lines:
        add_score(100*len(cleared_lines))
        edit_line(cleared_lines,'-')
        bottom_msg('')
        print(print_screen())
        sleep(0.5)
        edit_line(cleared_lines,' ')
        bottom_msg('default')
        
        for y in cleared_lines:
            for x in range(width):
                del Shapes.screen[x,y]
        remaining_lines = [y for y in range(height) \
                           if y not in cleared_lines]
        screen_copy = Shapes.screen
        for i, y in enumerate(remaining_lines):
            for x in range(width):
                Shapes.screen[x,i] = screen_copy[x,y]
        for y in range(len(remaining_lines),height):
            for x in range(width):
                Shapes.screen[x,y] = ' '
        
        update_pieceless()

def next_pieces():
    """Defines the positions of the two 'next pieces' on 
    the mini-screen."""
    for x in range(next_width):
        for y in range(next_height):
            Shapes.next_screen[x,y] = ' '
    shape1 = pieces[-2].shape
    shape2 = pieces[-1].shape
    
    for (x, y) in shape1.squares:
        Shapes.next_screen[(x+2, y+4)] = shape1.char
    for (x, y) in shape2.squares:
        Shapes.next_screen[(x+7, y+4)] = shape2.char
    
def print_screen(screen_type=None):
    """Displays the entire screen, containing the playable screen,
    the mini-screen of 'next pieces' and the score."""
    if screen_type is None:
        screen_type = Shapes.screen
    
    clear()
    # ======================================
    screen_text = score_screen('blank') + ''.join(['=' for i \
                           in range((1 + width + 1) 
                                    + next_width + 1)]) + '\n'
    
    
    #       = SCREEN SCREEN SCREEN = NEXT PIECES =
    # SCORE =                      =      .      =
    #  ...  =           .          =      .      =
    #       =           .          = NEXT PIECES =
    #       =           .          = 
    #       =                      = 
    #       = SCREEN SCREEN SCREEN = 
    
    for y in reversed(range(height)):
        line_y = []
        assert next_height < height
        h = height - 1
        n = next_height - 1
        d = h - n
        for x in range(width):
            line_y.append(screen_type[(x,y)])
            
        line_y.append('=')
        if d - 1 < y <= h:
            for x in range(next_width):
                line_y.append(Shapes.next_screen[(x,y-d)])
            line_y.append('=')
        elif y == d - 1:
            line_y.append(''.join(['=' for i in range(next_width+1)]))

            
        screen_text += score_screen(y) + '=' + ''.join(line_y) + '\n'
    
    
    # ========================
    screen_text += score_screen('blank') + ''.join(['=' for i \
                         in range(1 + width + 1)]) + '\n'
    screen_text += bottom_msg()
    
    return screen_text

# initialize()
# empty()

# spawn_piece()
# spawn_piece()
# spawn_piece()
# Piece = Shapes.current()
# Piece.place()
# Piece.iterate_move(SPACE)
# print(print_screen())
# print(Piece.can_move(Piece.drop()))
# Piece.iterate_move(SPACE)
# print(print_screen())
# print(Piece.reached_bottom)

def play():
    initialize() # Clear the screen dictionaries for possible errors
    empty() # Clear the screen
    
    spawn_piece() # Spawn the first piece
    spawn_piece()
    spawn_piece()
    next_pieces() # Update the 'next piece' list
    Piece = Shapes.current() # Select the first piece
    Piece.place() # Place piece on screen
    
    bottom_msg('start') # Make sure game outputs 'Press a button to move: '
    while True:
        Piece.place_ghost()
        print(print_screen())
        inp = getch.getch()
        if inp == ENTER:
            break
        Piece.iterate_move(inp) # Check for free space and move if free
        
        if Piece.reached_bottom:
            add_score(10)
            line_clear() # If any horizontal lines are filled, clear them
            spawn_piece()
            next_pieces()
            Piece = Shapes.current() # Select next piece
            if Piece.can_move(spawn,dont_rotate):
                Piece.place() # Place piece if there is space
            else:   
                Piece.push_up() # If the piece cannot spawn, push it up
                bottom_msg('game over')
                print(print_screen())
                inp = getch.getch()
                if inp.lower() == 'r':
                    play()
                else:
                    break # otherwise game over
                
    
        

play()