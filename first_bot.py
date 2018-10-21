#!/usr/bin/env python3
import hlt
from hlt import constants
from hlt.positionals import Direction, Position
import random
import logging

""" <<<Game Begin>>> """
game = hlt.Game()
game_map = game.game_map

def get_task(ship, game_map, my_dropoffs_positions, last_task):
    #if ship.halite_amount > 900:
    #    return 'deliver'
    #if game_map[ship.position].halite_amount > ship.halite_amount / 10:
    #    return 'collect'
    if ship.position in my_dropoffs_positions:
        return 'random safe move'
    if ship.halite_amount > 900:
        return 'deliver'
    if game_map[ship.position].halite_amount >= 100:
        return 'collect'
    if ship.id in last_task and last_task[ship.id] == 'deliver':
        return 'deliver'
    return 'random safe move'

def random_safe_move(ship, game_map):
    possible_vect = [
        Position(1, 1),
        Position(1, -1),
        Position(-1, 1),
        Position(-1, -1)
    ]
    return game_map.naive_navigate(ship, random.choice(possible_vect), 0)

def deliver(ship, game_map, my_dropoffs_positions):
    dist = 70000
    best_vect = None
    for dropoff_pos in my_dropoffs_positions:
        new_dist, vect = game_map.calculate_distance(ship.position, dropoff_pos)
        if new_dist >= dist:
            continue
        dist = new_dist
        best_vect = vect
    return naive_navigate(ship, best_vect, 2)


last_task = {}
game.ready("MyPythonBot")
my_id = game.my_id
logging.info("Successfully created bot! My Player ID is {}.".format(my_id))
""" <<<Game Loop>>> """

while True:
    game.update_frame()
    me = game.players[my_id]
    my_dropoffs_positions = list(map(lambda x: x.position, me.get_dropoffs()))
    my_dropoffs_positions.append(me.shipyard.position)
    game_map = game.game_map
    command_queue = []
    my_ships = me.get_ships()
    all_ships = []
    for i, player in game.players.items():
        all_ships = all_ships + player.get_ships()
    for ship in me.get_ships():
        task = get_task(ship, game_map, my_dropoffs_positions, last_task)
        logging.info((ship.id, ship.halite_amount, task))
        last_task[ship.id] = task
        if task == 'collect':
            command_queue.append(ship.stay_still())
        if task == 'deliver':
            command_queue.append(ship.move(deliver(ship, all_ships, my_dropoffs_positions)))
        if task == 'random safe move':
            command_queue.append(ship.move(random_safe_move(ship, all_ships)))
    if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied(0):
        command_queue.append(me.shipyard.spawn())

    game.end_turn(command_queue)
