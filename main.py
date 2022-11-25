import pprint
from typing import Iterable

import mido
# import dataclasses
import enum

import music21
from mido import Message

INPUT_FILENAME = 'input1.mid'

STYLE_MAJOR_STEPS = [0, 2, 2, 1, 2, 2, 2]
STYLE_MINOR_STEPS = [0, 2, 1, 2, 2, 1, 2]


def get_style(lnote: int, offset_list: [int]):
    return [(lnote + sum(offset_list[:i + 1])) % 12 for i in range(len(offset_list))]


class ChordSteps(enum.Enum):
    MAJOR = [0, 4, 7]
    MINOR = [0, 3, 7]
    DIM = [0, 3, 6]


MAJOR_TYPE = ChordSteps.MAJOR
MINOR_TYPE = ChordSteps.MINOR
DIM_TYPE = ChordSteps.DIM

# Types of chords applied to allowed chords, generated from KEY
CONSONANT_CHORDS_TYPES = [
    MAJOR_TYPE,
    MINOR_TYPE,
    MINOR_TYPE,
    MAJOR_TYPE,
    MAJOR_TYPE,
    MINOR_TYPE,
    DIM_TYPE,
]

mid = mido.MidiFile(INPUT_FILENAME)
tmp, notes_track = mid.tracks

notes: list[int] = []

cur_note = None
for msg in notes_track:
    if not msg.is_meta and 'note' in msg.__dict__:
        # print(msg)

        is_note_on = msg.type == 'note_on'
        midi_val = msg.note

        if not is_note_on:
            notes.append(midi_val)


# pprint.pprint(notes)

def is_style_major(style: [int]):
    return style[2] - style[1] == 0


def determine_best_style(notes: Iterable[int]):
    notes = list(map(lambda x: x % 12, notes))

    possible_styles = []
    for note in notes:
        major_style = get_style(note, STYLE_MAJOR_STEPS)
        minor_style = get_style(note, STYLE_MINOR_STEPS)

        possible_styles.extend((major_style, minor_style))

    def rate_style(style: [int]) -> int:
        res = len(
            set(notes).intersection(
                set(style)
            )
        )
        print(res)
        return res

    possible_styles.sort(key=rate_style, reverse=True)
    return possible_styles[0]


best_style = determine_best_style(notes)

style_leading_note = best_style[0]
style_is_major = is_style_major(best_style)

print(style_leading_note)
print(style_is_major)

# key = music21.converter.parse(INPUT_FILENAME).analyze('key')
# if key.mode == "minor":
#     MUSIC_SCALE = (key.tonic.midi + 3) % 12
# else:
#     MUSIC_SCALE = key.tonic.midi % 12
#
# m21style = get_style(MUSIC_SCALE, STYLE_MAJOR_STEPS if key.mode == "major" else STYLE_MINOR_STEPS)
# pprint.pprint(m21style)

def get_consonant_chords(style: [int]) -> [[int]]:
    res = []
    for i in range(len(CONSONANT_CHORDS_TYPES)):
        offsets = CONSONANT_CHORDS_TYPES[i].value  # [0, 3, 7]
        chord_notes = [(style[i] + offsets[j]) % 12 for j in range(len(offsets))]
        res.append(chord_notes)

    return res

consonant_chords = get_consonant_chords(best_style)
pprint.pprint(best_style)
pprint.pprint(consonant_chords)

CHORD_DURATION = mid.ticks_per_beat * 2


def get_notes_amount():
    beats = 0
    for msg in mid.tracks[1]:
        if type(msg) is Message:
            beats += msg.time
    length = (beats + CHORD_DURATION - 1) // CHORD_DURATION
    return length


def get_average_octave():
    """Return the average range of notes from original song."""
    note_count = 0
    avg_octave = 0
    for note in notes:
        avg_octave += int(note / 12)
        note_count += 1
    return int(avg_octave / note_count)


average_offset = 12 * (get_average_octave() - 2)

chords_count = get_notes_amount()
print(chords_count)

new_track = []

for i in range(chords_count):
    chord_notes = consonant_chords[i % len(consonant_chords)]

    for j in range(3):
        new_track.append(
            Message(
                'note_on',
                channel=0,
                note=chord_notes[j] + average_offset,
                # velocity=velocity,
                time=0
            ))

    for j in range(3):
        new_track.append(
            Message(
                'note_off',
                channel=0,
                note=chord_notes[j] + average_offset,
                # velocity=velocity,
                time=CHORD_DURATION if j == 0 else 0
            ))

mid.tracks.append(new_track)
mid.save('my_output1.mid')
