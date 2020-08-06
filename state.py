from copy import copy
from typing import Dict, List

from cards import Card
from players import PLAYERS_CYCLE, Player, Team
from trick import Trick


class State:
    """ Current state of the game of Bridge."""

    def __init__(self, trick: Trick,
                 teams: List[Team],
                 players: List[Player],
                 prev_tricks: List[Trick],
                 score: Dict[int, int],
                 curr_player=None) -> None:
        self.trick = trick
        self.teams = teams
        self.players = players
        self.prev_tricks = prev_tricks
        self.score = score  # tricks won by teams
        self.curr_player = curr_player
        self.players_pos = {player.position: player for player in self.players}

    def get_successor(self, action: Card):
        """

        :param action: Card to play
        :returns State: Resulting state of game if playing `action`
        """
        assert (action in self.get_legal_actions())

        teams = [copy(self.teams[i]) for i in range(len(self.teams))]
        score = {teams[i]: self.score[team] for i, team in
                 enumerate(self.teams)}
        players = teams[0].get_players() + teams[1].get_players()
        trick = self.trick.create_from_other_players(players)
        curr_player = [p for p in players if p == self.curr_player][0]

        successor = State(trick, teams, players, self.prev_tricks, score,
                          curr_player)
        successor.apply_action(action)
        return successor

    def apply_action(self, card: Card, is_real_game:bool = False) -> None:
        """

        :param card: Action to apply on current state
        :param is_real_game: TODO [oriyan] Maryna, what is this?
        """
        assert (len(self.trick) < len(self.players_pos))
        self.curr_player.play_card(card)
        self.trick.add_card(self.curr_player, card)
        if len(self.trick) == len(self.players_pos):  # last card played - open new trick
            if is_real_game:
                self.prev_tricks.append(copy(self.trick))
            self.curr_player = self.trick.get_winner()
            i = 0 if self.teams[0].has_player(self.curr_player) else 1
            self.score[self.teams[i]] += 1
            self.trick = Trick({})
        else:
            self.curr_player = self.players_pos[PLAYERS_CYCLE[self.curr_player.position]]

    def get_legal_actions(self) -> List[Card]:
        return self.curr_player.get_legal_actions(self.trick)

    def get_score(self, curr_team_indicator) -> int:
        """ Returns score of team

        :param curr_team_indicator: [oriyan] is this for determining if player is max/min player? clarification needed
        :returns: current score of team
        """
        # assume there are 2 teams
        i, j = (0, 1) if self.teams[0].has_player(self.curr_player) else (1, 0)
        curr_team, other_team = self.teams[i], self.teams[j]
        if curr_team_indicator:
            return self.score[curr_team]
        return self.score[other_team]