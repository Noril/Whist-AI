from copy import copy
from enum import Enum
from typing import List

from cards import Hand, Card


PositionEnum = Enum("PlayersEnum", ['N', 'E', 'S', 'W'])

POSITIONS = list(PositionEnum)

PLAYERS_CYCLE = {PositionEnum.N: PositionEnum.E,
                 PositionEnum.E: PositionEnum.S,
                 PositionEnum.S: PositionEnum.W,
                 PositionEnum.W: PositionEnum.N}


class Player:
    """ Represents one of the 4 players in the game."""

    def __init__(self, position: PositionEnum, hand: Hand):
        """

        :param position: Position of player
        :param hand: Initial hand of player
        """
        self.position = position
        self.hand = hand
        self.played = set()

    def __copy__(self):
        hand = copy(self.hand)
        player = Player(self.position, hand)
        player.played = set(self.played)
        return player

    def play_card(self, card: Card) -> None:
        """ Plays card from hand. card is no longer available."""
        assert card not in self.played
        self.hand.play_card(card)
        self.played.add(card)

    def get_legal_actions(self, trick, already_played) -> List[Card]:
        """ Returns list of legal actions for player in current trick

        :param Trick trick: Current trick
        :param already_played: Set of cards already used in state, used for unit testing.
        :returns: legal actions for player:
        """
        legal_actions = self.hand.get_cards_from_suite(trick.starting_suit, already_played)
        assert self.played.isdisjoint(legal_actions)
        assert already_played.isdisjoint(legal_actions)
        if not legal_actions:
            legal_actions = self.hand.cards
            assert already_played.isdisjoint(legal_actions)
        return legal_actions

    def __str__(self):
        return self.position.name

    def __eq__(self, other):
        return self.position == other.position

    def __hash__(self):
        return hash(self.position)


def get_legal_actions(suit, player, already_played) -> List[Card]:
    legal_actions = player.hand.get_cards_from_suite(suit, already_played)
    if not legal_actions:
        legal_actions = player.hand.cards
    else:
        trump_cards = [card for card in player.hand.cards if card.is_trump]
        legal_actions.extend(trump_cards)
    return legal_actions
