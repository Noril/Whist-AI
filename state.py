from copy import copy
from typing import Dict, List

from cards import Card, TrumpType
from players import PLAYERS_CYCLE, Player
from trick import Trick


class State:
    """ Current state of the game of Bridge."""

    def __init__(self, trick: Trick,
                 players: List[Player],
                 cards_in_hand: int,
                 prev_tricks: List[Trick],
                 tricks_counter: Dict[Player, int],
                 score: Dict[Player, int],
                 bids: Dict[Player, int],
                 curr_player=None,
                 trump: TrumpType=TrumpType.NT) -> None:
        self.trick = trick
        self.players = players
        self.cards_in_hand = cards_in_hand
        self.prev_tricks = prev_tricks
        self.tricks_counter = tricks_counter
        self.score = score
        self.bids = bids
        self.curr_player = curr_player
        self.players_pos = {player.position: player for player in self.players}

        self.already_played = set()
        self.trump = trump

    def get_successor(self, action: Card):
        """

        :param action: Card to play
        :returns State: Resulting state of game if playing `action`
        """
        assert (action in self.get_legal_actions())

        players = [copy(self.players[i]) for i in range(len(self.players))]
        tricks_counter = {player: self.tricks_counter[player] for player in self.players}
        score = {player: self.score[player] for player in self.players}
        bids = {player: self.bids[player] for player in self.players}
        trick = self.trick.create_from_other_players(players)
        curr_player = [p for p in players if p == self.curr_player][0]

        successor = State(trick, players, self.cards_in_hand, self.prev_tricks, tricks_counter, score, bids,
                          curr_player, trump=self.trump)
        successor.apply_action(action)
        return successor

    def apply_action(self, card: Card, is_real_game: bool = False) -> Trick:
        """

        :param card: Action to apply on current state
        :param is_real_game: indicator to differentiate a state used in simulation of a game
        by the object Game, from a state used within tree search.
        :returns Trick: Trick status after applying card.
        """
        assert (len(self.trick) < len(self.players_pos))
        assert card not in self.already_played

        prev_num_cards = len(self.curr_player.hand.cards)
        self.curr_player.play_card(card)
        curr_num_cards = len(self.curr_player.hand.cards)
        assert prev_num_cards != curr_num_cards

        self.trick.add_card(self.curr_player, card)
        self.already_played.add(card)
        assert self.already_played.isdisjoint(self.curr_player.hand.cards)
        
        if len(self.trick) == len(self.players_pos):  # last card played - open new trick
            if is_real_game:
                self.prev_tricks.append(copy(self.trick))
            winner_position = self.trick.get_winner()
            self.curr_player = self.players_pos[winner_position]
            self.tricks_counter[self.curr_player] += 1
            self.trick = Trick({})
        else:
            assert self.curr_player in self.players_pos.values()
            assert self.curr_player in self.players
            # print(f"Mapping of position->next player: {repr(self.players_pos)}")
            self.curr_player = self.players_pos[PLAYERS_CYCLE[self.curr_player.position]]
            assert self.curr_player in self.players_pos.values()
            assert self.curr_player in self.players
        
        return self.trick

    def get_legal_actions(self) -> List[Card]:
        legal_actions = self.curr_player.get_legal_actions(self.trick, self.already_played)
        assert self.already_played.isdisjoint(legal_actions)
        return legal_actions

    def get_score(self, player) -> int:
        """
        Returns score of player
        """
        return self.score[player]

    def __copy__(self):
        trick = copy(self.trick)
        prev_tricks = [copy(trick) for trick in self.prev_tricks]
        players = [copy(player) for player in self.players]
        tricks_counter = {players[i]: self.tricks_counter[player] for i, player in enumerate(self.players)}
        score = {players[i]: self.score[player] for i, player in enumerate(self.players)}
        bids = {players[i]: self.bids[player] for i, player in enumerate(self.players)}
        curr_player_pos = self.curr_player.position
        state = State(trick, players, self.cards_in_hand, prev_tricks, tricks_counter, score, bids, None, trump=self.trump)
        state.curr_player = state.players_pos[curr_player_pos]
        played = set(self.already_played)
        state.already_played = played
        return state

    @property
    def is_game_over(self) -> bool:
        for player in self.players:
            if len(player.hand.cards) != 0:
                return False
        return True
