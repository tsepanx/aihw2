import random
import typing

from utils import get_chord, CHORD_MAJOR, CHORD_MINOR, CHORD_DIM

"""
In ideal implementation,
this file should also depend on: 
- Chromosome.fitness_func, 
- create_random_gene
- class Gene
"""

class Gene:
    """
    Represents single chord
    """

    def __init__(self, chord_notes: [int]):
        self.a = random.randint(0, 100)
        self.chord_notes = chord_notes

    # def __int__(self):
    #     return self.rating

    def __repr__(self):
        return f'{self.chord_notes}'


class Chromosome:
    genes: [Gene]
    evaluation: float
    fitness_func: typing.Callable

    def __init__(self, genes=None):
        if genes is not None:
            self.genes = genes
            self.evaluation = self.fitness_func()
        else:
            self.evaluation = float('inf')
            self.genes = []

    def crossover(self, other: 'Chromosome') -> 'Chromosome':
        child = Chromosome()

        for i in range(len(self.genes)):
            g1 = self.genes[i]
            g2 = other.genes[i]

            gene_choice = random.choice((g1, g2))
            child.genes.append(gene_choice)

        return child

    def mutate(self, n_genes):
        for i in range(n_genes):
            rand_ind = random.randint(0, len(self.genes) - 1)
            self.genes[rand_ind] = create_random_gene()

    def __repr__(self):
        return f'{self.fitness_func()}    '


def create_random_gene() -> Gene:
    chord_offsets = random.choice([CHORD_MAJOR, CHORD_MINOR, CHORD_DIM])
    lead_note = random.randint(0, 11)

    notes = get_chord(lead_note, chord_offsets)
    return Gene(notes)


def create_random_chromosome(size: int) -> Chromosome:
    genes = [create_random_gene() for _ in range(size)]
    return Chromosome(genes)


def select_best(population: [Chromosome], selection_ratio: float, fitness_func: typing.Callable):
    selection_size = int(len(population) * selection_ratio)

    for i in population:
        i.evaluation = fitness_func(i)

    return sorted(population, key=lambda x: x.evaluation)[:selection_size]

def reproduce(population: [Chromosome], needed_count: int) -> [Chromosome]:
    children: [Chromosome] = []
    while len(children) < needed_count:
        p1: Chromosome = random.choice(population)
        p2: Chromosome = random.choice(population)
        while p2 == p1:
            p2 = random.choice(population)

        child = p1.crossover(p2)
        children.append(child)

    return children


def mutate(population: [Chromosome], mutation_ratio: float, genes_to_mutate: int):
    mutation_count = int(len(population) * mutation_ratio)

    to_mutate = random.choices(population, k=mutation_count)
    for c in to_mutate:
        c.mutate(genes_to_mutate)


def evo_algo(
        population_size: int,
        chromosome_size: int,
        iter_count: int,
        selection_ratio: float,
        mutation_ratio: float,
        mutation_genes_count: int,
        fitness_func: typing.Callable
) -> Chromosome:
    Chromosome.fitness_func = fitness_func

    population: [Chromosome] = [
        create_random_chromosome(chromosome_size)
        for _ in range(population_size)
    ]

    for i in range(iter_count):
        mutate(population, mutation_ratio, mutation_genes_count)
        selection: [Chromosome] = select_best(population, selection_ratio, fitness_func)
        print(selection[0])

        if selection[0].evaluation <= 0:
            return selection[0]

        population: [Chromosome] = reproduce(selection, population_size)

    return population[0]
