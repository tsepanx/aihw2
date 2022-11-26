from typing import Iterable

import mido
from mido import Message

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

def get_chord(lead_note: int, offsets: [int]):
    return [(lead_note + offsets[i]) % 12 for i in range(len(offsets))]

def is_note_msg(msg) -> bool:
    return not msg.is_meta and 'note' in msg.__dict__

def global_notes_from_file(mid_file: mido.MidiFile):
    notes: list[int] = []

    for msg in mid_file.tracks[1]:
        if is_note_msg(msg):
            is_note_on = msg.type == 'note_on'
            midi_val = msg.note

            if not is_note_on:
                notes.append(midi_val)
    return notes


def save_with_chords(mid: mido.MidiFile, output_fname: str, chords_sequence: [[int]], chords_octave: int, chord_duration: int):
    new_track = []
    for i in range(len(chords_sequence)):
        # Dummy list
        # chords_sequence = consonant_chords[i % len(consonant_chords)]
        chord = chords_sequence[i]

        for j in range(3):
            new_track.append(
                Message(
                    'note_on',
                    channel=0,
                    note=chord[j] + chords_octave * 12,
                    velocity=VELOCITY,
                    time=0
                ))

        for j in range(3):
            new_track.append(
                Message(
                    'note_off',
                    channel=0,
                    note=chord[j] + chords_octave * 12,
                    velocity=VELOCITY,
                    time=chord_duration if j == 0 else 0
                ))

    mid.tracks.append(new_track)
    mid.save(output_fname)


def compute_border_notes(mid_file: mido.MidiFile, chords_count, chord_duration):
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
        if time % chord_duration == 0:
            res[time // chord_duration] = notes_by_start_time[time]
    return res


def get_consonant_chords(style: [int]) -> [[int]]:
    res = []
    for i in range(len(CONSONANT_CHORDS_TYPES)):
        offsets = CONSONANT_CHORDS_TYPES[i]  # [0, 3, 7]
        chord = [(style[i] + offsets[j]) % 12 for j in range(len(offsets))]
        res.append(chord)

    return res


def get_chords_count(mid_file: mido.MidiFile, chord_duration: int):
    beats = 0
    for msg in mid_file.tracks[1]:
        if type(msg) is Message:
            beats += msg.time
    return (beats + chord_duration - 1) // chord_duration


def get_track_octave(global_notes: [int]):
    cnt = 0
    octave = 0
    for note in global_notes:
        octave += note // 12
        cnt += 1
    return octave // cnt


def get_style(lead_note: int, is_major=True):
    offset_list = STYLE_MAJOR_STEPS if is_major else STYLE_MINOR_STEPS
    return [(lead_note + sum(offset_list[:i + 1])) % 12 for i in range(len(offset_list))]


def determine_best_style(notes: Iterable[int]):
    notes = list(map(lambda x: x % 12, notes))

    possible_styles = []
    for note in notes:
        major_style = get_style(note, is_major=True)
        minor_style = get_style(note, is_major=False)

        possible_styles.extend((major_style, minor_style))

    def rate_style(style: [int]) -> int:
        res = len(
            set(notes).intersection(set(style))
        )
        return res

    possible_styles.sort(key=rate_style, reverse=True)
    return possible_styles[0]


def is_style_major(style: [int]):
    return style[2] - style[1] == 2
