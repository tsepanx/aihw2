import pprint

import mido

from utils import save_with_chords, compute_border_notes, get_consonant_chords, get_chords_count, get_track_octave, \
    get_style, determine_best_style, is_style_major, global_notes_from_file

INPUT_FILENAME = 'mid/input2.mid'
OUTPUT_FILENAME = 'mid/my_output2.mid'

mid = mido.MidiFile(INPUT_FILENAME)
tmp, notes_track = mid.tracks

CHORD_DURATION = mid.ticks_per_beat

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


def select_best_chord(chords_list: [[int]], notes_list: [int]) -> [int]:
    # TODO Deprecated
    best_intersection = 0
    best_chord = chords_list[0]

    for i in chords_list:
        l = len(set(i).intersection(set(notes_list)))
        if l > best_intersection:
            best_intersection = l
            best_chord = i
    return best_chord


chords_sequence = []
for i in range(chords_count):
    if border_notes[i] is not None:
        chord_i = select_best_chord(consonant_chords, border_notes[i])
    else:
        chord_i = consonant_chords[0]
    chords_sequence.append(chord_i)

save_with_chords(
    mid,
    OUTPUT_FILENAME,
    chords_sequence,
    get_track_octave(notes) - 1,
    CHORD_DURATION
)
