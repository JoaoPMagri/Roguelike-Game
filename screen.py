import pygame
import random
from pygame.locals import *
from sys import exit
from maps_generator.BSP import BSP
from maps_generator.MapGenerator import MixedGenerator
from maps_generator.RandomWalk import RandomWalk
from maps_generator.CellularAutomata import CellularAutomata

pygame.init()

WIDTH = 1200
HEIGHT = 600
seed = random.random()
TILE_SIZE = 30
MIN_LEAF_SIZE = 8
map_type = 0
rng = random.Random(seed)

tela = pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption('Teste')
relogio = pygame.time.Clock()

def load_map(grid, tile_size):
    walls = []
    player_x = player_y = 0
    exit_x = exit_y = 0
    player_found = False

    for y, linha in enumerate(grid):
        for x, tile in enumerate(linha):
            px = x * tile_size
            py = y * tile_size

            if tile == '#' or tile == '+' or tile == '_':
                walls.append(pygame.Rect(px, py, tile_size, tile_size))

            elif tile == '.':
                if not player_found:
                    player_x = px + tile_size / 2
                    player_y = py + tile_size / 2
                    player_found = True
                else:
                    exit_x = px + tile_size / 2
                    exit_y = py + tile_size / 2

    return walls, player_x, player_y, exit_x, exit_y



grid = [ ['.' for _ in range(WIDTH//30)] for _ in range(HEIGHT//30)]

letters = {
            0: [0,4,6,7,8,9,10,12,13,14,15,16], 1: [0,1,3,4,6,10,12,16], 
            2: [0,2,4,6,7,8,9,10,12,13,14,15,16], 3: [0,4,6,10,12],
            4: [0,4,6,10,12], 6: [0,1,2,3,4,6,7,8,9,10,12,16],
            7: [0,6,12,13,16], 8: [0,3,4,6,7,8,9,12,14,16],
            9: [0,4,6,12,15,16], 10: [0,1,2,3,4,6,7,8,9,10,12,16], 
        }

for key, list in letters.items():
    y = key + 5
    for valor in list:
        x = valor + 12
        grid[y][x] = '#'

walls, player_x, player_y, exit_x, exit_y = load_map(grid, TILE_SIZE)

def get_grid(map_type):
    if map_type == 0:
        mapa = RandomWalk(width=WIDTH//30,height=HEIGHT//30,iterations=500,seed=seed)
        mapa.generate()
        return mapa.grid
    elif map_type == 1:
        mapa = CellularAutomata(width=WIDTH//30,height=HEIGHT//30,iterations=5,density=0.45,seed=seed)
        mapa.generate()
        return mapa.grid
    elif map_type == 2:
        mapa = BSP(width=WIDTH//30,height=HEIGHT//30,seed=seed,min_leaf_size=MIN_LEAF_SIZE,min_room_size=MIN_LEAF_SIZE-2)
        mapa.generate()
        return mapa.grid
    else:
        mapa = MixedGenerator(width=WIDTH//30,height=HEIGHT//30,seed=seed,
                              min_leaf_size=MIN_LEAF_SIZE,min_room_size=MIN_LEAF_SIZE-2,generators=["MIXED_CA_RW"])
        mapa.generate()
        return mapa.grid
        

while True:
    relogio.tick(60)
    tela.fill((0,102,0))
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            exit()
     
    new_x = player_x
    new_y = player_y
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        new_y = player_y - 2
    elif keys[pygame.K_s]:
        new_y = player_y + 2
    elif keys[pygame.K_a]:
        new_x = player_x - 2
    elif keys[pygame.K_d]:
        new_x = player_x + 2
    elif keys[pygame.K_r]:
        map_type = 0
        grid = get_grid(map_type)
        walls, player_x, player_y, exit_x, exit_y = load_map(grid, TILE_SIZE)
    elif keys[pygame.K_c]:
        map_type = 1
        grid = get_grid(map_type)
        walls, player_x, player_y, exit_x, exit_y = load_map(grid, TILE_SIZE)
    elif keys[pygame.K_b]:
        map_type = 2
        grid = get_grid(map_type)
        walls, player_x, player_y, exit_x, exit_y = load_map(grid, TILE_SIZE)
    elif keys[pygame.K_m]:
        map_type = 3
        grid = get_grid(map_type)
        walls, player_x, player_y, exit_x, exit_y = load_map(grid, TILE_SIZE)
    
    circulo = pygame.Rect(new_x-7.5,new_y-7.5,15,15)
    exit_hole = pygame.Rect(exit_x-7.5,exit_y-7.5,15,15)
    possible = True

    for rect in walls:
        pygame.draw.rect(tela, (102,102,102), rect)
        if rect.colliderect(circulo):
            possible = False

    if possible:
        player_x = new_x
        player_y = new_y
    
    pygame.draw.circle(tela,(0,0,0),(exit_x,exit_y),7.5)
    pygame.draw.circle(tela,(255,0,0),(player_x,player_y),7.5)

    pygame.display.update()

    if circulo.colliderect(exit_hole):
        seed = rng.random()
        grid = get_grid(map_type)
        walls, player_x, player_y, exit_x, exit_y = load_map(grid, TILE_SIZE)
