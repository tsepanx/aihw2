import random
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
    rating: int

    def __init__(self, chord_notes: [int]):
        self.chord_notes = chord_notes

    def __int__(self):
        return self.rating

    def __repr__(self):
        return f'{self.rating}, {self.chord_notes}'


class Chromosome:
    genes: [Gene]
    CHROMOSOME_SIZE: int  # Count of chords in composition
    evaluation: float

    def __init__(self, genes=()):
        self.genes = genes
        self.evaluation = 0

    def crossover(self, other: 'Chromosome') -> 'Chromosome':
        child = Chromosome()

        for i in range(self.CHROMOSOME_SIZE):
            g1 = self.genes[i]
            g2 = other.genes[i]

            child.genes.append(random.choice((g1, g2)))

        return child

    def mutate(self, n_genes):
        for i in range(n_genes):
            rand_ind = random.randint(0, len(self.genes))
            self.genes[rand_ind] = create_random_gene()


def fitness(c: Chromosome) -> float:
    result = 0  # TODO

    c.evaluation = 0
    return result


def create_random_gene() -> Gene:
    chord_offsets = random.choice([CHORD_MAJOR, CHORD_MINOR, CHORD_DIM])
    lead_note = random.randint(0, 11)

    notes = get_chord(lead_note, chord_offsets)
    return Gene(notes)


def create_random_chromosome(size: int) -> Chromosome:
    genes = [create_random_gene() for _ in range(size)]
    return Chromosome(genes)


def select_best(population: [Chromosome], selection_ratio: float):
    selection_size = int(len(population) * selection_ratio)

    c: Chromosome
    chromosomes_scores_items = [(fitness(c), c) for c in population]
    chromosomes_scores_items.sort(key=lambda x: x[0])

    selected_list = chromosomes_scores_items[:selection_size]
    return list(map(lambda x: x[1], selected_list))


def repopulate(population: [Chromosome], needed_size: int) -> [Chromosome]:
    children: [Chromosome] = []
    while len(population) < needed_size:
        p1: Chromosome = random.choice(population)
        p2: Chromosome = random.choice(population)
        while p2 == p1:
            p2 = random.choice(population)

        child = p1.crossover(p2)
        children.append(child)

    return population + children


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
        genes_to_mutate: int
) -> Chromosome:

    population: [Chromosome] = [
        create_random_chromosome(chromosome_size)
        for _ in range(population_size)
    ]

    for i in range(iter_count):
        if population[0].evaluation >= 1:
            return population[0]

        selection: [Chromosome] = select_best(population, selection_ratio)
        population: [Chromosome] = repopulate(selection, population_size)
        mutate(population, mutation_ratio, genes_to_mutate)
