import dataclasses
import random
import typing
from typing import Iterable

import mido

INPUT_FILENAME = "mid/input3.mid"
OUTPUT_FILENAME = "mid/TsepaStepan_output3.mid"

# --- MUSIC THEORY CONSTANTS ---

NOTE_REPRESENTATION_LIST = [
    "C",
    "C#",
    "D",
    "D#",
    "E",
    "F",
    "F#",
    "G",
    "G#",
    "A",
    "A#",
    "B",
]

STYLE_MAJOR_STEPS = [0, 2, 2, 1, 2, 2, 2]
STYLE_MINOR_STEPS = [0, 2, 1, 2, 2, 1, 2]

CHORD_MAJOR = [0, 4, 7]
CHORD_MINOR = [0, 3, 7]
CHORD_DIM = [0, 3, 6]

CONSONANT_CHORDS_TYPES = [
    CHORD_MAJOR,
    CHORD_MINOR,
    CHORD_MINOR,
    CHORD_MAJOR,
    CHORD_MAJOR,
    CHORD_MINOR,
    CHORD_DIM,
]

VELOCITY = 45

# --- UTILS FUNCTIONS ---


def get_chord(lead_note: int, offsets: [int]):
    return [(lead_note + offsets[i]) % 12 for i in range(len(offsets))]


def is_note_msg(msg) -> bool:
    return not msg.is_meta and "note" in msg.__dict__


def global_notes_from_file(mid_file: mido.MidiFile):
    notes: list[int] = []

    for msg in mid_file.tracks[1]:
        if is_note_msg(msg):
            is_note_on = msg.type == "note_on"
            midi_val = msg.note

            if not is_note_on:
                notes.append(midi_val)
    return notes


def save_with_chords(
    mid: mido.MidiFile,
    output_fname: str,
    chords_sequence: [[int]],
    chords_octave: int,
    chord_length: int,
):
    new_track = []
    for i in range(len(chords_sequence)):
        chord = chords_sequence[i]

        for j in range(3):
            new_track.append(
                mido.Message(
                    "note_on",
                    channel=0,
                    note=chord[j] + chords_octave * 12,
                    velocity=VELOCITY,
                    time=0,
                )
            )

        for j in range(3):
            new_track.append(
                mido.Message(
                    "note_off",
                    channel=0,
                    note=chord[j] + chords_octave * 12,
                    velocity=VELOCITY,
                    time=chord_length if j == 0 else 0,
                )
            )

    mid.tracks.append(new_track)
    mid.save(output_fname)


def compute_border_notes(mid_file: mido.MidiFile, chords_count, chord_length):
    res = [None] * chords_count
    time_passed = 0
    notes_by_start_time = dict()
    for msg in mid_file.tracks[1]:
        if is_note_msg(msg):
            time_passed += msg.time

            if msg.type == "note_on":
                note = msg.note % 12
                if time_passed in notes_by_start_time:
                    notes_by_start_time[time_passed].append(note)
                else:
                    notes_by_start_time[time_passed] = [note]

    # TODO take next note list if no on border
    for time in sorted(notes_by_start_time.keys()):
        if time % chord_length == 0:
            res[time // chord_length] = notes_by_start_time[time]
    return res


def get_consonant_chords(style: [int]) -> [[int]]:
    res = []
    for i in range(len(CONSONANT_CHORDS_TYPES)):
        offsets = CONSONANT_CHORDS_TYPES[i]  # f.e. [0, 3, 7]
        chord_notes = [(style[i] + offsets[j]) % 12 for j in range(len(offsets))]
        res.append(chord_notes)

    return res


def get_chords_count(mid_file: mido.MidiFile, chord_length: int):
    beats = 0
    for msg in mid_file.tracks[1]:
        if type(msg) is mido.Message:
            beats += msg.time
    return (beats + chord_length - 1) // chord_length


def get_track_octave(global_notes: [int]):
    cnt = 0
    octave = 0
    for note in global_notes:
        octave += note // 12
        cnt += 1
    return octave // cnt


def get_style(lead_note: int, is_major=True):
    """
    :return: get style notes by leading note and major/minor type
    """
    step_list = STYLE_MAJOR_STEPS if is_major else STYLE_MINOR_STEPS
    return [(lead_note + sum(step_list[: i + 1])) % 12 for i in range(len(step_list))]


def determine_best_style(notes: Iterable[int]):
    """
    Determine best style with maximum intersection of its notes with song notes
    :param notes: song notes
    :return: best style notes list
    """
    notes = list(map(lambda x: x % 12, notes))

    possible_styles = []
    for note in notes:
        major_style = get_style(note, is_major=True)
        minor_style = get_style(note, is_major=False)

        possible_styles.extend((major_style, minor_style))

    def rate_style(style: [int]) -> int:
        res = len(set(notes).intersection(set(style)))
        return res

    possible_styles.sort(key=rate_style, reverse=True)
    return possible_styles[0]


def is_style_major(style: [int]):
    return style[2] - style[1] == 2


def alter_filename_with_key(fname: str):
    style_representation = NOTE_REPRESENTATION_LIST[style_leading_note] + (
        "" if style_is_major else "m"
    )

    fname = fname[: fname.find(".")] + f"_{style_representation}.mid"
    print("Song style: ", style_representation)
    return fname


# --- EVOLUTION ALGORITHM RELATED CLASSES & FUNCS ---


@dataclasses.dataclass
class Gene:
    chord_notes: [int]


class Chromosome:
    """
    Represents accompaniment
    """

    genes: [Gene]
    evaluation: float
    fitness_func: typing.Callable

    def __init__(self, genes=None):
        if genes is not None:
            self.genes = genes
            self.evaluation = self.fitness_func()
        else:
            self.evaluation = float("inf")
            self.genes = []

    def crossover(self, other: "Chromosome") -> "Chromosome":
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
        return f"{round(self.fitness_func(), 5)}"


def create_random_gene() -> Gene:
    chord_notes = random.choice(consonant_chords)
    return Gene(chord_notes)


def create_random_chromosome(size: int) -> Chromosome:
    genes = [create_random_gene() for _ in range(size)]
    return Chromosome(genes)


def select_best(
    population: [Chromosome], selection_ratio: float, fitness_func: typing.Callable
):
    selection_size = int(len(population) * selection_ratio)

    for i in population:
        i.evaluation = fitness_func(i)

    return sorted(population, key=lambda x: x.evaluation, reverse=True)[:selection_size]


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
    fitness_func: typing.Callable,
) -> Chromosome:
    Chromosome.fitness_func = fitness_func

    population: [Chromosome] = [
        create_random_chromosome(chromosome_size) for _ in range(population_size)
    ]

    for i in range(iter_count):
        mutate(population, mutation_ratio, mutation_genes_count)
        selection: [Chromosome] = select_best(population, selection_ratio, fitness_func)
        print(selection[0])

        if selection[0].evaluation >= 1:
            return selection[0]

        population: [Chromosome] = reproduce(selection, population_size)

    return population[0]


