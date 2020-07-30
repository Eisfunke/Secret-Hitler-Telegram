# -*- coding: utf-8 -*-

import pickle
import random
import re
import sys
import time
import unicodedata
from enum import Enum
import functools

from telegram.error import Unauthorized, TelegramError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode

import bot_telegram

from model import *


# Fix for #14
all_unicode_chars = (chr(i) for i in range(sys.maxunicode))
non_printable_chars = ''.join(c for c in all_unicode_chars if unicodedata.category(c) == 'Cc')
non_printable_regex = re.compile('[%s]'%re.escape(non_printable_chars))


def strip_non_printable(s):
    return non_printable_regex.sub('', s)


with open("config/username", "r") as f:
    BOT_USERNAME = f.read().rstrip()

# TESTING = (__name__ == "__main__")  # test whenever this file is run directly
# set TESTING to True to simulate a game locally
# if not TESTING:

#    telegram_errors = []

    # unnecessary in TESTING mode

class GameOverException(Exception):
    pass

"""
def test_game():
    game = Game(None)
    players = [
        Player("1", "A"),
        Player("2", "B"),
        Player("3", "C"),
        Player("4", "D"),
        Player("5", "E"),
        Player("6", "F"),
        Player("7", "G")]

    for p in players:
        game.add_player(p)

    game.TEST_handle(players[2], "startgame")

    game.TEST_handle(players[0], "nominate", "D")  # election 1
    game.TEST_vote()

    game.TEST_handle(players[0], "discard", "L")
    game.TEST_handle(players[3], "enact", "F")  # 0L / 1F

    game.TEST_handle(players[1], "nominate", "E")  # election 2
    game.TEST_vote()
    game.TEST_handle(players[1], "discard", "L")
    game.TEST_handle(players[4], "enact", "F")

    game.TEST_handle(players[1], "investigate", "E")

    game.TEST_handle(players[2], "nominate", "F")  # election 3
    game.TEST_vote()
    game.TEST_handle(players[2], "discard", "L")
    game.TEST_handle(players[5], "enact", "F")

    game.TEST_handle(players[2], "nominate", "B")  # special elect

    game.TEST_handle(players[1], "nominate", "G")  # election 4
    game.TEST_vote()
    game.TEST_handle(players[1], "discard", "L")
    game.TEST_handle(players[6], "enact", "F")

    game.TEST_handle(players[1], "kill", "me too thanks")  # execution

    game.TEST_handle(players[3], "nominate",
                     "A")  # election 5 - should fail because dead people cannot vote and ties fail
    game.TEST_handle(players[0], "nein")
    game.TEST_handle(players[1], "ja")  # players[1] is dead
    game.TEST_handle(players[2], "ja")
    game.TEST_handle(players[3], "nein")
    game.TEST_handle(players[4], "nein")
    game.TEST_handle(players[5], "ja")
    game.TEST_handle(players[6], "ja")

    game.TEST_handle(players[4], "nominate", "A")  # election 6 - fail
    game.TEST_handle(players[0], "nein")
    game.TEST_handle(players[2], "ja")
    game.TEST_handle(players[3], "nein")
    game.TEST_handle(players[4], "nein")
    game.TEST_handle(players[5], "ja")
    game.TEST_handle(players[6], "ja")

    game.TEST_handle(players[5], "nominate", "A")  # election 7 - fail
    game.TEST_handle(players[0], "nein")
    game.TEST_handle(players[2], "ja")
    game.TEST_handle(players[3], "nein")
    game.TEST_handle(players[4], "nein")
    game.TEST_handle(players[5], "ja")
    game.TEST_handle(players[6], "ja")

    # anarchy, second bullet should be ignored

    game.TEST_handle(players[6], "nominate", "A")
    game.TEST_vote()

    game.TEST_handle(players[6], "discard", "s p i c y b o i")
    game.TEST_handle(players[0], "enact", "liberal")  # check other policy nomenclature

    game.TEST_handle(players[0], "ja")  # veto decisison
    game.TEST_handle(players[6], "nein")

    game.TEST_handle(players[0], "nominate", "D")
    game.TEST_vote()

    game.TEST_handle(players[0], "discard", "l")
    game.TEST_handle(players[3], "enact", "f")

    # veto decisison
    game.TEST_handle(players[0], "nein")
    # Fascist victory
    # game.handle_message(players[6], "ja") # other veto vote shouldn't matter


if TESTING:
    test_game()
"""
