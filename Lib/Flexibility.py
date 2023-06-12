# -*- coding: utf-8 -*-
__author__ = 'LiYuanhe'

import sys
import os
import math
import copy
import shutil
import re
import time
import random

from My_Lib_Stock import *
import numpy as np
from Lib import *


def coverage(input_list,full_range = (-180,180)):
    '''
    get a input list of values at each time frame, generate a value of the coverage
    this value should be [1,1,2,3,3,4,5] < [1,1,1,1,2,3,60,63,62,64] < [1,5,10,16,20,25,30] < [0,10,20,30,40,50,70,90]
    one should be able to compare this value with different number of point, and with a fixed legend
    (i.e., not dependent on other list, methods that are relying on maximizing difference is not a good definition)

    To smear with some function? But how flat should I choose
    Sort by most close differences?

    :param input_list:
    :param full_range:
    :return: a float point number between 0 and 1, representing the softness.
    '''



test_mol2file = r"D:\Gaussian\XXXXXXXXXXXXX\31.mol2"

mol2_bond_order = get_bond_order_from_mol2_file(test_mol2file)
mol2_coordinate = [std_coordinate(x) for x in open(test_mol2file).readlines()] # just to fill up the get_dihedrals function
mol2_coordinate = Coordinates(remove_blank(mol2_coordinate))
mol2_dihedrals = get_dihedrals(mol2_coordinate,mol2_bond_order,ignore_hydrogens=False)

def read_mdcrd_coordinate(mdcrd_file, atoms_to_take:int, total_atom:int, periodic:bool):
    '''
    read a mdcrd_file, take the coordinate of the first n atoms, return a list of molecule coordinates, which consist of numpy 3-arrays
    :param mdcrd_file:
    :param atoms_to_take: take how many atoms
    :param total_atom:
    :param periodic:
    :return:
    '''
    mdcrd_file_content = ''.join(open(mdcrd_file).readlines()[1:]) #去除标题行
    mdcrd_file_numbers = [float(x) for x in mdcrd_file_content.split()]
    number_count_per_cycle = (total_atom + (1 if periodic else 0))*3
    assert len(mdcrd_file_numbers)%number_count_per_cycle == 0, "mdcrd doesn't contain whole molecule. "+str(len(mdcrd_file_numbers))+" "+str(number_count_per_cycle)
    frame_count = int(len(mdcrd_file_numbers)/number_count_per_cycle)

    ret = []

    for frame in range(frame_count):
        molecule = mdcrd_file_numbers[frame*number_count_per_cycle:frame*number_count_per_cycle+atoms_to_take*3]
        molecule = [np.array(molecule[atom_count*3:atom_count*3+3]) for atom_count in range(atoms_to_take)]

        ret.append(molecule)

    return ret

mdcrd_frames = read_mdcrd_coordinate(r"D:\Gaussian\XXXXXXXXXXXXXXXX\confsearch_pickonly2.mdcrd",
                                     85, 1255, True)

from collections import OrderedDict
ret_dict = OrderedDict()
for dihedral_object in mol2_dihedrals:
    ret_dict[tuple(dihedral_object.atom_indexes)] = [calculate_dihedral_angle(*[frame[atom] for atom in dihedral_object.atom_indexes]) for frame in mdcrd_frames]




time.sleep(1)