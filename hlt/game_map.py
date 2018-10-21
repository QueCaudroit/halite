import queue

from . import constants
from .entity import Entity, Shipyard, Ship, Dropoff
from .positionals import Direction, Position
from .common import read_input
import logging
import random
import numpy as np


class Player:
    """
    Player object containing all items/metadata pertinent to the player.
    """
    def __init__(self, player_id, shipyard, halite=0):
        self.id = player_id
        self.shipyard = shipyard
        self.halite_amount = halite
        self._ships = {}
        self._dropoffs = {}

    def get_ship(self, ship_id):
        """
        Returns a singular ship mapped by the ship id
        :param ship_id: The ship id of the ship you wish to return
        :return: the ship object.
        """
        return self._ships[ship_id]

    def get_ships(self):
        """
        :return: Returns all ship objects in a list
        """
        return list(self._ships.values())

    def get_dropoff(self, dropoff_id):
        """
        Returns a singular dropoff mapped by its id
        :param dropoff_id: The dropoff id to return
        :return: The dropoff object
        """
        return self._dropoffs[dropoff_id]

    def get_dropoffs(self):
        """
        :return: Returns all dropoff objects in a list
        """
        return list(self._dropoffs.values())

    def has_ship(self, ship_id):
        """
        Check whether the player has a ship with a given ID.

        Useful if you track ships via IDs elsewhere and want to make
        sure the ship still exists.

        :param ship_id: The ID to check.
        :return: True if and only if the ship exists.
        """
        return ship_id in self._ships


    @staticmethod
    def _generate():
        """
        Creates a player object from the input given by the game engine
        :return: The player object
        """
        player, shipyard_x, shipyard_y = map(int, read_input().split())
        return Player(player, Shipyard(player, -1, Position(shipyard_x, shipyard_y)))

    def _update(self, num_ships, num_dropoffs, halite):
        """
        Updates this player object considering the input from the game engine for the current specific turn.
        :param num_ships: The number of ships this player has this turn
        :param num_dropoffs: The number of dropoffs this player has this turn
        :param halite: How much halite the player has in total
        :return: nothing.
        """
        self.halite_amount = halite
        self._ships = {id: ship for (id, ship) in [Ship._generate(self.id) for _ in range(num_ships)]}
        self._dropoffs = {id: dropoff for (id, dropoff) in [Dropoff._generate(self.id) for _ in range(num_dropoffs)]}


class MapCell:
    """A cell on the game map."""
    def __init__(self, position, halite_amount):
        self.position = position
        self.halite_amount = halite_amount
        self.ships = [[], [], []]
        self.structure = None

    def is_empty(self, level):
        """
        :return: Whether this cell has no ships or structures
        """
        return not self.is_occupied(level) and self.structure is None

    def is_occupied(self, level):
        """
        :return: Whether this cell has any ships
        """
        occupation_count = 0
        for i in range(level + 1):
            occupation_count += len(self.ships[i])
        return occupation_count > 0

    @property
    def has_structure(self):
        """
        :return: Whether this cell has any structures
        """
        return self.structure is not None

    @property
    def structure_type(self):
        """
        :return: What is the structure type in this cell
        """
        return None if not self.structure else type(self.structure)

    def mark_unsafe(self, ship, level):
        """
        Mark this cell as unsafe (occupied) for navigation.

        Use in conjunction with GameMap.naive_navigate.
        """
        self.ships[level].append(ship)
        if level == 0 and len(self.ships[0]) > 1:
            logging.info('cell %s already marked unafe level 0. Crash is imminent')

    def mark_safe(self, ship, level):
        for l in range(level + 1):
            new_ships = []
            for other_ship in self.ships[l]:
                if other_ship.id != ship.id:
                    new_ships.append(other_ship)
            self.ships[l] = new_ships



    def __eq__(self, other):
        return self.position == other.position

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return 'MapCell({}, halite={})'.format(self.position, self.halite_amount)


