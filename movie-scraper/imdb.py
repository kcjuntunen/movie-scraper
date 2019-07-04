#!/usr/bin/python3

import sys
from imdb_page import ImdbPage

if __name__ == "__main__":
    ImdbPage(' '.join(sys.argv[1:])).render()
