#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 27 17:23:01 2018

@author: sbenamor
"""

from random import random
import numpy as np


def random_int_from_distr(proba_dist, n_sample=1):
    """ function that generate n random value according to a given
        discrete probability distribution proba_dist

    Args:
        - proba_dist (numpy array 2*m): discrete probability distribution with m possible value.
        - n_sample (int): number of generated samples.

    Returns:
        - list: list of n random generated values.

    Example:
        >>> randon_int_distr(np.array([[5],[1]]),1) #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        [5]
        >>> randon_int_distr(np.array([[2,3,8],[.1, .2, .7]]),1)[0] in [2,3,8]  #doctest: \
        +ELLIPSIS +NORMALIZE_WHITESPACE
        1
        >>> np.all(np.isin(randon_int_distr(np.array([[2,3,8],[.1, .2, .7]]),5), [2,3,8]))  \
        #doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        True
    """
    samples = []

    cdf = np.cumsum(proba_dist[1, :])    # Cumulative Distribution Function

    for _ in range(n_sample):
        proba = random()          # generate a probability value uniformly between 0 and 1
        rand_value_index = np.argmax(cdf > proba)    #  transform generated probability to a value from the distribution using cdf function
        samples.append(int(proba_dist[0, rand_value_index]))

    return samples


if __name__ == "__main__":
    import doctest
    doctest.testmod()
