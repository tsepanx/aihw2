import pprint

import mido

from utils import save_with_chords, compute_border_notes, get_consonant_chords, get_chords_count, get_track_octave, \
    get_style, determine_best_style, is_style_major, global_notes_from_file

INPUT_FILENAME = 'mid/barbiegirl_mono.mid'
OUTPUT_FILENAME = 'mid/my_output_barbie.mid'

mid = mido.MidiFile(INPUT_FILENAME)
tmp, notes_track = mid.tracks

CHORD_DURATION = mid.ticks_per_beat
CHORDS_OCTAVE_DELTA = -2

notes = global_notes_from_file(mid)
best_style = determine_best_style(notes)

style_leading_note = best_style[0]
style_is_major = is_style_major(best_style)

if not style_is_major:
    style_leading_note = (style_leading_note + 3) % 12

best_style = get_style(style_leading_note, style_is_major)

print(style_leading_note)
print(style_is_major)

consonant_chords = get_consonant_chords(best_style)
pprint.pprint(best_style)
pprint.pprint(consonant_chords)

chords_count = get_chords_count(mid, CHORD_DURATION)
border_notes: [[int]] = compute_border_notes(mid, chords_count, CHORD_DURATION)
pprint.pprint(border_notes, width=40)

# --- EVOLUTION ALGO BLOCK

from evo import evo_algo, Chromosome


def fitness(chromosome: Chromosome) -> float:
    chromosome_chords: [[int]] = [gene.chord_notes for gene in chromosome.genes]

    max_score = len(chromosome.genes)
    score = max_score

    for i in range(chords_count):
        chord: [int] = chromosome_chords[i]
        cur_track_notes: [int] = border_notes[i]

        if chord in consonant_chords:
            score -= 0.5

        if cur_track_notes is not None:
            same_notes = list(set(cur_track_notes).intersection(chord))
            if len(same_notes) >= len(cur_track_notes):
                score -= 0.5
        elif i > 0:
            prev_chord = chromosome_chords[i - 1]
            if prev_chord == chord:
                score -= 0.5

    return score / max_score


POPULATION_SIZE = 100
CHROMOSOME_SIZE = chords_count
SELECTION_RATIO = 0.5
MUTATION_RATIO = 0.5
MUTATION_GENES_COUNT = 1
ITER_COUNT = 10000

best_chromosome = evo_algo(
    POPULATION_SIZE,
    CHROMOSOME_SIZE,
    ITER_COUNT,
    SELECTION_RATIO,
    MUTATION_RATIO,
    MUTATION_GENES_COUNT,
    fitness
)

chords_best_sequence = [gene.chord_notes for gene in best_chromosome.genes]
# pprint.pprint(list(map(lambda x: x in consonant_chords, chords_best_sequence)))

# --- END OF EVO BLOCK

save_with_chords(
    mid,
    OUTPUT_FILENAME,
    chords_best_sequence,
    get_track_octave(notes) + CHORDS_OCTAVE_DELTA,
    CHORD_DURATION
)
