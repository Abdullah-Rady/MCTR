import itertools
import numpy as np
import math
from queue import Queue


# Constants
minimum_collision_distance = 1  # Minimum distance between any two points to avoid collisions
maximum_energy = 100  # Maximum allowable total energy consumption per drone
constant_speed = 1.0  # Constant speed of the drones
energy_weight = 1  # Weight for energy consumption in the fitness function
energy_per_distance = 1.0  # Energy consumed per unit distance traveled
tolerance = 1.0  # douglas_peucker
separation = 1  # separation between drones




def bresenham3D(point1, point2):
    points = []
    x1, y1, z1 = point1
    x2, y2, z2 = point2
    # Calculate differences and absolute differences
    dx = x2 - x1
    dy = y2 - y1
    dz = z2 - z1

    gcd_abc = math.gcd(math.gcd(dx, dy), dz)

    # Divide each integer by the GCD
    simplified_dx = dx // gcd_abc
    simplified_dy = dy // gcd_abc
    simplified_dz = dz // gcd_abc



    # Set the starting point
    x, y, z = x1, y1, z1
    points.append((x1, y1, z1))
    while x != x2 or y != y2 or z != z2:
        # Add the current point to the list of points
        x += simplified_dx
        y += simplified_dy
        z += simplified_dz
        points.append((x, y, z))

    return points



def euclidean_distance(start_point, end_point):
    return ((start_point[0] - end_point[0]) ** 2 + (start_point[1] - end_point[1]) ** 2 + (start_point[2] - end_point[2]) ** 2) ** 0.5


def calculate_single_path_distance(control_points):
    """
    Calculate the total distance for a single path x.

    Parameters:
        control_points (list of 3D tuples): A list of 3D control points defining the path.

    Returns:
        float: The total distance traveled along the path.

    """
    return sum(euclidean_distance(control_points[i], control_points[i + 1]) for i in range(len(control_points) - 1))


def calculate_single_path_fitness(control_points):
    """
    Calculate the total distance and energy consumption for a single path x.

    Parameters:
    control_points (list of 3D tuples): A list of 3D control points defining the path.

    Returns:
        float: The fitness value for the path.
    """

    num_points = len(control_points)
    if num_points < 2:
        return 0.0  # No movement if there are no control points

    total_distance = calculate_single_path_distance(control_points)

    # Calculate energy consumption based on distance
    energy_consumed = total_distance * energy_per_distance

    # Calculate the fitness value as a weighted sum of time and energy
    fitness = total_distance + energy_weight * energy_consumed

    return fitness


def calculate_total_fitness(drone_paths):
    """
    Calculate the total distance for multiple drones' paths.

    Parameters:
    drone_paths (list of lists  of 3D points): A list of paths, where each path is defined as a list of 3D control points.

    Returns:
    float: The total fitness of the paths.
    """
    total_fitness = 0.0
    for path in drone_paths:
        fitness = calculate_single_path_fitness(path)
        total_fitness += fitness
    return total_fitness


def check_energy_constraint(drone_paths):
    """
    Check if the total energy consumed by all drones satisfies the energy constraint.

    Args:
        drone_paths (list): List of drone paths where each path is a list of 3D points.
        constant_speed (float): Constant speed of the drones.

    Returns:
        bool: True if the energy constraint is satisfied, False otherwise.
    """

    for path in drone_paths:
        total_distance = calculate_single_path_distance(path)
        energy_consumed = total_distance * energy_per_distance

        if energy_consumed > maximum_energy:
            return False  # Energy constraint is violated

    return True  # Energy constraint is satisfied



