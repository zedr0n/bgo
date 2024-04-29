from typing import List
try:
    from .Game import Game, ItemClass, Card
except:
    from Game import Game, ItemClass, Card

import random
import time
import math

import multiprocessing as mp

class Element:
    def __init__(self, dim_x=0, dim_y=0, dim_z=0, x=0, y=0, z=0, layer=0) -> None:
        self.dim_x = dim_x
        self.dim_y = dim_y
        self.dim_z = dim_z
        self.x = x
        self.y = y
        self.z = z
        self.layer = layer

    def get_overlap(self, other, total = True) -> float:
        return 0.0

    def mutate(self) -> None:
        pass

    def copy(self):
        pass

    def display(self):
        pass

class Tray(Element):
    def __init__(self, dim_x=0, dim_y=0, dim_z=0, x=0, y=0, z=0, layer=0) -> None:
        self.dim_x = dim_x
        self.dim_y = dim_y
        self.dim_z = dim_z
        self.x = x
        self.y = y
        self.z = z
        self.layer = layer
        self._params_count = 7

    @staticmethod
    def from_game(game: Game):
        layer_size_x, layer_size_y, layer_size_z = game.layer_size()
        x = random.randint(0, layer_size_x - 1)
        y = random.randint(0, layer_size_y - 1)
        #z = random.randint(0, layer_size_z - 1)
        z = 0
        dim_x = random.randint(1, layer_size_x - x + 1)
        dim_y = random.randint(1, layer_size_y - y + 1)
        # dim_z = random.randint(1, layer_size_z - z + 1)
        dim_z = layer_size_z
        return Tray(
            dim_x=dim_x,
            dim_y=dim_y,
            dim_z=dim_z,
            x=x,
            y=y,
            z=z,
            layer=0
        )

    def get_overlap(self, other, total = True) -> float|tuple[int, int, int]:
        if not isinstance(other, Tray):
            return 0.0
        # Calculate overlap in each dimension
        # Overlap in x
        x_overlap = max(0, min(self.x + self.dim_x, other.x + other.dim_x) - max(self.x, other.x))
        # Overlap in y
        y_overlap = max(0, min(self.y + self.dim_y, other.y + other.dim_y) - max(self.y, other.y))
        # Overlap in z
        z_overlap = max(0, min(self.z + self.dim_z, other.z + other.dim_z) - max(self.z, other.z))

        # If all dimensions have overlap, calculate the volume of the overlap
        if total:
            return x_overlap * y_overlap * z_overlap
        else:
            return x_overlap, y_overlap, z_overlap

    def mutate(self) -> float:
        choice = random.choice(range(self._params_count))
        k = random.randint(1, 10)
        if choice == 0:
            self.dim_x += random.choice([-k, k])
            self.dim_x = max(1, self.dim_x)  # Ensure dimensions are positive        
        if choice == 1:
            self.dim_y += random.choice([-k, k])
            self.dim_y = max(1, self.dim_y)  # Ensure dimensions are positive        
        if choice == 2 and False:
            self.dim_z += random.choice([-k, k])
            self.dim_z = max(1, self.dim_z)  # Ensure dimensions are positive        

        if choice == 3:
            self.x += random.choice([-k, k])
            self.x = max(0, self.x)
        if choice == 4:
            self.y += random.choice([-k, k])
            self.y = max(0, self.y)
        if choice == 5 and False:
            self.z += random.choice([-k, k])
            self.z = max(0, self.z)  # Ensure dimensions are positive

    def copy(self):
        return Tray(
            self.dim_x,
            self.dim_y,
            self.dim_z,
            self.x,
            self.y,
            self.z,
            self.layer)

    def display(self):
        print(f"{self.dim_x}, {self.dim_y}, {self.dim_z}, {self.x}, {self.y}, {self.z}, {self.layer}")
class Gene:
    def __init__(self) -> None:
        # Each Gene represents a set of element's configuration: dimensions (x, y, z), position (x, y, z), and layer index
        self.data: List[Element] = []
        self._max_number_of_elements = 1

    def can_add_more_elements(self):
        return len(self.data) < self._max_number_of_elements

