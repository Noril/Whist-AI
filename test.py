import random
import numpy as np
from IPython.utils import io

from match import run_match

def test_agents(agents, num_games=100):
    agents_dict = {idx: agent for idx, agent in enumerate(agents)}
    results = {"{}.{}".format(agent, idx): 0 for idx, agent in agents_dict.items()}

    for i in range(num_games):
        print("{}/{}".format(i+1, num_games))
        order = [0, 1, 2, 3]
        random.shuffle(order)

        with io.capture_output() as captured:
            result = run_match(
                agent1=agents_dict[order[0]],
                agent2=agents_dict[order[1]],
                agent3=agents_dict[order[2]],
                agent4=agents_dict[order[3]],
                num_games=1,
                cards_in_hand=8,
                verbose_mode=1
            )

        for i in range(4):
            results["{}.{}".format(agents_dict[order[i]], order[i])] += result[i]

        print(results)

    return results

if __name__ == '__main__':
    test_agents([
        'MCTS-pure-Whist-500',
        'MCTS-pure-Random-500',
        'Simple-Random',
        'Simple-Random'
    ])
