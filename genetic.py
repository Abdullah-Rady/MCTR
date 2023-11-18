import random
import math
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation 
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from objective_function import calculate_total_fitness, generate_initial_solution, build_grid, tweak_path, tweak_path_crossover
from visualize import calculate_stats, plot_fitness_over_iterations, save_scenario_stats_to_json, visualize_problem_solution

#Genetic Algorithm Parameters
num_generations = 100
population_size  = 10
p_elite = 0.2
p_cross = 0.4
p_mutation = 0.4
# alpha = 0.7


num_crossover = int(p_cross * population_size)
num_mutation = int(p_mutation * population_size)
num_elite = int(p_elite * population_size)



def crossover(parent1, parent2, grid, drone_occ_1, drone_occ_2):
    remaining = [i for i in range(len(parent1) - 1)]
    child1 = None
    child2 = None
    while len(remaining) > 0:
        picked_x = random.choice(remaining)
        remaining.remove(picked_x)
        child1,child2,drone_occ_new_1,drone_occ_new_2 = tweak_path_crossover(parent1, parent2, picked_x, drone_occ_1, drone_occ_2, grid)
        if(len(child1)!= 0 and len(child2)!=0):
            return child1,child2,drone_occ_new_1,drone_occ_new_2
    else:
        return parent1,parent2, drone_occ_1,drone_occ_2



        
    


def mutate(gene, drone_occupancy, grid):
    random_r1 = random.randint(0, len(gene) - 1)
    new_path, new_drone_occupancy = tweak_path(gene, random_r1, drone_occupancy, gene[random_r1][0], gene[random_r1][-1], grid)
    if(len(new_path) != 0):
        gene[random_r1] = new_path
    return gene, new_drone_occupancy


def select_elite(population, fitness):
    elite_indices = list(np.argsort(fitness)[:num_elite])

    return [population[i] for i in elite_indices], elite_indices

def select_worst(population, fitness):
    worst_indices = list(np.argsort(fitness)[-1 * num_mutation:])

    return [population[index] for index in worst_indices],worst_indices




def fitness_proportionate_selection(population, fitness_scores, num_selected):
    # Calculate total fitness
    total_inverse_fitness = sum(1 / score for score in fitness_scores)    
    # Calculate selection probabilities
    selection_probabilities = [ (1/score) / total_inverse_fitness for score in fitness_scores]
    # Select individuals based on probabilities
    selected_indices = []
    for _ in range(num_selected):
        rand_num = random.random()
        cumulative_prob = 0
        # Iterate through individuals and check if they are selected
        for i, prob in enumerate(selection_probabilities):
            cumulative_prob += prob
            if rand_num <= cumulative_prob:
                selected_indices.append(i)
                break

    # Return the selected individuals
    selected_population = [population[i] for i in selected_indices]
    return selected_population, selected_indices


def generate_population(size_of_grid, starting_points, target_points, obstacles):
    population = []
    drone_occupancies = []
    grid = []
    for i in range(population_size):
        paths,grid, drone_occupancy = generate_initial_solution(size_of_grid, starting_points, target_points, obstacles)
        population.append(paths)
        drone_occupancies.append(drone_occupancy)
    return population, drone_occupancies,grid

def genetic(size_of_grid, starting_points, target_points, obstacles, visualize=False):
    population, drone_occupancies, grid = generate_population(size_of_grid, starting_points, target_points, obstacles)

    initial_solution = population[0]

    if visualize:
        print("Length of drone occupancies: ", len(drone_occupancies))

    for iteration in range(num_generations):
        fitness = []
        new_population = []
        new_drone_occupancies = []

        if visualize:
            print("Population size: ", len(population))
        for gene in population:
            fitness.append(calculate_total_fitness(gene))
        if visualize:
            print("All fitnesses: ", fitness)
        
        best_index = np.argmin(fitness)
        best_solution = population[best_index]
        best_fitness = fitness[best_index]
        
        if visualize:
            print(f"Iteration {iteration}: Best Fitness = {best_fitness}")
        
        new_population = []
        elites, elite_indices = select_elite(population, fitness)
        for i,elite in enumerate(elites):
            new_population.append(elite)
            new_drone_occupancies.append(drone_occupancies[elite_indices[i]])
        
        parents, indices = fitness_proportionate_selection(population, fitness, num_crossover)
        
        if visualize:
            print("Parents: ", parents)
        
        for i in range(0, len(parents), 2):

            if visualize:
                print("do i enter")
            
            # Select parents
            parent1 = parents[i]
            parent2 = parents[i + 1]
            # Perform crossover
            child1, child2, drone_occupancy_1,drone_occupancy_2 = crossover(parent1, parent2, grid, drone_occupancies[indices[i]], drone_occupancies[indices[i + 1]])
            new_drone_occupancies.append(drone_occupancy_1)
            new_drone_occupancies.append(drone_occupancy_2)
            new_population.append(child1)
            new_population.append(child2)
        # Perform mutation

        worst_genes, worst_gene_indices = select_worst(population, fitness)

        if visualize:
            print("Worst gene indices: ", worst_gene_indices)
            print("Worst genes indices size: ", len(worst_gene_indices))
        
        for i , gene in enumerate(worst_genes):
            if visualize:
                print("Index: ", i)

            gene_index = worst_gene_indices[i]
            new_gene, new_drone_occupancy = mutate(gene,drone_occupancies[gene_index],grid)
            if(len(new_gene) != 0):
                new_drone_occupancies.append(new_drone_occupancy)
                new_population.append(new_gene)
        population = new_population
        drone_occupancies = new_drone_occupancies
        
    return best_solution, best_fitness, population, initial_solution, fitness

size_of_grid1 = 30  # Size of the grid

# Define start points for the drones (x, y, z)
ps_list1 = [(5, 5, 5), (1, 10, 10), (20, 20, 20)]

# Define target points for the drones (x, y, z)
pt_list1 = [(25, 25, 25), (1, 15, 20), (18, 12, 12)]

# Define obstacles [(x, y, z) (x, y, z)] all grid cells from x1 to x2 and y1 to y2 and z1 to z2 are obstacles
obstacle_list = [[(2, 1, 1), (3, 2, 6)], [(2, 3, 1), (3, 6, 6)]]
obstacle_list1 = [[(8, 8, 8), (12, 12, 12)], [(20, 15, 10), (25, 18, 20)], [(7, 15, 12), (10, 20, 18)]]



# start_time = time.time()
# best_solution, best_fitness, population, initial_solution, fitness_values = genetic(size_of_grid1, ps_list1, pt_list1, obstacle_list1)
# end_time = time.time()


# print("Best solution: ", best_solution)
# print("Best solution: ", best_fitness)
# print("Best solution: ", population)

# stats_dict = calculate_stats(fitness_values, end_time)
# save_scenario_stats_to_json("A", stats_dict)

# plot_fitness_over_iterations(fitness_values)

visualize_problem_solution(ps_list1, pt_list1, obstacle_list1, solution_paths=[[(5, 5, 5), (6, 6, 14), (25, 25, 25)], [(1, 10, 10), (1, 10, 11), (1, 15, 20)], [(20, 20, 20), (18, 12, 13), (18, 12, 12)]])