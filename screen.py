import pygame
import random
from pygame.locals import *
from sys import exit
from maps_generator.mapGenerator import MapGenerator
from maps_generator.bsp import Bsp
from maps_generator.randomWalk import RandomWalk
from maps_generator.cellularAutomata import CellularAutomata
from maps_generator.hybridGenerator import HybridGenerator

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

def load_map(mapa, tile_size):
    walls = []
    floors = []
    player_x = player_y = 0
    exit_x = exit_y = 0
    player_found = False

    map_floors = mapa.get_floors()
    map_walls = mapa.get_walls()

    for x,y in map_floors:
        px = x * tile_size
        py = y * tile_size
        floors.append(pygame.Rect(px, py, tile_size, tile_size))
        if not player_found:
            player_x = px + tile_size / 2
            player_y = py + tile_size / 2
            player_found = True
        else:
            exit_x = px + tile_size / 2
            exit_y = py + tile_size / 2
    
    for x,y in map_walls:
        walls.append(pygame.Rect(x*tile_size, y*tile_size, tile_size, tile_size))

    return walls, player_x, player_y, exit_x, exit_y, floors

initial_map = MapGenerator(width=WIDTH//30,height=HEIGHT//30,seed=seed)

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

initial_map.grid = grid
walls, player_x, player_y, exit_x, exit_y, floors = load_map(initial_map, TILE_SIZE)

def get_mapa(map_type):
    width = WIDTH // TILE_SIZE
    height = HEIGHT // TILE_SIZE
    if map_type == 0:
        mapa = RandomWalk(width=width,height=height,iterations=width*height*4//5,seed=seed)
        mapa.generate()
        return mapa
    elif map_type == 1:
        mapa = CellularAutomata(width=width,height=height,iterations=4,density=0.45,seed=seed)
        mapa.generate()
        return mapa
    elif map_type == 2:
        mapa = Bsp(width=width,height=height,seed=seed,min_leaf_size=MIN_LEAF_SIZE)
        mapa.generate()
        return mapa
    elif map_type == 3:
        mapa = HybridGenerator(width=width,height=height,seed=seed,min_leaf_size=MIN_LEAF_SIZE,density=0.7,iterations=3)
        mapa.generate()
        return mapa
    else:
        mapa1 = Bsp(width=width//2,height=height,seed=seed,min_leaf_size=MIN_LEAF_SIZE)
        mapa1.generate()
        mapa2 = CellularAutomata(width=width//2,height=height,seed=seed,density=0.55,iterations=2)
        mapa2.generate()
        mapa = MapGenerator(width=width,height=height,seed=seed)
        mapa.join_maps([mapa1,mapa2])
        return mapa
        

while True:
    relogio.tick(60)
    tela.fill((0,0,0))
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
        mapa = get_mapa(map_type)
        walls, player_x, player_y, exit_x, exit_y, floors = load_map(mapa, TILE_SIZE)
        new_x = player_x
        new_y = player_y
    elif keys[pygame.K_c]:
        map_type = 1
        mapa = get_mapa(map_type)
        walls, player_x, player_y, exit_x, exit_y, floors = load_map(mapa, TILE_SIZE)
        new_x = player_x
        new_y = player_y
    elif keys[pygame.K_b]:
        map_type = 2
        mapa = get_mapa(map_type)
        walls, player_x, player_y, exit_x, exit_y, floors = load_map(mapa, TILE_SIZE)
        new_x = player_x
        new_y = player_y
    elif keys[pygame.K_m]:
        map_type = 3
        mapa = get_mapa(map_type)
        walls, player_x, player_y, exit_x, exit_y, floors = load_map(mapa, TILE_SIZE)
        new_x = player_x
        new_y = player_y
    elif keys[pygame.K_j]:
        map_type = 4
        mapa = get_mapa(map_type)
        walls, player_x, player_y, exit_x, exit_y, floors = load_map(mapa, TILE_SIZE)
        new_x = player_x
        new_y = player_y
    
    circulo = pygame.Rect(new_x-7.5,new_y-7.5,15,15)
    exit_hole = pygame.Rect(exit_x-7.5,exit_y-7.5,15,15)
    possible = True

    for rect in floors:
        pygame.draw.rect(tela, (0,102,0), rect)

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
        mapa = get_mapa(map_type)
        walls, player_x, player_y, exit_x, exit_y, floors = load_map(mapa, TILE_SIZE)
