"""This script is a playground for generating a song with Gimbop."""

from src.setup import SongWriter


def main():
    writer = SongWriter(bpm=120)
    writer.write("test_song", sample_song=True)


if __name__ == "__main__":
    main()