class GameMap:
    """
    The game map.

    Can be indexed by a position, or by a contained entity.
    Coordinates start at 0. Coordinates are normalized for you
    """
    def __init__(self, cells, width, height):
        self.width = width
        self.height = height
        self._cells = cells
        self.halite_array = np.zeros((self.width, self.height))

    def __getitem__(self, location):
        """
        Getter for position object or entity objects within the game map
        :param location: the position or entity to access in this map
        :return: the contents housing that cell or entity
        """
        if isinstance(location, Position):
            location = self.normalize(location)
            return self._cells[location.y][location.x]
        elif isinstance(location, Entity):
            return self._cells[location.position.y][location.position.x]
        return None

    def calculate_distance(self, source, target):
        """
        Compute the Manhattan distance between two locations.
        Accounts for wrap-around.
        :param source: The source from where to calculate
        :param target: The target to where calculate
        :return: The distance between these items
        """
        vect = target - source
        vect_n = self.normalize(vect)
        if vect_n.x > self.width / 2:
            move_x = vect_n.x - self.width
        else:
            move_x = vect_n.x
        if vect_n.y > self.height / 2:
            move_y = vect_n.y - self.height
        else:
            move_y = vect_n.y
        dist = abs(move_x) + abs(move_y)
        return dist, Position(move_x, move_y)

    def normalize(self, position):
        """
        Normalized the position within the bounds of the toroidal map.
        i.e.: Takes a point which may or may not be within width and
        height bounds, and places it within those bounds considering
        wraparound.
        :param position: A position object.
        :return: A normalized position object fitting within the bounds of the map
        """
        return Position(position.x % self.width, position.y % self.height)

    def naive_navigate(self, ship, vect, level):
        """
        Returns a singular safe move towards the destination.

        :param ship: The ship to move.
        :param destination: Ending position
        :return: A direction.
        """
        self[ship.position].mark_safe(ship, 2)
        directions = [Direction.North, Direction.South, Direction.East, Direction.West, Direction.Still]
        possible_directions = []
        for direction in directions:
            position = self.normalize(ship.position.directional_offset(direction))
            if not self[position].is_occupied(level):
                possible_directions.append(direction)
        possible_moves = []
        if vect.x > 0 and Direction.East in possible_directions:
            possible_moves = possible_moves + [Direction.East] * int(vect.x)
        if vect.x < 0 and Direction.West in possible_directions:
            possible_moves = possible_moves + [Direction.West] * int(-vect.x)
        if vect.y > 0 and Direction.South in possible_directions:
            possible_moves = possible_moves + [Direction.South] * int(vect.y)
        if vect.y < 0 and Direction.North in possible_directions:
            possible_moves = possible_moves + [Direction.North] * int(-vect.y)
        if len(possible_moves) == 0:
            possible_moves += possible_directions
        if len(possible_moves) == 0:
            logging.info('no place left, gonna crash')
            possible_moves.append(Direction.Still)
        direction = random.choice(possible_moves)
        target_pos = ship.position.directional_offset(direction)
        self[target_pos].mark_unsafe(ship, 0)
        return direction

    def get_best_halite(self, n):
        flat_array = self.halite_array.flatten()
        flat_indices = flat_array.argsort()[len(flat_array) - n:]
        best_pos = []
        for i in flat_indices:
            best_pos.append(Position(i // self.height, i % self.height))
        return best_pos

    def mean_halite(self):
        return np.mean(self.halite_array)

    @staticmethod
    def _generate():
        """
        Creates a map object from the input given by the game engine
        :return: The map object
        """
        map_width, map_height = map(int, read_input().split())
        game_map = [[None for _ in range(map_width)] for _ in range(map_height)]
        for y_position in range(map_height):
            cells = read_input().split()
            for x_position in range(map_width):
                game_map[y_position][x_position] = MapCell(Position(x_position, y_position),
                                                           int(cells[x_position]))
        return GameMap(game_map, map_width, map_height)

    def _update(self):
        """
        Updates this map object from the input given by the game engine
        :return: nothing
        """
        # Mark cells as safe for navigation (will re-mark unsafe cells
        # later)
        for y in range(self.height):
            for x in range(self.width):
                self[Position(x, y)].ships = [[], [], []]

        self.halite_array = np.zeros((self.width, self.height))
        for _ in range(int(read_input())):
            cell_x, cell_y, cell_energy = map(int, read_input().split())
            self[Position(cell_x, cell_y)].halite_amount = cell_energy
            self.halite_array[cell_x, cell_y] = cell_energy
