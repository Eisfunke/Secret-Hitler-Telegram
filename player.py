# -*- coding: utf-8 -*-

from model import Player


def send_message(self: Player, msg, supress_errors=True, reply_markup=None):
#    if TESTING:
#        print("[ Message for {} ]\n{}".format(self, msg))
#    else:
    try:
        bot_telegram.bot.send_message(chat_id=self.id, text=msg, reply_markup=reply_markup)
    except TelegramError as e:
        if supress_errors:
            telegram_errors.append(e)
            # network issues can cause errors in Telegram
        else:
            raise e


def get_markdown_tag(self: Player):
    return "[{}](tg://user?id={})".format(self.name, self.id)


def set_role(self: Player, _role):
    """
    Sets a user's role/party affiliation and notifies them about it.
    """
    self.role = _role
    self.party = _role.replace("Hitler", "Fascist")
    self.send_message("Your secret role is {}".format(self.role))


def join_game(self: Player, _game):
    if leave_game(self, confirmed=False):
        self.game = _game
        return True
    else:
        return False  # user must first deal with leaving their current game


def leave_game(self, confirmed=False):
    if self.game is None:
        return True  # nothing to leave
    elif confirmed:
        # TODO after testing, don't require confirmation to leave these games
        # or self.game.game_state in (GameStates.GAME_OVER, GameStates.ACCEPT_PLAYERS):
        self.game.remove_player(self)
        self.game.remove_spectator(self)

        self.game = None
        self.role = None

        return True
    else:
        return False  # must confirm to successfully leave a game in one
        # of the more significant states
