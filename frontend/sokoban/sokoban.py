#!../bin/python

import sys
import pygame
import string
import queue
import os

class game:

    def is_valid_value(self,char):
        if ( char == ' ' or #floor
            char == '#' or #wall
            char == '@' or #worker on floor
            char == '.' or #dock
            char == '*' or #box on dock
            char == '$' or #box
            char == '+' ): #worker on dock
            return True
        else:
            return False

    def __init__(self,filename,level):
        self.queue = queue.LifoQueue()
        self.matrix = []
#        if level < 1 or level > 50:
        if level < 1:
            print ("ERROR: Level "+str(level)+" is out of range")
            sys.exit(1)
        else:
            file = open(filename,'r')
            level_found = False
            for line in file:
                row = []
                if not level_found:
                    if  "Level "+str(level) == line.strip():
                        level_found = True
                else:
                    if line.strip() != "":
                        row = []
                        for c in line:
                            if c != '\n' and self.is_valid_value(c):
                                row.append(c)
                            elif c == '\n': #jump to next row when newline
                                continue
                            else:
                                print ("ERROR: Level "+str(level)+" has invalid value "+c)
                                sys.exit(1)
                        self.matrix.append(row)
                    else:
                        break

    def load_size(self):
        x = 0
        y = len(self.matrix)
        for row in self.matrix:
            if len(row) > x:
                x = len(row)
        TILE_SIZE = 64  # or 64 for larger tiles      
        return (x * TILE_SIZE, y * TILE_SIZE)

    def get_matrix(self):
        return self.matrix

    def print_matrix(self):
        for row in self.matrix:
            for char in row:
                sys.stdout.write(char)
                sys.stdout.flush()
            sys.stdout.write('\n')

    def get_content(self,x,y):
        return self.matrix[y][x]

    def set_content(self,x,y,content):
        if self.is_valid_value(content):
            self.matrix[y][x] = content
        else:
            print ("ERROR: Value '"+content+"' to be added is not valid")

    def worker(self):
        x = 0
        y = 0
        for row in self.matrix:
            for pos in row:
                if pos == '@' or pos == '+':
                    return (x, y, pos)
                else:
                    x = x + 1
            y = y + 1
            x = 0

    def can_move(self,x,y):
        return self.get_content(self.worker()[0]+x,self.worker()[1]+y) not in ['#','*','$']

    def next(self,x,y):
        return self.get_content(self.worker()[0]+x,self.worker()[1]+y)

    def can_push(self,x,y):
        return (self.next(x,y) in ['*','$'] and self.next(x+x,y+y) in [' ','.'])

    def is_completed(self):
        for row in self.matrix:
            for cell in row:
                if cell == '$':
                    return False
        return True

    def move_box(self,x,y,a,b):
