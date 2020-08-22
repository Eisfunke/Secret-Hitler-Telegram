#!/usr/bin/env python

import logging
import os
import sys
import threading
from subprocess import call

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import Base, Game, GameState

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
from telegram.error import TelegramError

DEV_CHAT_ID = int(os.environ["SECRET_HITLER_BOT_DEVCHAT"])

updater = Updater(os.environ["SECRET_HITLER_BOT_TOKEN"], use_context=True)
# restored_players = {}
# restored_game = {}
# MAINTENANCE_MODE = False
MAX_MESSAGE_LENGTH = 4096
# existing_games = {}  # Chat ID -> Game
# waiting_players_per_group = {}  # Chat ID -> [Chat ID]


engine = create_engine("sqlite:///:memory:")
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()
Base.metadata.create_all(engine)

ACCEPTED_COMMANDS = ("listplayers", "changename", "startgame",
                     "boardstats", "deckstats", "anarchystats", "blame", "ja", "nein",
                     "nominate", "kill", "investigate", "enact", "discard", "whois",
                     "spectate", "unspectate", "logs", "timelogs")


def main():
    # global restored_players
    # global restored_game
    # global updater

    # if len(sys.argv) > 1:
    #    restored_game = secret_hitler.Game.load(sys.argv[1])
    #    for p in restored_game.players:
    #        restored_players[p.id] = p
    # else:
    #    restored_game = None

    # Set up all command handlers

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start_handler))
    # dispatcher.add_handler(get_static_handler("help"))
    # dispatcher.add_handler(CommandHandler('feedback', feedback_handler, pass_args=True))

    dispatcher.add_handler(CommandHandler('newgame', newgame_handler, pass_chat_data=True))
    dispatcher.add_handler(CommandHandler('cancelgame', cancelgame_handler, pass_chat_data=True))
    dispatcher.add_handler(CommandHandler('leave', leave_handler, pass_user_data=True))
#    dispatcher.add_handler(CommandHandler('nextgame', nextgame_handler, pass_chat_data=True))
    dispatcher.add_handler(CommandHandler('joingame', joingame_handler, pass_chat_data=True, pass_user_data=True))
    dispatcher.add_handler(CommandHandler(ACCEPTED_COMMANDS, game_command_handler, pass_chat_data=True, pass_user_data=True))

    dispatcher.add_handler(CallbackQueryHandler(button_handler, pass_chat_data=True, pass_user_data=True))

    dispatcher.add_error_handler(handle_error)

    # allows viewing of exceptions
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)  # not sure exactly how this works

    updater.start_polling()
#    updater.bot.send_message(chat_id=DEV_CHAT_ID, text="Good morning, comrades! \
#                                                        The bot has started. Let's crush fascism.\n\nbtw: richard ist ein frechdachs")


def split_message(message, length=MAX_MESSAGE_LENGTH):
    return [message[i:i + length] for i in range(0, len(message), length)]


def start_handler(update: Update, context: CallbackContext):
    message = "Hi! This bot runs games of Secret Hitler via Telegram. Add me to a chat with all \
              players and send the /newgame command there. This will specify where all public \
              information is posted."
    context.bot.send_message(chat_id=update.message.chat.id, text=message)


def newgame_handler(update: Update, context: CallbackContext):
    """
    Create a new game.
    """

    chat_id = update.message.chat.id

    if update.message.chat.type == "private":
        context.bot.send_message(chat_id=chat_id, text="You can’t create a game in a private chat!")
    else:
        game = session.query(Game).get(chat_id)
        if game is not None and game.game_state is not GameState.GAME_OVER:
            context.bot.send_message(chat_id=chat_id, text="There is a game already running here. \
                                                            Cancel it first to start a new one.")
        else:
            if game is not None:
                game.set_game_state(GameState.GAME_OVER)
                # TODO clean up
                # TODO notify waiting
            session.add(Game(chat_id))
            session.commit
            updater.bot.send_message(chat_id=chat_id, text="**Created new game!**\nUse /joingame to join and /startgame to start.")


""" def nextgame_handler(bot, update, chat_data):

    Add the issuing player to the current group’s waiting list if there is a game in progress.

    game = chat_data.get("game_obj")
    chat_id = update.message.chat.id
    if update.message.chat.type == "private":
        bot.send_message(chat_id=chat_id, text="You can’t wait for new games in private chat!")
    if game is not None and game.game_state == secret_hitler.GameState.ACCEPT_PLAYERS and game.num_players<10 and update.message.from_user.id not in map(lambda player: player.id, game.players) and update.message.text.find("confirm")==-1:
        bot.send_message(chat_id=chat_id, text="You could still join the _current_ game via /joingame. Type '/nextgame confirm' if you really want to wait.", parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        if "{}".format(chat_id) not in waiting_players_per_group:
            waiting_players_per_group["{}".format(chat_id)]=[]
        waiting_players_per_group["{}".format(chat_id)].append(update.message.from_user.id)
        bot.send_message(chat_id=update.message.from_user.id, text="I will notify you when a new game starts in [{}]({})".format(update.message.chat.title, bot.export_chat_invite_link(chat_id=chat_id)), parse_mode=telegram.ParseMode.MARKDOWN) """


def cancelgame_handler(bot, update, chat_data):
    """
    Cancel a game.
    """
    game = chat_data.get("game_obj")

    chat_id = update.message.chat.id
    if game is not None:
        game.end_game("whole", "Game has been cancelled{}".format("" if MAINTENANCE_MODE else ". Type /newgame to start a new one"))
        del existing_games["{}".format(chat_id)]
    else:
        bot.send_message(chat_id=chat_id, text="No game in progress here.")


