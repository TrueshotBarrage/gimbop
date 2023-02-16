"""This module contains utilities for music generation."""

# Wrapper for repeating any method indefinitely
def repeat(func, args, n):
    for _ in range(n):
        x = func(*args)
    return


# Plays a note at a given time for the specified duration, with optional args.
def play_note(lines, note, time, length, d=0.875, ch=0, track=1):
    lines.append([track, time, "Note_on_c", ch, note, 80])
    lines.append([track, time + (length * d), "Note_off_c", ch, note, 0])

    return lines
