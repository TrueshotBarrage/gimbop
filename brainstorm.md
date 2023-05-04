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

## Clustering Chords

- Features: relative note timing (w.r.t. total song length & tempo), LH/RH
  likelihood (e.g. if a note is played in the LH, it is more likely to be a
  chord; a note in LH and RH cannot be a chord; how to determine this? look at
  the next section)

### Determining LH/RH

1. Average the min/max notes in the song. Gives rough split
2. Use the median note
3. Use the mean note

## Other Ideas

- Hypothesis: improved music generation (better prediction of notes)
