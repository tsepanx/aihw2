import pprint
from typing import Iterable

import mido
# import dataclasses
import enum

import music21
from mido import Message

INPUT_FILENAME = 'input2.mid'

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
    return style[2] - style[1] == 2


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
        # print(res)
        return res

    possible_styles.sort(key=rate_style, reverse=True)
    return possible_styles[0]


best_style = determine_best_style(notes)

style_leading_note = best_style[0]
style_is_major = is_style_major(best_style)

if not style_is_major:
    style_leading_note = (style_leading_note + 3) % 12

best_style = get_style(style_leading_note, STYLE_MAJOR_STEPS if style_is_major else STYLE_MINOR_STEPS)

print(style_leading_note)
print(style_is_major)


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

CHORD_DURATION = mid.ticks_per_beat
VELOCITY = 45

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


average_offset = 12 * (get_average_octave() - 1)

chords_count = get_notes_amount()
print(chords_count)

"""Get all the notes of the track, which are needed for computing the chords"""


def compute_border_notes(track, length):
    res = [None] * length
    time_passed = 0
    notes_by_start_time = dict()
    for msg in track:
        if type(msg) is Message:
            time_passed += msg.time
            if msg.type == "note_on":
                note = msg.note % 12
                if time_passed in notes_by_start_time:
                    notes_by_start_time[time_passed].append(note)
                else:
                    notes_by_start_time[time_passed] = [note]

    # TODO take next note list if no on border
    for time in sorted(notes_by_start_time.keys()):
        if time % CHORD_DURATION == 0:
            res[time // CHORD_DURATION] = notes_by_start_time[time]
    return res


border_notes: [[int]] = compute_border_notes(mid.tracks[1], chords_count)
pprint.pprint(border_notes, width=40)

def select_best_chord(chords_list: [[int]], notes_list: [int]) -> [int]:
    best_intersection = 0
    best_chord = chords_list[0]

    for i in chords_list:
        l = len(set(i).intersection(set(notes_list)))
        if l > best_intersection:
            best_intersection = l
            best_chord = i
    return best_chord


relating_notes = compute_border_notes(mid.tracks[1], chords_count)

chords_sequence = []
for i in range(chords_count):
    if border_notes[i] is not None:
        chord_i = select_best_chord(consonant_chords, border_notes[i])
    else:
        chord_i = consonant_chords[0]
    chords_sequence.append(chord_i)

new_track = []
for i in range(chords_count):
    # Dummy list
    # chords_sequence = consonant_chords[i % len(consonant_chords)]
    chord = chords_sequence[i]

    for j in range(3):
        new_track.append(
            Message(
                'note_on',
                channel=0,
                note=chord[j] + average_offset,
                velocity=VELOCITY,
                time=0
            ))

    for j in range(3):
        new_track.append(
            Message(
                'note_off',
                channel=0,
                note=chord[j] + average_offset,
                velocity=VELOCITY,
                time=CHORD_DURATION if j == 0 else 0
            ))

mid.tracks.append(new_track)
mid.save('my_output2.mid')