#        (x,y) -> move to do
#        (a,b) -> box to move
        current_box = self.get_content(x,y)
        future_box = self.get_content(x+a,y+b)
        if current_box == '$' and future_box == ' ':
            self.set_content(x+a,y+b,'$')
            self.set_content(x,y,' ')
        elif current_box == '$' and future_box == '.':
            self.set_content(x+a,y+b,'*')
            self.set_content(x,y,' ')
        elif current_box == '*' and future_box == ' ':
            self.set_content(x+a,y+b,'$')
            self.set_content(x,y,'.')
        elif current_box == '*' and future_box == '.':
            self.set_content(x+a,y+b,'*')
            self.set_content(x,y,'.')

    def unmove(self):
        if not self.queue.empty():
            movement = self.queue.get()
            if movement[2]:
                current = self.worker()
                self.move(movement[0] * -1,movement[1] * -1, False)
                self.move_box(current[0]+movement[0],current[1]+movement[1],movement[0] * -1,movement[1] * -1)
            else:
                self.move(movement[0] * -1,movement[1] * -1, False)

    def move(self,x,y,save):
        if self.can_move(x,y):
            current = self.worker()
            future = self.next(x,y)
            if current[2] == '@' and future == ' ':
                self.set_content(current[0]+x,current[1]+y,'@')
                self.set_content(current[0],current[1],' ')
                if save: self.queue.put((x,y,False))
            elif current[2] == '@' and future == '.':
                self.set_content(current[0]+x,current[1]+y,'+')
                self.set_content(current[0],current[1],' ')
                if save: self.queue.put((x,y,False))
            elif current[2] == '+' and future == ' ':
                self.set_content(current[0]+x,current[1]+y,'@')
                self.set_content(current[0],current[1],'.')
                if save: self.queue.put((x,y,False))
            elif current[2] == '+' and future == '.':
                self.set_content(current[0]+x,current[1]+y,'+')
                self.set_content(current[0],current[1],'.')
                if save: self.queue.put((x,y,False))
        elif self.can_push(x,y):
            current = self.worker()
            future = self.next(x,y)
            future_box = self.next(x+x,y+y)
            if current[2] == '@' and future == '$' and future_box == ' ':
                self.move_box(current[0]+x,current[1]+y,x,y)
                self.set_content(current[0],current[1],' ')
                self.set_content(current[0]+x,current[1]+y,'@')
                if save: self.queue.put((x,y,True))
            elif current[2] == '@' and future == '$' and future_box == '.':
                self.move_box(current[0]+x,current[1]+y,x,y)
                self.set_content(current[0],current[1],' ')
                self.set_content(current[0]+x,current[1]+y,'@')
                if save: self.queue.put((x,y,True))
            elif current[2] == '@' and future == '*' and future_box == ' ':
                self.move_box(current[0]+x,current[1]+y,x,y)
                self.set_content(current[0],current[1],' ')
                self.set_content(current[0]+x,current[1]+y,'+')
                if save: self.queue.put((x,y,True))
            elif current[2] == '@' and future == '*' and future_box == '.':
                self.move_box(current[0]+x,current[1]+y,x,y)
                self.set_content(current[0],current[1],' ')
                self.set_content(current[0]+x,current[1]+y,'+')
                if save: self.queue.put((x,y,True))
            if current[2] == '+' and future == '$' and future_box == ' ':
                self.move_box(current[0]+x,current[1]+y,x,y)
                self.set_content(current[0],current[1],'.')
                self.set_content(current[0]+x,current[1]+y,'@')
                if save: self.queue.put((x,y,True))
            elif current[2] == '+' and future == '$' and future_box == '.':
                self.move_box(current[0]+x,current[1]+y,x,y)
                self.set_content(current[0],current[1],'.')
                self.set_content(current[0]+x,current[1]+y,'+')
                if save: self.queue.put((x,y,True))
            elif current[2] == '+' and future == '*' and future_box == ' ':
                self.move_box(current[0]+x,current[1]+y,x,y)
                self.set_content(current[0],current[1],'.')
                self.set_content(current[0]+x,current[1]+y,'+')
                if save: self.queue.put((x,y,True))
            elif current[2] == '+' and future == '*' and future_box == '.':
                self.move_box(current[0]+x,current[1]+y,x,y)
                self.set_content(current[0],current[1],'.')
                self.set_content(current[0]+x,current[1]+y,'+')
                if save: self.queue.put((x,y,True))

def print_game(matrix,screen):
    screen.fill(background)
    TILE_SIZE = 64
    x = 0
    y = 0
    for row in matrix:
        for char in row:
            if char == ' ': #floor
                screen.blit(floor,(x,y))
            elif char == '#': #wall
                screen.blit(wall,(x,y))
            elif char == '@': #worker on floor
                screen.blit(worker,(x,y))
            elif char == '.': #dock
                screen.blit(docker,(x,y))
            elif char == '*': #box on dock
                screen.blit(box_docked,(x,y))
            elif char == '$': #box
                screen.blit(box,(x,y))
            elif char == '+': #worker on dock
                screen.blit(worker_docked,(x,y))
            x += TILE_SIZE
        x = 0
        y += TILE_SIZE


def get_key():
  while 1:
    event = pygame.event.poll()
    if event.type == pygame.KEYDOWN:
      return event.key
    else:
      pass

def display_box(screen, message):
  "Print a message in a box in the middle of the screen"
  fontobject = pygame.font.Font(None,18)
  pygame.draw.rect(screen, (0,0,0),
                   ((screen.get_width() / 2) - 100,
                    (screen.get_height() / 2) - 10,
                    200,20), 0)
  pygame.draw.rect(screen, (255,255,255),
                   ((screen.get_width() / 2) - 102,
                    (screen.get_height() / 2) - 12,
                    204,24), 1)
  if len(message) != 0:
    screen.blit(fontobject.render(message, 1, (255,255,255)),
                ((screen.get_width() / 2) - 100, (screen.get_height() / 2) - 10))
  pygame.display.flip()

