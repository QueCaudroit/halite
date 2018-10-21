#!/usr/bin/env python3
import hlt
from hlt import constants
from hlt.positionals import Direction, Position
import random
import logging

""" <<<Game Begin>>> """
game = hlt.Game()
game_map = game.game_map

def get_task(ship, game_map, my_dropoffs_positions, last_task, best_spots):
    #if ship.halite_amount > 900:
    #    return 'deliver'
    if game_map[ship.position].halite_amount / 10 > ship.halite_amount:
        return 'collect'
    if ship.position in my_dropoffs_positions:
        return 'chose_spot'
    if ship.is_full:
        return 'deliver'
    if ship.id in last_task and last_task[ship.id] == 'deliver':
        return 'deliver'
    if game_map[ship.position].halite_amount >= 100:
        return 'collect'
    if ship.target is not None:
        # if ship.target not in best_spots:
        #     return 'chose_spot'
        return 'travel_to_spot'
    return 'chose_spot'

def random_safe_move(ship, game_map):
    possible_vect = [
        Position(1, 1),
        Position(1, -1),
        Position(-1, 1),
        Position(-1, -1)
    ]
    return game_map.naive_navigate(ship, random.choice(possible_vect), 0)

def deliver(ship, game_map, my_dropoffs_positions, spots_taken):
    if ship.target is not None:
        spots_taken.remove(ship.target)
        ship.target = None
    dist = 70000
    best_vect = None
    for dropoff_pos in my_dropoffs_positions:
        new_dist, vect = game_map.calculate_distance(ship.position, dropoff_pos)
        if new_dist >= dist:
            continue
        dist = new_dist
        best_vect = vect
    return game_map.naive_navigate(ship, best_vect, 2)

def chose_spot(ship, game_map, best_spots, spots_taken):
    if ship.target is not None:
        spots_taken.remove(ship.target)
    dist = 70000
    best_vect = None
    if len(spots_taken) >= len(best_spots):
        logging.info('problem!')
    for spot in best_spots:
        if spot in spots_taken:
            continue
        new_dist, vect = game_map.calculate_distance(ship.position, spot)
        if new_dist >= dist:
            continue
        dist = new_dist
        best_vect = vect
        ship.target = spot
        spots_taken.append(spot)
    return travel_to_spot(ship, game_map)

def travel_to_spot(ship, game_map):
    new_dist, vect = game_map.calculate_distance(ship.position, ship.target)
    return game_map.naive_navigate(ship, vect, 0)

def collect(ship, game_map):
    game_map[ship.position].mark_unsafe(ship, 0)
    return Direction.Still

last_task = {}
tasks = {
    'collect': [],
    'deliver': [],
    'random safe move': [],
    'travel_to_spot': [],
    'chose_spot': []
}
spots_taken = []
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
    my_ships.sort(key=lambda x: x.halite_amount, reverse=True)
    best_spots = game_map.get_best_halite(len(my_ships))
    logging.info(best_spots)
    tasks = {
        'collect': [],
        'deliver': [],
        'random safe move': [],
        'travel_to_spot': [],
        'chose_spot': []
    }
    for ship in my_ships:
        task = get_task(ship, game_map, my_dropoffs_positions, last_task, best_spots)
        logging.info((ship.id, ship.halite_amount, task))
        last_task[ship.id] = task
        tasks[task].append(ship)
    for ship in tasks['collect']:
        command_queue.append(ship.move(collect(ship, game_map)))
    for ship in tasks['deliver']:
        command_queue.append(ship.move(deliver(ship, game_map, my_dropoffs_positions, spots_taken)))
    for ship in tasks['random safe move']:
        command_queue.append(ship.move(random_safe_move(ship, game_map)))
    for ship in tasks['travel_to_spot']:
        command_queue.append(ship.move(travel_to_spot(ship, game_map)))
    for ship in tasks['chose_spot']:
        command_queue.append(ship.move(chose_spot(ship, game_map, best_spots, spots_taken)))
    if game.turn_number <= 200 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied(0):
        command_queue.append(me.shipyard.spawn())

    game.end_turn(command_queue)
