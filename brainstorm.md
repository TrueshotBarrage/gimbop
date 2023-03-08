# Brainstorming/Ideapad

- Classic RNN structure: Given a sequence of notes (e.g. 25 notes in a row), use
  the first 24 as data and the last 1 as label. Then train using the neural net
- Now, instead of using raw notes, cluster notes in a hierarchical manner:

## Note Hierarchy

1. Chords

- Make sure to differentiate between chords and simultaneous notes (e.g. RH/LH)

2. (common) Chord progressions
3. Sections (e.g. verse, chorus, bridge)

A good clustering of these may be useful for transfer learning.

- Hypothesis: improved music generation (better prediction of notes)