def display_end(screen):
    """Grand celebration when a level is completed (auto closes after 5 seconds)."""
    width, height = screen.get_size()
    font_big = pygame.font.Font(None, int(height * 0.18))  # scale to window height
    font_small = pygame.font.Font(None, int(height * 0.06))
    message = "  LEVEL COMPLETED!  "
    sub_message = "Get ready for the next challenge..."
    
    # Animated color background
    colors = [
        (255, 99, 71),   # Tomato
        (255, 165, 0),   # Orange
        (60, 179, 113),  # MediumSeaGreen
        (100, 149, 237), # CornflowerBlue
        (218, 112, 214)  # Orchid
    ]
    
    clock = pygame.time.Clock()
    color_index = 0
    scale = 1.0
    growing = True
    elapsed_time = 0
    duration = 5000  # milliseconds (5 seconds)
    
    start_ticks = pygame.time.get_ticks()

    while True:
        # Auto close after 5 seconds
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - start_ticks
        if elapsed_time >= duration:
            return  # Auto exit after 5 seconds

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

        # Background color animation
        screen.fill(colors[color_index])
        color_index = (color_index + 1) % len(colors)

        # Pulsating text animation
        scale += 0.025 if growing else -0.025
        if scale >= 1.3:
            growing = False
        elif scale <= 0.9:
            growing = True

        # Render text surfaces
        title_surf = font_big.render(message, True, (255, 255, 255))
        sub_surf = font_small.render(sub_message, True, (0, 0, 0))

        # Scale title dynamically
        scaled_title = pygame.transform.scale(
            title_surf,
            (int(title_surf.get_width() * scale), int(title_surf.get_height() * scale))
        )

        # Center the text
        rect = scaled_title.get_rect(center=(width / 2, height / 2))
        sub_rect = sub_surf.get_rect(center=(width / 2, height * 0.75))

        # Draw to screen
        screen.blit(scaled_title, rect)
        screen.blit(sub_surf, sub_rect)

        pygame.display.flip()
        clock.tick(10)




def ask(screen, question):
  "ask(screen, question) -> answer"
  pygame.font.init()
  current_string = []
  display_box(screen, question + ": " + "".join(current_string))
  while 1:
    inkey = get_key()
    if inkey == pygame.K_BACKSPACE:
      current_string = current_string[0:-1]
    elif inkey == pygame.K_RETURN:
      break
    elif inkey == pygame.K_MINUS:
      current_string.append("_")
    elif inkey <= 127:
      current_string.append(chr(inkey))
    display_box(screen, question + ": " + "".join(current_string))
  return "".join(current_string)


def start_game():
    start = pygame.display.set_mode((320,240))
    level_str = ask(start, "Select Level")
    
    # Convert to integer safely
    try:
        level = int(level_str)
    except ValueError:
        print(f"ERROR: Invalid Level: {level_str}")
        sys.exit(2)
        
        
    if level > 0:
        return level
    else:
        print ("ERROR: Invalid Level: "+str(level))
        sys.exit(2)

TILE_SIZE = 64  # make sure this matches what you used in load_size() and print_game()

# Get absolute path to assets folder
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")

wall = pygame.transform.scale(pygame.image.load(os.path.join(ASSETS_DIR, "wall.ico")), (TILE_SIZE, TILE_SIZE))
floor = pygame.transform.scale(pygame.image.load(os.path.join(ASSETS_DIR, "floor.ico")), (TILE_SIZE, TILE_SIZE))
box = pygame.transform.scale(pygame.image.load(os.path.join(ASSETS_DIR, "box.ico")), (TILE_SIZE, TILE_SIZE))
box_docked = pygame.transform.scale(pygame.image.load(os.path.join(ASSETS_DIR, "box_docked.ico")), (TILE_SIZE, TILE_SIZE))
worker = pygame.transform.scale(pygame.image.load(os.path.join(ASSETS_DIR, "worker.ico")), (TILE_SIZE, TILE_SIZE))
worker_docked = pygame.transform.scale(pygame.image.load(os.path.join(ASSETS_DIR, "worker_dock.ico")), (TILE_SIZE, TILE_SIZE))
docker = pygame.transform.scale(pygame.image.load(os.path.join(ASSETS_DIR, "dock.ico")), (TILE_SIZE, TILE_SIZE))

background = 255, 226, 191

# Center the window on screen
import os
os.environ['SDL_VIDEO_CENTERED'] = '1'

pygame.init()

# Allow launching with a level argument
if len(sys.argv) > 1:
    try:
        level = int(sys.argv[1])
        print(f"Starting Sokoban Level {level}")
    except ValueError:
        print("Invalid level argument, starting at level 1")
        level = 1
else:
    level = start_game()  # fallback if no level passed


LEVELS_PATH = os.path.join(os.path.dirname(__file__), "levels")
game = game(LEVELS_PATH, level)

size = game.load_size()

screen = pygame.display.set_mode(size)
while 1:
    if game.is_completed():
        display_end(screen)  # show animation
        pygame.quit()        # close the window properly
        sys.exit(0)          # end the game after completion
    print_game(game.get_matrix(), screen)
    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit(0)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP: game.move(0,-1, True)
            elif event.key == pygame.K_DOWN: game.move(0,1, True)
            elif event.key == pygame.K_LEFT: game.move(-1,0, True)
            elif event.key == pygame.K_RIGHT: game.move(1,0, True)
            elif event.key == pygame.K_q: sys.exit(0)
            elif event.key == pygame.K_d: game.unmove()
           
    pygame.display.update()
