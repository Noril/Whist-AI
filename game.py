import os
import sys
import numpy as np
from copy import copy
from typing import List

from cards import Deck, TrumpType, Card
from players import POSITIONS, Player, PositionEnum
from state import State
from trick import Trick


class Game:

    def __init__(self, agents,
                 games_counter: List[int],
                 tricks_counter: List[int],
                 verbose_mode: bool = True,
                 previous_tricks: List[Trick] = None,
                 curr_trick: Trick = None,
                 starting_pos: PositionEnum = None,
                 trump=None,
                 cards_in_hand=13,
                 hands_already_dealt=[]):
        self.cards_in_hand=cards_in_hand
        self.agents = agents  # type: IAgent
        self.games_counter = games_counter
        self.verbose_mode = verbose_mode
        if self.cards_in_hand == 13:
            trump = TrumpType.NT
        elif trump is None:
            while trump == TrumpType.NT or trump == None:
                trump = np.random.choice(TrumpType)
        else:
            trump = TrumpType.from_str(trump)
        self.trump = trump  # type: TrumpType
        self.deck = Deck(self.trump)
        hands = self.deck.deal(
            cards_in_hand=cards_in_hand,
            hands_already_dealt=hands_already_dealt
        )
        self.players = {pos: Player(pos, hand) for pos, hand in
                        zip(POSITIONS, hands)}
        
        self.curr_trick = curr_trick
        self.previous_tricks = previous_tricks
        self.tricks_counter = {player: tricks_counter[i] for i, player in enumerate(self.players.values())}
        self.score = {player: 0 for player in self.players.values()}

        if starting_pos is None:
            starting_pos = np.random.choice(POSITIONS)
        self.curr_player = self.players[starting_pos]
        self._state = None
        self.bids = self.compute_bids()

    def __str__(self):

        ret = ""

        ret += f"Match score: "
        for i, player in enumerate(self.players):
            ret += f"{player.name}:{self.games_counter[i]}"
            if i == len(self.players) - 1:
                ret += f"\n"
            else:
                ret += f"  "

        ret += f"Game score: "
        for i, player in enumerate(self.players.values()):
            ret += f"{player}:{self.tricks_counter[player]}"
            if i == len(self.players) - 1:
                ret += f"\n"
            else:
                ret += f"  "
        
        ret += f"Trump Suite: {self.trump.value}\n"
        ret += f"Bids:  "
        for player in self.players.values():
            ret += f"{player}:{self.bids[player]}  "
        ret += f"\nCurrent trick:  "
        for player, card in self.curr_trick.items():
            ret += f"{player}:{card}  "
        if len(self.curr_trick) == 4:
            ret += f", {self.players[self.curr_trick.get_winner()]} won trick."
        ret += f"\n"

        for player in self.players.values():
            ret += f"\n{player}\n{player.hand}"

        return ret
    
    def compute_bids(self, num_simulations=1000):
        from multi_agents import SimpleAgent, HumanAgent

        # Simulate game with agent maximizing number of tricks won
        bids = {}
        print(f"Trump Suite: {self.trump.value}\n")
        
        for i, player in enumerate(self.players.values()):
            print("Computing bid for player {}".format(player))
            print(f"\n{player}\n{player.hand}")
            agent = self.agents[i]
            
            if type(agent) == HumanAgent:
                inp = -1
                while inp < 0 or inp > self.cards_in_hand or (
                    i == len(self.players) - 1 and sum(bids.values()) + inp == self.cards_in_hand
                ):
                    print("What is your bid?")
                    inp = int(input())
                bids[player] = inp
            else:
                results = []
                for _ in range(num_simulations):
                    sim_agents = [SimpleAgent('random_action')] * len(self.players)
                    sim_agents[i] = SimpleAgent(agent.action_chooser_function)
                    simulated_game = SimulatedGame(
                        sim_agents,
                        False,
                        State(
                            self.curr_trick,
                            list(self.players.values()),
                            self.cards_in_hand,
                            self.previous_tricks,
                            self.tricks_counter,
                            self.score,
                            {player: self.cards_in_hand for player in self.players.values()}, # Max bid to push greed
                            self.curr_player,
                            self.trump
                        ),
                        None
                    )
                    simulated_game.run()
                    tricks_won = list(simulated_game.tricks_counter.values())[i]
                    results.append(tricks_won)

                optimal_bid = np.bincount(results).argmax()
                # If last player
                if i == len(self.players) - 1:
                    if sum(bids.values()) > self.cards_in_hand:
                        bids[player] = 0
                    elif sum(bids.values()) == self.cards_in_hand:
                        bids[player] = 1
                    else:
                        bids[player] = self.cards_in_hand - sum(bids.values())
                        bids[player] += 1 if optimal_bid > bids[player] else -1

                    if bids[player] != optimal_bid:
                        print("Player {} forced to bid {} instead of {}".format(
                            player,
                            bids[player],
                            optimal_bid
                        ))
                else:
                    bids[player] = optimal_bid
            
        return bids

    def compute_bids_old(self):
        # Draw 1M random hands of each size, then compute mean, std and 20-40-60-80 percentiles (see above)
        benchmark_values = {
            8: {'mean': 50.147472, 'std': 20.972235455697515, 'percentiles': [31., 42., 53., 68.]},
            9: {'mean': 56.420212, 'std': 21.999895906005012, 'percentiles': [37., 48., 60., 75.]},
            10: {'mean': 62.70239, 'std': 22.912973012856718, 'percentiles': [42., 54., 67., 82.]},
            11: {'mean': 68.982647, 'std': 23.74585951009967, 'percentiles': [48., 61., 73., 89.]},
            12: {'mean': 75.251363, 'std': 24.457838695236973, 'percentiles': [53., 67., 80., 96.]},
            13: {'mean': 81.486273, 'std': 25.197411366437446, 'percentiles': [ 59.,  73.,  86., 103.]}
        }

        bids = {}
        mean_value = benchmark_values[self.cards_in_hand]['mean']
        percentiles = benchmark_values[self.cards_in_hand]['percentiles']
        
        for i, player in enumerate(self.players.values()):
            hand_value = player.hand.get_bid_value()
            value_above_mean = hand_value >= mean_value
            mean_expected_tricks_won = self.cards_in_hand / len(self.players)
            
            j = 0
            while j < len(percentiles) and percentiles[j] < hand_value:
                j += 1
            
            optimal_bid = max(0, min(round(j * mean_expected_tricks_won / 2), self.cards_in_hand))
            
            
            # If last player
            if i == len(self.players) - 1:
                bids[player] = max(0, self.cards_in_hand - sum(bids.values()) + (
                    1 if value_above_mean else -1
                ))
            else:
                bids[player] = optimal_bid

        return bids

    def run(self) -> bool:
        """
        Main game runner.
        :return: None
        """
        score = {player: 0 for player in self.players.values()}

        initial_state = State(self.curr_trick, list(self.players.values()), self.cards_in_hand,
                              self.previous_tricks, self.tricks_counter, score, self.bids,
                              self.curr_player, trump=self.trump)
        self._state = initial_state
        self.previous_tricks = self._state.prev_tricks
        self.game_loop()
        return True

    def game_loop(self) -> None:
        while sum(self.tricks_counter.values()) < self.cards_in_hand:
            for _ in range(len(POSITIONS) - len(self.curr_trick)):
                self.play_single_move()
                if self.verbose_mode:
                    self.show()
            if self.verbose_mode:
                self.show()

        # Game ended, calc result.
        for player in self.players.values():
            tricks_won = self.tricks_counter[player]
            bid = self.bids[player]
            if tricks_won == bid:
                self.score[player] += bid
            else:
                self.score[player] -= abs(tricks_won - bid)

    def play_single_move(self) -> Card:
        """
        Called when its' the given player's turn. The player will pick a
        action to play and it will be taken out of his hand a placed into the
        trick.
        """
        curr_player_idx = list(self.players.values()).index(self.curr_player)
        card = self.agents[curr_player_idx].get_action(self._state)
        assert(card is not None)

        self.curr_trick = self._state.apply_action(card, True)
        self.curr_player = self._state.curr_player  # Current player of state is trick winner
        self.tricks_counter = {player: self._state.tricks_counter[player] for player in self.players.values()}
        return card

    def show(self) -> None:
        """
        Update GUI
        :return: None
        """

        #os.system('clear' if 'linux' in sys.platform else 'cls')
        print(self)
        #input()


