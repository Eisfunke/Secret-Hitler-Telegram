from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey, Enum, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import enum


# Basic enums

class GameState(enum.Enum):
    """Enum for the different states a game can be in."""
    ACCEPT_PLAYERS = 1     # Game has not started yet and is accepting player entries.
    CHANCY_NOMINATION = 2  # The president has to nominate a chancellor.
    ELECTION = 3           # There is an ongoing election.
    LEG_PRES = 4           # Game is currently waiting on the president to discard a policy.
    LEG_CHANCY = 5         # The chancellor has to nominate a chancellor.
    VETO_CHOICE = 6        # Waiting on a veto decision.
    INVESTIGATION = 7      # The president has to decide which player to investigate.
    SPECIAL_ELECTION = 8   # Waiting for the president to pick a player for a special election.
    EXECUTION = 9          # The president has to choose a player to execute.
    GAME_OVER = 10         # The game has finished.


class Policy(enum.Enum):
    """Enum for a policy, can be either fascist or liberal."""
    F = 1  # A fascist policy.
    L = 2  # A liberal policy.


class Role(enum.Enum):
    """Enum for a role, can be either fascist, liberal or Hitler."""
    ROLE_FASCIST = 1  # A fascist player that isn't Hitler.
    ROLE_LIBERAL = 2  # A liberal player.
    ROLE_HITLER = 3   # Hitler.


# Classes for the ORM

Base = declarative_base()


class Game(Base):
    """Represents a single game of Secret Hitler."""
    __tablename__ = "games"

    def __init__(self, chat):
        self.chat = chat

    # The id of the group chat the game is in.
    chat = Column(Integer, primary_key=True)

    # The participating players.
    players = relationship("Player", foreign_keys="[Player.game_chat]",
                           cascade="all, delete, delete-orphan")

    cards = relationship("Card", cascade="all, delete, delete-orphan")  # Cards on the deck.
    discards = relationship("Discard")  # Discarded policies.

    president_id = Column(Integer, ForeignKey("players.id"))
    president = relationship("Player", foreign_keys="[Player.game_chat]")  # Current president.
    chancellor_id = Column(Integer, ForeignKey("players.id"))
    chancellor = relationship("Player", foreign_keys="[Player.game_chat]")  # Current chancellor.

    last_nonspecial_president_id = Column(Integer, ForeignKey("players.id"))
    last_nonspecial_president = relationship("Player",
                                             foreign_keys="[Game.last_nonspecial_president_id]")

    # The spectators.
    spectators = relationship("Spectator", cascade="all, delete, delete-orphan")

    # time_logs = relationship("TimeLog")
    # logs = relationship("Log")

    votes = relationship("Vote", foreign_keys="[Vote.game_id]",
                         cascade="all, delete, delete-orphan")

    vetoable_policy = Column(Enum(Policy))
    president_veto_vote = Column(Boolean)
    chancellor_veto_vote = Column(Boolean)

    liberal_policies = Column(Integer, default=0)
    fascist_policies = Column(Integer, default=0)
    anarchy_progress = Column(Integer, default=0)

    state = Column(Enum(GameState), default=GameState.ACCEPT_PLAYERS)


#log_player_table = Table("association", Base.metadata,
#                         Column("log", Integer, ForeignKey("logs.id")),
#                         Column("player", Integer, ForeignKey("players.id")))


class Player(Base):
    """
    Represents a single player in a single game. If a person is in multiple games at the same
    time, multiple Player instances are needed.
    """
    __tablename__ = "players"

    def __init__(self, chat_id, name):
        self.chat_id = chat_id
        self.name = name

    def __str__(self):
        return self.name

    id = Column(Integer, primary_key=True)
    chat = Column(Integer)
    name = Column(Text, nullable=False)

    game_id = Column(Integer, ForeignKey("games.chat"), nullable=False)

    role = Column(Enum(Role))

    termlimited = Column(Boolean)
    confirmed_not_hitler = Column(Boolean)
    dead = Column(Boolean)

    #known_logs = relationship("Log", secondary=log_player_table, back_populates="known_to")


class Spectator(Base):
    __tablename__ = "spectators"

    chat = Column(Integer, primary_key=True)  # The private chat with the spectator.

    game_id = Column(Integer, ForeignKey("games.chat"), nullable=False)
    game = relationship("Game", back_populates="spectators")


class Vote(Base):
    """Represents a single vote."""
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True)

    game_chat = Column(Integer, ForeignKey("games.chat"))

    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    vote = Column(Boolean, nullable=False)


class Card(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True)
    game_chat = Column(Integer, ForeignKey("games.chat"), nullable=False)
    policy = Column(Enum(Policy))


class Discard(Base):
    __tablename__ = "discards"

    id = Column(Integer, primary_key=True)

    game_chat = Column(Integer, ForeignKey("games.chat"), nullable=False)

    policy = Column(Enum(Policy))


"""class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True)

    game_id = Column(Integer, ForeignKey("games.chat"), nullable=False)
    game = relationship("Game", back_populates="logs")

    message = Column(Text, nullable=False)

    # Only lists players, not spectators, they have to be handled seperately
    known_to = relationship("Player", secondary=log_player_table, back_populates="known_logs")
    known_to_group = Column(Boolean)
"""

""" TODO Implement time logs
class TimeLog(Base):
    __tablename__ = "time_logs"

    id = Column(Integer, primary_key=True)

    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    game = relationship("Game", back_populates="time_logs")

    # time_logs : List<Map<GameState, Map<Player,Timestamp>>>
"""