def joingame_handler(bot, update, chat_data, user_data):
    if "{}".format(update.message.chat.id) in waiting_players_per_group and waiting_players_per_group["{}".format(update.message.chat.id)] is not None and update.message.from_user.id in waiting_players_per_group["{}".format(update.message.chat.id)]:
        waiting_players_per_group["{}".format(update.message.chat.id)].remove(update.message.from_user.id)
    game_command_handler(bot, update, chat_data, user_data)


def leave_handler(bot, update, user_data):
    """
    Forces a user to leave their current game, regardless of game state (could
    kill the game)
    """

    player_id = update.message.from_user.id
    # edge case: first message after restore is /leave
    global restored_players
    if player_id in list(restored_players.keys()):
        user_data["player_obj"] = restored_players[player_id]
        del restored_players[player_id]

    player = user_data.get("player_obj")

    if player is None or player.game is None:
        reply = "No game to leave!"
    else:
        game = player.game
        player.leave_game(confirmed=True)
        reply = "Successfully left game!"
        if game is not None and game.game_state==secret_hitler.GameStates.ACCEPT_PLAYERS and game.num_players==9:
            for waiting_player in waiting_players_per_group["{}".format(game.global_chat)]:
                bot.send_message(chat_id=waiting_player, text="A slot just opened up in [{}]({})!".format(bot.get_chat(chat_id=game.global_chat).title, bot.export_chat_invite_link(chat_id=game.global_chat)), parse_mode=telegram.ParseMode.MARKDOWN)
    if player is None:
        bot.send_message(chat_id=update.message.chat.id, text=reply)
    else:
        player.send_message(reply)


def button_handler(bot, update, chat_data, user_data):
    """
    Handles any command sent to the bot via an inline button
    """
    command, args = parse_message(update.callback_query.data)
    game_command_executor(bot, command, args, update.callback_query.from_user, update.callback_query.message.chat.id, chat_data, user_data)
    update.callback_query.message.edit_reply_markup()


def parse_message(msg):
    """
    Helper function: split a messsage into its command and its arguments (two strings)
    """
    command = msg.split()[0]
    if command.endswith(bot.username):
        command = command[1:command.find("@")]
    else:
        command = command[1:]
    args = msg.split()[1:]
    if len(args) == 0:
        args = ""  # None
    else:
        args = " ".join(args)
    return command, args


def game_command_handler(bot, update, chat_data, user_data):
    command, args = parse_message(update.message.text)
    game_command_executor(bot, command, args, update.message.from_user, update.message.chat.id, chat_data, user_data)


def game_command_executor(bot, command, args, from_user, chat_id, chat_data, user_data):
    """
    Pass all commands that secret_hitler.Game can handle to game's handle_message method
    Send outputs as replies via Telegram
    """

    # Try to restore relevant save data (and mark this data as dirty)
    global restored_game
    global restored_players
    if restored_game is not None and restored_game.global_chat == chat_id:
        chat_data["game_obj"] = restored_game
        restored_game = None
    if from_user.id in list(restored_players.keys()):
        user_data["player_obj"] = restored_players[from_user.id]
        del restored_players[from_user.id]

    player = None
    game = None
    if "player_obj" in list(user_data.keys()):
        player = user_data["player_obj"]
    if "game_obj" in list(chat_data.keys()):
        game = chat_data["game_obj"]

    # game = ((player is not None) and player.game) or chat_data["game_obj"]
    if player is None:
        # this is a user's first interaction with the bot, so a Player
        # object must be created
        if game is None:
            bot.send_message(chat_id=chat_id, text="Error: no game in progress here. Start one with /newgame")
            return
        else:
            if args and (game.check_name(args) is None):  # args is a valid name
                player = secret_hitler.Player(from_user.id, args)
            else:
                # TODO: maybe also chack their Telegram first name for validity
                player = secret_hitler.Player(from_user.id, from_user.first_name)

            user_data["player_obj"] = player
    else:
        # it must be a DM or something, because there's no game in the current chat
        if game is None:
            game = player.game

        # I don't know how you can end up here
        if game is None:
            bot.send_message(chat_id=chat_id, text="Error: it doesn't look like you're currently in a game")
            return

    # at this point, 'player' and 'game' should both be set correctly

    try:
        reply = game.handle_message(chat_id, player, command, args)
        # DEBUG Print time logs data structure to dev chat
        #   if command == "timelogs":
        #     bot.send_message(chat_id=DEV_CHAT_ID, text=game.print_time_logs())
        # pass all supressed errors (if any) directly to the handler in
        # the order that they occurred
        while len(secret_hitler.telegram_errors) > 0:
            handle_error(bot, command, secret_hitler.telegram_errors.pop(0))
        # TODO: it would be cleaner to just have a consumer thread handling
        # these errors as they occur

        if reply:  # reply is None if no response is necessary
            for part in split_message(reply):
                bot.send_message(chat_id=chat_id, text=part, parse_mode=telegram.ParseMode.MARKDOWN)

    except secret_hitler.GameOverException:
        if "{}".format(game.global_chat) in existing_games:
            del existing_games["{}".format(game.global_chat)]
        if len(existing_games) == 0 and MAINTENANCE_MODE:
            restart_executor()
        elif MAINTENANCE_MODE:
            bot.send_message(chat_id=DEV_CHAT_ID, text="A game has ended but there are {} more games, so I won’t restart yet".format(len(existing_games)))
        else:
            bot.send_message(chat_id=DEV_CHAT_ID, text="A game has ended.")
        return


def handle_error(bot, update, error):
    try:
        raise error
    except TelegramError:
        logging.getLogger(__name__).warning('TelegramError! %s caused by this update: %s', error, update)


if __name__ == "__main__":
    main()