# --- MAIN PART BLOCK ---

# Offset in octaves to alter chords accompaniment
CHORDS_OCTAVE_DELTA = -1

# Fitness func to evaluate single Chromosome
def fitness(chromosome: Chromosome) -> float:
    chromosome_chords: [[int]] = [gene.chord_notes for gene in chromosome.genes]

    max_score = len(chromosome.genes)
    score = 0

    for i in range(chords_count):
        chord: [int] = chromosome_chords[i]
        cur_track_notes: [int] = border_notes[i]

        if cur_track_notes is not None:
            same_notes = list(set(cur_track_notes).intersection(chord))
            if len(same_notes) == len(cur_track_notes):
                score += 1
        elif i > 0:
            prev_chord = chromosome_chords[i - 1]
            if prev_chord == chord:
                score += 1

    return score / max_score


if __name__ == "__main__":
    mid = mido.MidiFile(INPUT_FILENAME)
    tmp, notes_track = mid.tracks

    CHORD_LENGTH = mid.ticks_per_beat

    notes = global_notes_from_file(mid)
    best_style = determine_best_style(notes)

    style_leading_note = best_style[0]
    style_is_major = is_style_major(best_style)

    # if key is MINOR, change it to its relative MAJOR key, to simplify chords calculations
    if not style_is_major:
        style_leading_note = (style_leading_note + 3) % 12
        style_is_major = True

        best_style = get_style(style_leading_note, True)

    # List of chords, that can be used in accompaniment
    consonant_chords = get_consonant_chords(best_style)

    # Count of chords in accompaniment
    chords_count = get_chords_count(mid, CHORD_LENGTH)

    # 2D list of notes, playing at the same time as accompaniment chords
    border_notes: [[int]] = compute_border_notes(mid, chords_count, CHORD_LENGTH)

    # Constants responsible of evolution algo
    POPULATION_SIZE = 100
    CHROMOSOME_SIZE = chords_count
    SELECTION_RATIO = 0.5
    MUTATION_RATIO = 0.5
    MUTATION_GENES_COUNT = 1
    ITER_COUNT = 1000

    # Determining the best accompaniment using evo algo
    best_chromosome = evo_algo(
        POPULATION_SIZE,
        CHROMOSOME_SIZE,
        ITER_COUNT,
        SELECTION_RATIO,
        MUTATION_RATIO,
        MUTATION_GENES_COUNT,
        fitness,
    )

    # Convert Chromosome to list of chord notes
    chords_best_sequence = [gene.chord_notes for gene in best_chromosome.genes]

    OUTPUT_FILENAME = alter_filename_with_key(OUTPUT_FILENAME)

    # Save initial song with accompaniment to output file
    save_with_chords(
        mid,
        OUTPUT_FILENAME,
        chords_best_sequence,
        get_track_octave(notes) + CHORDS_OCTAVE_DELTA,
        CHORD_LENGTH,
    )