def check_feasibility(drone_tag, grid, drone_occupancy, drone_path, old_point_index, new_point,starting_point,target_point):
    """
    Check if the solution is feasible.

    Args:

    drone_paths (list): List of drone paths where each path is a list of 3D points.
    obstacle_list (list): List of obstacle representations.
    path_index (int): Index of the path modified.
    point_index (int): Index of the point modified in the path.

    Returns:
        bool: True if the solution is feasible, False otherwise.
    """

    #remove all points where drone_tag exists regardless of layer

    x, y, z = new_point
    admissible = 0 <= x < len(grid) and 0 <= y < len(grid) and 0 <= z < len(grid) and grid[x][y][z] == 0

    if(not admissible):
        return False
    
    drone_occupancy_copy = drone_occupancy.copy()
    point_before_edited_point = drone_path[old_point_index-1]
    point_after_edited_point = drone_path[old_point_index+1]

    points = bresenham3D(point_before_edited_point, point_after_edited_point)
    for (x, y, z) in points:
    # for x in range(point_before_edited_point[0],point_after_edited_point[0]+1):
    #     for y in range(point_before_edited_point[1],point_after_edited_point[1]+1):
    #         for z in range(point_before_edited_point[2],point_after_edited_point[2]+1):
        drones_in_cell = drone_occupancy_copy[x][y][z]
        for i in range(drones_in_cell):
            if drones_in_cell[i][0] == drone_tag:
                drone_occupancy_copy.remove(drones_in_cell[i])

    path_before_new_point = get_single_path_with_bfs(point_before_edited_point,new_point,grid,drone_occupancy_copy)
    if(len(path_before_new_point)==0):
        return False
    
    simplified_path_before_new_point = douglas_peucker(path_before_new_point)
    depth = 2
    for point in path_before_new_point:
        if point in [starting_point, target_point]:
            continue
        x, y, z = point
        drone_occupancy_copy[x][y][z].append((drone_tag, depth))
        depth += 1
    path_after_new_point = get_single_path_with_bfs(new_point, point_after_edited_point,grid,drone_occupancy_copy)

    if(len(path_after_new_point)==0):

        return False
    
    simplified_path_after_new_point = douglas_peucker(path_after_new_point)

    for point in path_after_new_point:
        if point in [starting_point, target_point]:
            continue
        x, y, z = point
        drone_occupancy_copy[x][y][z].append((drone_tag, depth))
        depth += 1

    for i in range(old_point_index + 2, len(drone_path), 1):
        x, y, z = drone_path[i]
        drones_in_cell = drone_occupancy_copy[x][y][z]
        for j in range(drones_in_cell):
            if drones_in_cell[i][0] == drone_tag:
                drone_occupancy_copy.remove(drones_in_cell[i])
                drone_occupancy_copy[x][y][z].append((drone_tag, depth))
                depth += 1

    # for x in range(point_after_edited_point[0],len(drone_occupancy)):
    #     for y in range(point_after_edited_point[1],len(drone_occupancy)):
    #         for z in range(point_after_edited_point[2],len(drone_occupancy)):
    last_index_before = 0
    drone_occupancy = drone_occupancy_copy
    for i in range(1, len(simplified_path_before_new_point)):
        drone_path.insert(i+old_point_index, simplified_path_before_new_point[i])
        last_index_before = i


    for i in range(1, len(simplified_path_after_new_point) - 1):
        drone_path.insert(i + last_index_before + old_point_index, simplified_path_after_new_point[i])

    return True







    # for i in range(len(drone_paths)):
    #     if i == path_index:
    #         continue
    #     path1 = drone_paths[i]
    #     point = drone_paths[path_index][point_index]
    #     for point1 in path1:
    #         if euclidean_distance(point1, point) < minimum_collision_distance:
    #             return False
    # for obstacle in obstacle_list:
    #     point = drone_paths[path_index][point_index]
    #     for i, j in itertools.product(range(obstacle[0][0], obstacle[1][0] + separation + 1), range(obstacle[0][1], obstacle[1][1] + separation + 1)):
    #         for k in range(obstacle[0][2], obstacle[1][2] + separation + 1):
    #             if euclidean_distance(point, (i, j, k)) < minimum_collision_distance:
    #                 return False
    return True


def build_grid(obstacles, size_of_grid):
    """
    Args:
        obstacles (list): List of obstacle representations.
        size_of_grid (int): Size of the 3D grid representation of the environment.
    Returns:
        list: A 3D grid representation of the environment.
    Builds a grid representation of the environment.
    0: Free space
    1: Obstacle
    """ 
    grid = [[[0 for _ in range(size_of_grid)] for _ in range(size_of_grid)] for _ in range(size_of_grid)]
    # Set all obstacles to 1
    for obstacle in obstacles:
        for i, j in itertools.product(range(obstacle[0][0], obstacle[1][0] + separation + 1 ), range(obstacle[0][1], obstacle[1][1]  + separation + 1)):
            for k in range(obstacle[0][2], obstacle[1][2] + separation + 1) :
                grid[i][j][k] = 1
    return grid


