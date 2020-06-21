#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# stats_tools.py
# Created: Darren Yeap 04.09.2020


def walk_forward_split(indexarray=None, cumm_traintest_ratio=0.5, n_splits=3):
    """Returns a list of tuples where each tuple has two list. The first list
    consist of two items: the first and last index of the training set. The 
    second list contains two items: first and last index of test set.
    
    Keyword Arguments:
        indexarray {list} -- An array of the series to split (default: {0.5})
        cumm_traintest_ratio {float} -- total proportion of whole set to be used
            as test set (default: {0.5})
        n_splits {int} -- number of splits to create for the given set. 
            (default: {3})
    
    Returns:
        [list] -- Empty list if no array is given. A list of tuple where each 
            tuple has a two list, a list for first and last index of training 
            set and a list of first and last index of test set. 
    """
    data_size = len(indexarray)
    train_start_index = 0
    train_end_index = data_size//(1+cumm_traintest_ratio)
    cumm_test_size = data_size - train_end_index
    test_size = cumm_test_size//n_splits
    split_points = []
    for i in range(n_splits):
        split_points.append((
            [int(train_start_index),int(train_end_index)]
            , [int(train_end_index),int(train_end_index+test_size)]
        )
        )
        train_start_index += test_size
        train_end_index += test_size
    return split_points