class Individual:
    def __init__(self, gene_count: int) -> None:
        # An individual is composed of multiple genes, each representing a set of elements for each item class
        self.data: List[Gene] = [Gene() for _ in range(gene_count)]
        self.fitness = None
        self.fitness_ex = None

class Genetic:
    def __init__(self, game: Game, population_size: int, number_of_elements_factor: float, unused_space_factor: float,
                 unfit_factor: float, overlap_factor: float, overfit_factor: float) -> None:
        self.mutation_rate = 0.5
        self.mutation_rate_number_of_elements_up = 0.1
        self.mutation_rate_number_of_elements_down = 0.1
        self._tournament_size = max(4, population_size // 100)

        self._total_space: List[int] = game.total_space()
        self._game = game
        self._item_classes: List[ItemClass] = game.generate_classes()
        gene_count = len(self._item_classes)

        self._number_of_elements_factor = number_of_elements_factor
        self._unused_space_factor = unused_space_factor
        self._unfit_factor = unfit_factor
        self._overlap_factor = overlap_factor
        self._overfit_factor = overfit_factor

        # Initialize population with a given size and number of genes per individual
        self.population: List[Individual] = [Individual(gene_count) for _ in range(population_size)]
        self._population_size = population_size

        for i, ind in enumerate(self.population):
            for gene in ind.data:
                gene.data.append(Tray.from_game(game))
            self.repair_individual(ind)

        #self._populations: List[List[Individual]] = [self.population.copy()]

    def compute_fitness(self, individual: Individual) -> float:
        number_of_elements = sum([len(x.data) for x in individual.data])
        min_number_of_elements = sum([ 1 for x in individual.data ])
        unused_space = self._total_space.copy()
        unfit_penalty = 0
        overfit_penalty = 0
        overlap_penalty = 0
        max_x, max_y, max_z = self._game.bounding_box()
        max_volume = max_x * max_y * max_z
        for i, gene in enumerate(individual.data):
            item_class = self._item_classes[i]
            required_x, required_y, required_z = item_class.bounding_box()
            unfit_x, unfit_y, unfit_z = 0, 0, 0
            overfit_x, overfit_y, overfit_z = 0, 0, 0
            stacked_y = 0
            for j, element in enumerate(gene.data):
                unused_space[element.layer] -= element.dim_x * element.dim_y * element.dim_z

                # Accumulate stacked height in y
                stacked_y += element.dim_y

            # the stacking is in y direction
            # Check if element dimensions meet or exceed item class requirements in x and z
            for j, element in enumerate(gene.data):
                #unfit_x = max(unfit_x, max(0, required_x - element.dim_x) * max(1, element.dim_y) * max(1, element.dim_z))
                unfit_x += max(0, required_x - element.dim_x) * max(1, element.dim_y) * max(1, element.dim_z)
                #unfit_z = max(unfit_z, max(0, required_z - element.dim_z) * max(1, element.dim_x) * max(1, element.dim_y))
                unfit_z += max(0, required_z - element.dim_z) * max(1, element.dim_x) * max(1, element.dim_y)
                #unfit_y = max(unfit_y, max(0, required_y - stacked_y) * max(1, element.dim_x) * max(1, element.dim_z))
                unfit_y += max(0, required_y - stacked_y) * max(1, element.dim_x) * max(1, element.dim_z)

            # check if element is outside the box
            for j, element in enumerate(gene.data):
                #overfit_x = (max(overfit_x, max(0, element.dim_x + element.x - max_x))
                #overfit_x = (max(overfit_x, max(0, element.dim_x + element.x - max_x))
                #             * max(1, element.dim_y) * max(1, element.dim_z))
                overfit_x += max(0, element.dim_x + element.x - max_x) * max(1, element.dim_y) * max(1, element.dim_z)
                #overfit_y = (max(overfit_y, max(0, element.dim_y + element.y - max_y))
                #             * max(1, element.dim_x) * max(1, element.dim_z))
                overfit_y += max(0, element.dim_y + element.y - max_y) * max(1, element.dim_x) * max(1, element.dim_z)
                #overfit_z = (max(overfit_z, max(0, element.dim_z + element.z - max_z)) * max(1, element.dim_x)
                #             * max(1, element.dim_y))
                overfit_z += max(0, element.dim_z + element.z - max_z) * max(1, element.dim_x) * max(1, element.dim_y)

            # add to penalties
            if unfit_x > 0 or unfit_y > 0 or unfit_z > 0:
                unfit_penalty += max(1, unfit_x) * max(1, unfit_y) * max(1, unfit_z)
            if overfit_x > 0 or overfit_y > 0 or overfit_z > 0:
                overfit_penalty += max(1, overfit_x) * max(1, overfit_y) * max(1, overfit_z)

            for j, element in enumerate(gene.data):
                for other_element in gene.data[j+1:]:
                    if other_element.layer != element.layer:
                        continue
                    overlap = element.get_overlap(other_element)
                    unused_space[element.layer] += overlap
                    overlap_penalty += overlap

            for j in range(i+1, len(individual.data)):
                other_gene = individual.data[j]
                for element in gene.data:
                    for other_element in other_gene.data:
                        if other_element.layer != element.layer:
                            continue
                        overlap = element.get_overlap(other_element)
                        unused_space[element.layer] += overlap
                        overlap_penalty += overlap

        fitness = ((self._unused_space_factor * sum(map(lambda x: abs(x), unused_space))
                   + self._unfit_factor * abs(unfit_penalty))
                   + self._overlap_factor * abs(overlap_penalty)
                   + self._overfit_factor * abs(overfit_penalty))

        # -self._number_of_elements_factor * number_of_elements
        fitness /= max_volume / 100
        fitness += self._number_of_elements_factor * ( number_of_elements - min_number_of_elements ) / len(individual.data) / 100
        fitness = -fitness

        individual.fitness = fitness
        individual.fitness_ex = sum(map(lambda x: abs(x), unused_space)), unfit_penalty, overlap_penalty, overfit_penalty
        return fitness

    def select_distinct(self, number_of_winners: int) -> List[Individual]:
        selected = set()
        winners = []
        while len(winners) < number_of_winners:
            tournament = [ind for ind in random.sample(self.population, self._tournament_size) if ind not in selected]
            winner = max(tournament, key=self.compute_fitness)
            winners.append(winner)
            selected.add(winner)
        return winners

    def select(self) -> Individual:
        tournament = random.sample(self.population, self._tournament_size)
        winner = max(tournament, key=self.compute_fitness)
        return winner

    def blended_crossover(self, parent1: Individual, parent2: Individual, alpha_range=(-0.05, 1.05)):
        child = Individual(len(parent1.data))
        for i in range(len(parent1.data)):
            gene = child.data[i]
            gene.data.clear()
            parent1_trays = parent1.data[i].data
            parent2_trays = parent2.data[i].data
            #max_number_of_elements = max(len(parent1.data[i].data), len(parent2.data[i].data))
            max_number_of_elements = max(len(parent1_trays), len(parent2_trays))
            for j in range(max_number_of_elements):
                #tray1 = random.choice(parent1.data[i].data)
                #tray2 = random.choice(parent2.data[i].data)
                alpha = random.uniform(*alpha_range)
                new_tray = None
                if j < len(parent1_trays) and j < len(parent2_trays):
                    tray1 = parent1_trays[j]
                    tray2 = parent2_trays[j]
                    new_tray = Tray(
                        dim_x=max(1, round(alpha*tray1.dim_x + (1-alpha)*tray2.dim_x), 0),
                        dim_y=max(1, round(alpha*tray1.dim_y + (1-alpha)*tray2.dim_y), 0),
                        dim_z=max(1, round(alpha*tray1.dim_z + (1-alpha)*tray2.dim_z), 0),
                        x=max(0, round(alpha*tray1.x + (1-alpha)*tray2.x), 0),
                        y=max(0, round(alpha*tray1.y + (1-alpha)*tray2.y), 0),
                        z=max(0, round(alpha*tray1.z + (1-alpha)*tray2.z), 0),
                        layer=tray1.layer  # Assuming the same layer, adjust as needed
                    )
                elif j < len(parent1_trays):
                    new_tray = parent1_trays[j]
                else:
                    new_tray = parent2_trays[j]
                if new_tray is not None:
                    gene.data.append(new_tray)

        return child

    def one_point_crossover(self, parent1: Individual, parent2: Individual) -> Individual:
        child = Individual(len(parent1.data))

        crossover_point = random.randint(1, len(parent1.data[0].data) - 1)  # Assuming all genes have the same length

        for i in range(len(parent1.data)):
            child.data[i].data = parent1.data[i].data[:crossover_point] + parent2.data[i].data[crossover_point:]

        return child

    def crossover(self, parent1: Individual, parent2: Individual) -> Individual:
        return self.blended_crossover(parent1, parent2)

    def mutate(self, individual: Individual) -> None:
        gene = random.choice(individual.data)
        rand = random.random()
        if rand < self.mutation_rate:
            element_to_mutate = random.choice(gene.data)
            element_to_mutate.mutate()
        else:
            rand -= self.mutation_rate
            if gene.can_add_more_elements() and rand < self.mutation_rate_number_of_elements_up:
                gene.data += [Tray.from_game(self._game)]
                # split the last tray in two
                #last_element: Element = gene.data[len(gene.data)-1]
                #last_element.dim_x = max(1, last_element.dim_x // 2)
                #last_element.dim_y = max(1, last_element.dim_y // 2)
                #last_element.dim_z = max(1, last_element.dim_z // 2)
                #new_element: Element = last_element.copy()
                #new_element.x = last_element.x + last_element.dim_x
                #new_element.y = last_element.y + last_element.dim_y
                #new_element.z = last_element.z + last_element.dim_z
                #gene.data += [new_element]
            else:
                rand -= self.mutation_rate_number_of_elements_up
                if len(gene.data) > 1 and rand < self.mutation_rate_number_of_elements_down:
                    gene.data.pop()

    def repair_individual(self, individual: Individual) -> None:
        max_x, max_y, max_z = self._game.bounding_box()
        for i, gene in enumerate(individual.data):
            for j, element in enumerate(gene.data):
                if element.dim_x + element.x > max_x:
                    element.dim_x = max(1, max_x - element.x)
                if element.dim_y + element.y > max_y:
                    element.dim_y = max(1, max_y - element.y)
                if element.dim_z + element.z > max_z:
                    element.dim_z = max(1, max_z - element.z)

        for i, gene in enumerate(individual.data):
            for j, element in enumerate(gene.data):
                for other_element in gene.data[j + 1:]:
                    if other_element.layer != element.layer:
                        continue
                    overlap_x, overlap_y, overlap_z = element.get_overlap(other_element, False)
                    if overlap_x * overlap_y * overlap_z == 0:
                        continue
                    if overlap_x > 0:
                        other_element.dim_x = max(1, other_element.dim_x - overlap_x)
                    if overlap_y > 0:
                        other_element.dim_x = max(1, other_element.dim_y - overlap_y)
                    if overlap_z > 0:
                        other_element.dim_x = max(1, other_element.dim_z - overlap_z)


    def run_generation(self, pool: mp.Pool = None) -> List[Individual]:
        # Determine the number of elite individuals to carry over
        num_elites = max(1, int(self._population_size * 0.06))  # For example, 6% of the population

        # Sort the current population based on fitness and select the top individuals
        if pool is not None:
            fitness_scores = pool.map(self.compute_fitness, self.population)
            sorted_population = [x for _, x in sorted(zip(fitness_scores, self.population), key=lambda x:x[0], reverse=True)]
        else:
            sorted_population = sorted(self.population, key=self.compute_fitness, reverse=True)
        elites = sorted_population[:num_elites]

        # Prepare the new population starting with the elites
        new_population = elites[:]

        # Generate the rest of the new population
        if pool is not None:
            tasks = []
            for _ in range((self._population_size - num_elites) // 2):
                parent1, parent2 = self.select(), self.select()
                tasks.append((parent1, parent2))

            results = pool.starmap(self.perform_crossover_and_mutation, tasks)
            for res in results:
                child1, child2 = res
                self.repair_individual(child1)
                self.repair_individual(child2)
                new_population.extend([child1, child2])
        else:
            #parents = self.select_distinct((self._population_size - num_elites) // 2)
            for _ in range((self._population_size - num_elites) // 2):
                parent1, parent2 = self.select(), self.select()
                child1 = self.crossover(parent1, parent2)
                child2 = self.crossover(parent1, parent2)
                self.mutate(child1)
                self.mutate(child2)
                self.repair_individual(child1)
                self.repair_individual(child2)
                new_population.extend([child1, child2])

        # Adjust the population size in case of rounding errors
        new_population = new_population[:self._population_size]

        # Update the global population list
        self.population = new_population
        return new_population

    def perform_crossover_and_mutation(self, parent1, parent2):
        child1 = self.crossover(parent1, parent2)
        child2 = self.crossover(parent1, parent2)
        self.mutate(child1)
        self.mutate(child2)
        return child1, child2

def individual_to_trays(individual: Individual):
    all_elements = []
    for gene in individual.data:
        for el in gene.data:
            if el is not None:
                tray = {}
                tray['x'] = el.x / 10
                tray['y'] = el.y / 10
                tray['z'] = el.z / 10
                tray['Length'] = el.dim_y / 10
                tray['Width'] = el.dim_x / 10
                tray['Height'] = el.dim_z / 10

                all_elements.append(tray)

    return all_elements


def create_etherfields():
    card = Card(88, 63, 1)
    tile = Card(100, 100, 1)
    game = Game(300, 300, 120)
    game.add_items(card, 100)
    game.add_items(tile, 100)

    #pool = mp.Pool(8)
    pool = None

    genetic = Genetic(game, 200, 0, 0.1, 1, 1, 1)
    winner = None
    min_fitness = None
    fitness_loop = 0
    max_fitness_loop = 100
    for i in range(0, 3000):
        population = genetic.run_generation(pool)
        if pool is not None:
            fitness_scores = pool.map(genetic.compute_fitness, genetic.population)
            fitness, winner = max(zip(fitness_scores, population), key=lambda x: x[0])
            winner.fitness = fitness
        else:
            winner = max(population, key=genetic.compute_fitness)
            if winner.fitness == min_fitness:
                fitness_loop += 1
            else:
                fitness_loop = 0

            if min_fitness is None or min_fitness > winner.fitness:
                min_fitness = winner.fitness
            if fitness_loop >= max_fitness_loop:
                break

        if i % 10 == 0:
            print(f"Generation {i} fitness: {winner.fitness}")
        if winner.fitness == 0:
            break
    
    for gene in winner.data:
        for el in gene.data:
            if el is not None:
                el.display()

    return individual_to_trays(winner)


if __name__ == '__main__':
    card = Card(88, 63, 1)
    tile = Card(100, 100, 1)
    game = Game(88, 300, 120)
    game.add_items(card, 100)
    game.add_items(tile, 100)

    #pool = mp.Pool(16)
    pool = None
    total_time = -time.time()

    genetic = Genetic(game, 100, 0, 1, 1, 1, 1)
    winner = None
    max_fitness = None
    fitness_loop = 0
    max_fitness_loop = 100

    for i in range(0, 10000):
        population = genetic.run_generation(pool)
        if pool is not None:
            fitness_scores = pool.map(genetic.compute_fitness, genetic.population)
            fitness, winner = max(zip(fitness_scores, population), key=lambda x: x[0])
            winner.fitness = fitness
        else:
            winner = max(population, key=genetic.compute_fitness)

        print(f"Generation {i} fitness: {winner.fitness}")
        if winner.fitness == max_fitness:
            fitness_loop += 1
        else:
            fitness_loop = 0

        if max_fitness is None or winner.fitness > max_fitness:
            max_fitness = winner.fitness

        if fitness_loop >= max_fitness_loop or genetic.compute_fitness(winner) == 0:
            break

    for gene in winner.data:
        for el in gene.data:
            if el is not None:
                el.display()

    unused_space_penalty, unfit_penalty, overlap_penalty, overfit_penalty = winner.fitness_ex
    print(f"Unused space penalty: {unused_space_penalty}")
    print(f"Unfit penalty: {unfit_penalty}")
    print(f"Overlap penalty: {overlap_penalty}")
    print(f"Overfit penalty: {overfit_penalty}")

    total_time += time.time()
    print(f"Time taken to find solution : {total_time}s")
