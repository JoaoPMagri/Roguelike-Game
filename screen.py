import pygame
import random
from pygame.locals import *
from sys import exit
from map_generator import Map

pygame.init()

largura = 1200
altura = 600

tela = pygame.display.set_mode((largura,altura))
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

            if tile == '#':
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


tile_size = 30

mapa = Map(width=40, height=20, seed=42)
mapa.generate()

grid = mapa.grid

walls, player_x, player_y, exit_x, exit_y = load_map(grid, tile_size)

while True:
    relogio.tick(60)
    tela.fill((0,0,255))
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
    
    circulo = pygame.Rect(new_x-7.5,new_y-7.5,15,15)
    exit_hole = pygame.Rect(exit_x-7.5,exit_y-7.5,15,15)
    possible = True

    for rect in walls:
        pygame.draw.rect(tela, "gray", rect)
        if rect.colliderect(circulo):
            possible = False

    
    if possible:
        player_x = new_x
        player_y = new_y
    
    pygame.draw.circle(tela,(0,0,0),(exit_x,exit_y),7.5)
    pygame.draw.circle(tela,(255,0,0),(player_x,player_y),7.5)

    pygame.display.update()

    if circulo.colliderect(exit_hole):
        mapa = Map(width=40, height=20)  # nova seed automática
        mapa.generate()
        grid = mapa.grid
        walls, player_x, player_y, exit_x, exit_y = load_map(grid, tile_size)