class SimulatedGame(Game):
    """ Simulates a game with a non-empty state"""

    def __init__(self, agents,
                 verbose_mode: bool = True, state: State = None, starting_action=None):
        """

        :param State state: Initial game state.
        :param Card starting_action: Initial play of current player.
            If None, chosen according to `agent`'s policy.
        """

        state_copy = copy(state)
        self.players = {player.position: player for player in state_copy.players}
        self.tricks_counter = state_copy.tricks_counter
        self.bids = state_copy.bids
        self.starting_action = starting_action
        self.first_play = True
        self.agents = agents  # type: IAgent
        self.games_counter = [0, 0, 0, 0]
        self.verbose_mode = verbose_mode
        self.trump = state_copy.trump
        self.deck = Deck(self.trump)
        self.curr_trick = state_copy.trick
        self.previous_tricks = state_copy.prev_tricks
        self.score = state_copy.score
        self.curr_player = state_copy.curr_player
        self._state = state_copy

    def play_single_move(self, validation=''):
        if self.first_play and self.starting_action is not None:
            card = self.starting_action
            self.first_play = False
        else:
            curr_player_idx = list(self.players.values()).index(self.curr_player)
            card = self.agents[curr_player_idx].get_action(self._state)

        if validation == 'simple':
            return card

        curr_trick = self._state.apply_action(card, True)
        self.curr_trick = curr_trick
        self.curr_player = self._state.curr_player  # Current player of state is trick winner
        self.tricks_counter = {player: self._state.tricks_counter[player] for player in self.players.values()}
        return card

    def game_loop(self) -> None:
        if len(self.curr_trick.cards()) > 0:
            for card in self.curr_trick.cards():
                self._state.already_played.add(card)
        
        while sum(self.tricks_counter.values()) < self._state.cards_in_hand:
            for _ in range(len(POSITIONS) - len(self.curr_trick)):
                self.play_single_move()
                if self.verbose_mode:
                    self.show()
            if self.verbose_mode:
                self.show()
        
        # Game ended, calc result.
        for player in self.players.values():
            tricks_won = self.tricks_counter[player]
            bid = self.bids[player]
            if tricks_won == bid:
                self.score[player] += bid
            else:
                self.score[player] -= abs(tricks_won - bid)

    def run(self) -> bool:
        self.game_loop()
        return True