def get_single_path_with_bfs(starting_point, target_point, grid, drone_occupancy):
    """
    Get a path from the start point to the target point using BFS.

    Args:
        starting_point (tuple): The start point (x, y, z).
        target_point (tuple): The target point (x, y, z).
        grid (list): A 3D grid representation of the obstacle placement.
        drone_occupancy (list): A 3D grid representation of the drones placement.

    Returns:
        list: A list of control points defining the path.
    """


    def is_valid(parent, point, layer):
        x, y, z = point
        admissible = 0 <= x < len(grid) and 0 <= y < len(grid) and 0 <= z < len(grid) and grid[x][y][z] == 0
        if(not admissible):
           return False
        current_drones_occupying_cell = drone_occupancy[x][y][z]
        for current_drone_tag , current_drone_depth in current_drones_occupying_cell:
            if layer[parent] + 1 == current_drone_depth:
                return False
        return admissible

    def get_neighbors(point,layer):
        x, y, z = point
        neighbors = [(x + dx, y + dy, z + dz) for dx in [-1, 0, 1] for dy in [-1, 0, 1] for dz in [-1, 0, 1] if
                     (dx != 0 or dy != 0 or dz != 0)]
        return [neighbor for neighbor in neighbors if is_valid(point, neighbor,layer)]

    start = tuple(map(int, starting_point))
    target = tuple(map(int, target_point))
    queue = Queue()
    queue.put(start)
    came_from = {}
    came_from[start] = None
    layer = {}
    layer[start] = 2


    while not queue.empty():
        current = queue.get()

        if current == target:
            path = [current]
            while current != start:
                current = came_from[current]
                path.insert(0, current)
            return path

        for neighbor in get_neighbors(current,layer):
            if neighbor not in came_from:
                queue.put(neighbor)
                came_from[neighbor] = current   
                layer[neighbor] = layer[current] + 1

    return []


def get_all_paths_with_bfs(starting_points, target_points, grid):
    """
    Get all paths from the start points to the target points using BFS.

    Args:
        starting_points (list): A list of he start points (x, y, z).
        target_points (list): A list of the target points (x, y, z).
        grid (list): A 3D grid representation of the environment.

    Returns:
        list: A list of paths, where each path is a list of control points.
    """
    all_paths = []
    simplified_paths = []
    drone_occupancy = [[[ [] for _ in range(len(grid))] for _ in range(len(grid))] for _ in range(len(grid))]
    for drone_tag, (starting_point, target_point) in enumerate(zip(starting_points, target_points), start=1):
        drone_occupancy[starting_point[0]][starting_point[1]][starting_point[2]].append((drone_tag, 1))
        drone_occupancy[target_point[0]][target_point[1]][target_point[2]].append((drone_tag, 100))

    for drone_tag, (starting_point, target_point) in enumerate(zip(starting_points, target_points), start=1):
        path = get_single_path_with_bfs(starting_point, target_point, grid, drone_occupancy)
        
        depth = 2
        for point in path:
            if point in [starting_point, target_point]:
                continue
            x, y, z = point
            drone_occupancy[x][y][z].append((drone_tag, depth))
            depth += 1

        # print(path)
        simplified_path = douglas_peucker(path)
        print(simplified_path)
        all_paths.append(path)
        simplified_paths.append(simplified_path)

        
    return all_paths, drone_occupancy


def generate_initial_solution(size_of_grid, starting_points, target_points, obstacles):
    """
    Generate an initial solution to the problem using BFS.

    Args:
        starting_points (list): A list of he start points (x, y, z).
        target_points (list): A list of the target points (x, y, z).
        grid (list): A 3D grid representation of the environment.
    Returns:
        list: Initial solution.
    """
    grid = build_grid(obstacles, size_of_grid)
    paths, drone_occupancy = get_all_paths_with_bfs(starting_points, target_points, grid)

    return paths, grid , drone_occupancy








def douglas_peucker(points):
    """
    Applys douglas_peucker algorithm on generated points from bfs to lower the number of control points

    Args:
        points (list): A list of all paths generated by BFS.

    Returns:
        list: similar path with fewer number of control points.
    """
    if len(points) < 2:
        return 
    
    if len(points) <= 2:
        return [points[0], points[-1]]

    # Find the point farthest from the line connecting the start and end points
    max_distance = 0
    max_index = 0
    start, end = points[0], points[-1]

    for i in range(1, len(points) - 1):
        distance = euclidean_distance(points[i], start) + euclidean_distance(points[i], end)
        line_distance = euclidean_distance(start, end)
        d = distance - line_distance

        if d > max_distance:
            max_distance = d
            max_index = i

    if max_distance <= tolerance:
        return [start, end]
    # Recursively simplify the path
    first_segment = douglas_peucker(points[:max_index + 1])
    second_segment = douglas_peucker(points[max_index:])

    return first_segment[:-1] + second_segment  # Exclude the duplicated point
