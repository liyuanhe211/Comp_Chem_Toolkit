# -*- coding: utf-8 -*-
__author__ = 'LiYuanhe'

import sys
import pathlib

parent_path = str(pathlib.Path(__file__).parent.resolve())
sys.path.append(parent_path)

from Python_Lib.My_Lib_Stock import *
from Lib_Constants import *
import numpy as np


class Coordinates:
    def __init__(self, coordinates=(), charge: Union[int, str] = 999, multiplet: Union[int, str] = 999, selected_atom_range=(), is_xtb=False, periodic_cell=()):
        """

        Args:
            coordinates:
                A list of lines containing coordinate information.
                Could be a filepath, the last molecule matching std_coordinate() is obtained.
                    In this scenario, the charge and multiplicity is not read.
                Or could be a list of strings, and each string should match std_coordinate()

            charge:

            multiplet:

            selected_atom_range: select atoms with number starts from zero, others will be removed

            is_xtb:
                XTB 产生的XYZ的元素是小写，默认不匹配，为true时做一次upper()

            periodic_cell:
                zero to three lines of PBC vector, in the forms like:
                ["18.86654729     0.00000000     0.00000000"
                 "0.00000000    20.01084904     0.00000000"
                 "0.00000000     0.00000000    19.12138942"]

        Atrributes:

        Methods:
            注意PBC是后加的，许多函数会直接忽视PBC，比如 eq和hash

        """

        self.hashnum: Optional[int] = None

        self.coordinates = []  # a list of std_coordinate()

        if isinstance(coordinates, str) and os.path.isfile(coordinates):
            # 可以传一个文件进来，读取最后一个坐标，不过charge和multiplet读不了，需要指定
            with open(coordinates) as coordinates_file:
                coordinates_lines = coordinates_file.readlines()
            for count in range(len(coordinates_lines) - 1, -1, -1):
                line = coordinates_lines[count]
                if is_xtb:
                    line = line.strip()[0].upper() + line.strip()[1:]
                if std_coordinate(line):
                    # 插入时是倒序的
                    self.coordinates.append(std_coordinate(line))
                    for coord_line_count in range(count - 1, -1, -1):
                        self.coordinates.append(std_coordinate(coordinates_lines[coord_line_count]))
                        if not self.coordinates[-1]:
                            self.coordinates.pop()
                            break
                    self.coordinates.reverse()
                    break
        elif isinstance(coordinates, list) or isinstance(coordinates, tuple):
            for line in coordinates:
                if line:
                    if is_xtb:
                        line = line.strip()[0].upper() + line.strip()[1:]
                    self.coordinates.append(std_coordinate(line))

            # print(self.coordinates)
        elif isinstance(coordinates, str):
            for line in coordinates.splitlines():
                if line:
                    if is_xtb:
                        line = line.strip()[0].upper() + line.strip()[1:]
                    self.coordinates.append(std_coordinate(line))

        else:
            print("Coordinates object input invalid. Exiting...")
            exit()

        if selected_atom_range:
            self.coordinates = [x for count, x in enumerate(self.coordinates) if count in selected_atom_range]

        self.periodic_cell = []
        for vectors in periodic_cell:
            self.periodic_cell.append("\t".join(vectors.split()))
        print(self.periodic_cell)
        assert len(self.periodic_cell) <= 3, "PBC condition more than 3-dimensional."
        assert list(set(len(x.split('\t')) for x in self.periodic_cell)) == [3], "PBC vector not 3-dimensional."

        self.charge = int(charge)
        self.multiplicity = int(multiplet)

        if None in self.coordinates:
            print("Internal coordinate system or other unmatchable pattern. Further coordinate operation not supported.")
            self.is_fault = True

        else:
            self.is_fault = False
            self.elements = [coord.split('\t')[0].upper() for coord in self.coordinates]
            self.elements = [(x[0].upper() + x[1:].lower() if not is_int(x) else x) for x in self.elements]
            self.elements = [(x if x in element_to_num_dict else num_to_element_dict[x]) for x in self.elements]
            self.elements_num = [element_to_num_dict[x] for x in self.elements]
            self.coordinates_numer = [[float(x) for x in coord.split('\t')[1:4]] for coord in self.coordinates]
            self.coordinates_np = [np.array(coord) for coord in self.coordinates_numer]
            self.atom_count = len(self.coordinates_numer)

            # self.get_distance_matrix()

    def check_charge_and_multiplicity_parity(self):
        # check whether charge and multiplicity is correct
        if self.charge == 999 or self.multiplicity == 999 or self.multiplicity == 99:
            return False
        number_of_electrons = sum(self.elements_num) + self.charge
        if number_of_electrons % 2 == self.multiplicity % 2:
            return False

        return True

    def __add__(self, other):
        """
        Generate a new object, where new atoms were added,
        :param other: one str, which should be std_coordinate recognizable, or a list of lines all being recognizable
        :return: a new Coordinate object
        """

        if isinstance(other, str):
            return Coordinates(self.coordinates + [other])
        elif isinstance(other, list):
            return Coordinates(self.coordinates + other)

    def __sub__(self, other):
        """
        Generate a new object, where a selected atom is deleted
        :param other: an int, atom index start from 1; or an list of int, multiple atom indexes start from 1
        :return: a new Coordinate object
        """
        if isinstance(other, int):
            return Coordinates([x for count, x in enumerate(self.coordinates) if count != other - 1])
        elif isinstance(other, list) or isinstance(other, tuple):
            return Coordinates([x for count, x in enumerate(self.coordinates) if count not in [x - 1 for x in other]])

    def formula(self):
        a = list(collections.Counter(self.elements).items())

        def sort_function(element):
            starter_dict = {'C': -5, 'H': -4, 'O': -3, 'N': -2}
            if element in starter_dict:
                return starter_dict[element]
            else:
                return element_to_num_dict[element]

        a.sort(key=lambda x: sort_function(x[0]))

        return "".join([x[0] + str(x[1]) for x in a])

    def CDA_fragments(self, *selection_str):
        # for a selection of n fragments, return N+2 objects, the first one is the whole system, rearranged
        # atom order for CDA fragment, the second to last one is N+1 fragments as selection
        # self is not affected

        selected_atoms = []
        fragments = []
        ret = []
        for string in selection_str:
            phrased_range = phrase_range_selection(string)
            if not phrased_range:
                continue
            fragments.append(phrased_range)
            selected_atoms += phrased_range
            ret.append(Coordinates([self.coordinates[i] for i in phrased_range], self.charge, self.multiplicity))

        if len(set(selected_atoms)) != len(selected_atoms):
            # 有重复选择
            alert_UI("CDA selection is false.")
            return []

        last_fragment = [x for x in list(range(self.atom_count)) if x not in selected_atoms]
        if last_fragment:
            fragments.append(last_fragment)
            ret.append(Coordinates([self.coordinates[i] for i in last_fragment], self.charge, self.multiplicity))

        ret = [Coordinates([self.coordinates[i] for i in sum(fragments, [])], self.charge, self.multiplicity)] + ret

        return ret

    def replace_element_for_one_atom(self, atom_count, element=None):
        """
        replace the element of one certain atom to tne new one
        :param atom_count: starts from 1

        Args:
            element:
        """
        atom_count = int(atom_count) - 1
        self.elements[atom_count] = element
        self.coordinates = [self.elements[count] + "\t" + "\t".join(coord.split('\t')[1:]) for count, coord in enumerate(self.coordinates)]

    def replace_elements(self, replacement_str):
        """
        replace the multiple elements, with formats of Atom_num, New element, Atom_num, New Element
        atom_num starts from 1
        e.g. 108 N 32 N 97 N 16 N 8 Pd 9 O 111 N
        """

        replacement_str = replacement_str.split()
        assert len(replacement_str) % 2 == 0
        nums = [x for count, x in enumerate(replacement_str) if count % 2 == 0]
        elements = [x for count, x in enumerate(replacement_str) if count % 2 == 1]
        assert all([is_int(x) for x in nums])
        for count, num in enumerate(nums):
            self.replace_element_for_one_atom(num, elements[count])

    def replace_element_list(self, element_list):
        assert len(element_list) == self.atom_count
        # 用于构象搜索时替换元素
        self.elements = element_list
        self.coordinates = [element_list[count] + "\t" + "\t".join(coord.split('\t')[1:]) for count, coord in enumerate(self.coordinates)]

    def get_distance_matrix(self):
        if not hasattr(self, 'distance_matrix'):
            self.distance_matrix = [[-1] * self.atom_count for _ in range(self.atom_count)]  # n*n matrix
            for i in range(self.atom_count):
                self.distance_matrix[i][i] = 0
            for i in range(self.atom_count):
                for j in range(i):
                    distance = np.linalg.norm(self.coordinates_np[i] - self.coordinates_np[j])
                    self.distance_matrix[i][j] = distance
                    self.distance_matrix[j][i] = distance
            assert -1 not in sum(self.distance_matrix, []), 'Distance Matrix Error'

        return self.distance_matrix

    def has_too_close(self, threshold=0.5):
        """
        Check whether there exists two atoms that has a distance shorter than threshold * covalent bond length
        :param file: Gaussian_input_file
        :param threshold:
        :return:
        """
        from Python_Lib.mogli.mogli import ATOM_VALENCE_RADII
        self.get_distance_matrix()
        self.threshold_matrix = [[-1] * self.atom_count for _ in range(self.atom_count)]  # n*n matrix
        for i in range(self.atom_count):
            self.threshold_matrix[i][i] = -1
        for i in range(self.atom_count):
            for j in range(i):
                distance = (ATOM_VALENCE_RADII[self.elements_num[i]] + ATOM_VALENCE_RADII[self.elements_num[j]])
                self.threshold_matrix[i][j] = distance * threshold
                self.threshold_matrix[j][i] = distance * threshold
        # assert -1 not in sum(self.threshold_matrix, []), 'Threshold Matrix Error'
        minimum_ratio = 1000
        for i in range(self.atom_count):
            for j in range(i):
                if self.distance_matrix[i][j] / self.threshold_matrix[i][j] < minimum_ratio:
                    minimum_ratio = self.distance_matrix[i][j] / self.threshold_matrix[i][j]
                if self.distance_matrix[i][j] < self.threshold_matrix[i][j]:
                    print("\t\t\t\tMinimum (should be vDW distance):", "{:.2f}".format(minimum_ratio * threshold * 2), 'times of sum of valence distance.')
                    return True
        print("\t\t\t\tMinimum (should be vDW distance):", "{:.2f}".format(minimum_ratio * threshold * 2), 'times of sum of valence distance.')
        return False

    def __hash__(self):
        # 用于放到excel里用来表明结构相同性的数值，这个hash的重复处理的不好，谨慎使用

        if self.hashnum != "":  # 算过了
            return self.hashnum
        else:
            hash_num = sorted(sum(self.get_distance_matrix(), []))
            hash_num = int((sum(hash_num, 0) * 100000) % 1000000000)  # 精确到5位，取后9位
            self.hashnum = hash_num
            return hash_num  # 取一个6位的hash

    def is_linear(self):
        if len(self.coordinates) <= 2:
            return True

        # 分子共线性判断
        # 得到第一个原子和第二个原子的坐标

        coord_0 = self.coordinates_np[0]
        coord_1 = self.coordinates_np[1]
        ref_distance_vec = coord_1 - coord_0  # -->(C1-C2)
        ref_distance_norm = np.linalg.norm(ref_distance_vec)  # |-->(C1-C2)|

        for coord in self.coordinates_np[2:]:
            distance_vec = coord - coord_0  # -->(C1-Cn)
            distance_norm = np.linalg.norm(distance_vec)  # |-->(C1-Cn)|

            ratio = distance_norm / ref_distance_norm  # norm ratio
            compair_vec = ref_distance_vec * ratio  # if the molecule is linear, this should be exact eq to _distance_vec_

            # the diff_vec can be scaled in two directions, chose the smaller one
            pos_diff_vec = (distance_vec - compair_vec) / ratio
            neg_diff_vec = (distance_vec + compair_vec) / ratio

            # 若差的模大于5E-6(相当于[2E-6,2E-6,2E-6])，判定为非线性
            # 修改为1E-3了，高斯把179.96904 也看成线性，没办法
            if min(np.linalg.norm(pos_diff_vec), np.linalg.norm(neg_diff_vec)) > 1E-3:
                return False

        return True

    def __eq__(self, other):
        # 原子顺序不得改变，但分子可旋转
        assert isinstance(other, Coordinates)

        if self.atom_count != other.atom_count:
            return False

        if self.elements != other.elements:
            return False

        if self.charge != other.charge:
            return False

        if self.multiplicity != other.multiplicity:
            return False

        if hasattr(self, 'distance_matrix'):
            self_distance_matrix = self.distance_matrix
        else:
            self_distance_matrix = self.get_distance_matrix()

        if hasattr(other, 'distance_matrix'):
            other_distance_matrix = other.distance_matrix
        else:
            other_distance_matrix = other.get_distance_matrix()

        diff_distance_matrix = np.array(sum(self_distance_matrix, [])) - np.array(sum(other_distance_matrix, []))
        diff_distance_matrix = [abs(x) for x in list(diff_distance_matrix)]
        if max(diff_distance_matrix) > 3E-6:
            return False

        return True

    def __str__(self):
        return '\n'.join(self.coordinates) + '\nTV\t' + '\nTV\t'.join(self.periodic_cell)

    def gjf(self, title='Geometry from coordinate object', override_charge=0, override_multiplicity=1):
        return '#p\n\n' + title.strip() + '\n\n' + str(override_charge) + ' ' + str(override_multiplicity) + '\n' + str(self)

    def gjf_file(self, title='Geometry from coordinate object', filename=None, override_charge=0, override_multiplicity=1):

        # return a filename that are the generated gjf_file

        if not filename:
            filename = os.path.join(TEMP_FOLDER_PATH, 'temp_' + readable_timestamp() + '.gjf')

        with open(filename, 'w') as output_file_object:
            output_file_object.write(self.gjf(title=title, override_charge=override_charge, override_multiplicity=override_multiplicity))
        return filename

    def open_GView(self):
        config = open_config_file()
        gview_exe = get_config(config, 'Gview_Path', r"C:\g16w\gview.exe")
        if not os.path.isfile(gview_exe):
            exe = get_open_file_UI(None, r"C:\g16w", 'exe', 'Choose GView .exe')
            if os.path.isfile(exe):
                gview_exe = exe

        config['Gview_Path'] = gview_exe
        save_config(config)
        subprocess.Popen([gview_exe, self.gjf_file()])

    def xyz(self, title='Geometry from coordinate object'):
        title = str(title)
        return str(self.atom_count) + '\n' + title.replace('\n', " ") + '\n' + str(self)

    def xyz_file(self, title='Geometry from coordinate object', filename=None):

        # return a filename that are the generated xyz_file
        title = str(title)

        if not filename:
            self_directory = filename_class(sys.argv[0]).path
            temp_directory = os.path.join(self_directory, 'Temp')
            if not os.path.isdir(temp_directory):
                os.mkdir(temp_directory)
            filename = os.path.join(temp_directory, 'temp' + str(random.randint(0, 12345678)) + '.xyz')

        with open(filename, 'w') as output_file_object:
            output_file_object.write(self.xyz(title=title))
        return filename

    def get_connection_dict(self):
        # {0: [1, 3, 4], 1: [0, 2, 10], 2: [1], 3: [0], 4: [0, 5, 6], 5: [4], 6: [4, 7, 8],
        #  7: [6], 8: [6, 9, 10], 9: [8], 10: [1, 8, 11], 11: [10, 12, 13, 14], 12: [11],
        #  13: [11], 14: [11, 15], 15: [14, 16, 17, 49], 16: [15], 17: [15, 18, 19, 34],
        #  18: [17], 19: [17, 20, 21, 22], 20: [19], 21: [19], 22: [19, 23, 24, 25], 23: [22],
        #  24: [22], 25: [22, 26, 27, 28], 26: [25], 27: [25], 28: [25, 29, 30, 31], 29: [28],
        #  30: [28], 31: [28, 32, 33, 34], 32: [31], 33: [31], 34: [17, 31, 35, 36], 35: [34, 49],
        #  36: [34, 37, 38, 39], 37: [36], 38: [36], 39: [36, 40, 41, 42], 40: [39], 41: [39],
        #  42: [39, 43, 47, 61], 43: [42, 44, 45, 46], 44: [43], 45: [43], 46: [43], 47: [42, 48, 49, 53],
        #  48: [47], 49: [15, 35, 47, 50], 50: [49, 51], 51: [50, 52, 53], 52: [51], 53: [47, 51, 54, 55],
        #  54: [53], 55: [53, 56, 60, 61], 56: [55, 57, 58, 59], 57: [56], 58: [56], 59: [56], 60: [55],
        #  61: [42, 55, 62], 62: [61]}

        if not hasattr(self, 'connections'):
            self.connections = get_bonds(self.xyz_file(), neighbor_list=True)

        return self.connections


def get_bond_order_from_mol2_file(file, selected_atoms=(), add_bond=""):
    """
    get the bond order information in mol2 file
    :param file:
    :param exclude_atoms: 用于排除其中的几个原子，搞自由基的时候用
    :param add_bond: a str with the format of "1-2,1-5", atom count start from 0, where a (single) bond will be added if they are not bonded before
    :return: a list of 3-tuples, (atom1, atom2, bond_order)
    e.g.
    [[0, 1, 1], [1, 2, 1], [2, 3, 1], [3, 4, 1], [4, 5, 1], [4, 6, 1], [4, 7, 1], [3, 8, 1], [8, 9, 1],
    [8, 10, 1], [8, 11, 1], [1, 12, 1], [12, 13, 1], [13, 14, 1], [13, 15, 1], [15, 16, 1], [16, 17, 1],
    [16, 18, 1], [16, 19, 1], [15, 20, 1], [20, 21, 1], [20, 22, 1], [22, 23, 1], [22, 24, 1], [22, 25, 1],
     [25, 26, 1], [25, 27, 1], [27, 28, 1], [27, 29, 1], [29, 30, 1], [29, 31, 1], [31, 32, 1], [32, 33, 1],
     [33, 34, 1], [34, 35, 1], [34, 36, 1], [34, 37, 1], [37, 38, 1], [37, 39, 1], [37, 40, 1], [33, 41, 1],
     [41, 42, 1], [41, 43, 1], [41, 44, 1], [44, 45, 1], [44, 46, 1], [44, 47, 1], [33, 48, 1], [48, 49, 1],
     [48, 50, 1], [48, 51, 1], [51, 52, 1], [51, 53, 1], [51, 54, 1], [31, 55, 1], [55, 56, 1], [55, 57, 1],
     [55, 58, 1], [58, 59, 1], [58, 60, 1], [58, 61, 1], [61, 62, 1], [62, 63, 1], [62, 64, 1], [62, 65, 1],
     [61, 66, 1], [66, 67, 1], [66, 68, 1], [66, 69, 1], [69, 70, 1], [69, 71, 1], [71, 72, 1], [72, 73, 1],
     [72, 74, 1], [74, 75, 1], [75, 76, 1], [75, 77, 1], [77, 78, 1], [77, 79, 1], [79, 80, 1], [80, 81, 1],
     [3, 20, 1], [12, 25, 1], [12, 31, 1], [26, 27, 1], [61, 72, 1], [74, 80, 1]]

    Args:
        selected_atoms:
    """

    ret = []

    # convert "1-2,1-5" to [(1,2),(1,5)]
    if not add_bond:
        add_bond = []
    else:
        add_bond = add_bond.split(",")
        new_add_bond = []
        for bond in add_bond:
            bond = bond.split('-')
            bond = [int(x) - 1 for x in bond]
            bond.sort()
            new_add_bond.append(bond)

        add_bond = new_add_bond

    with open(file) as mol2_file:
        mol2_file_lines = mol2_file.readlines()

    for count, line in enumerate(mol2_file_lines):
        if "@<TRIPOS>BOND" in line:
            for bonding_line in mol2_file_lines[count + 1:]:
                if '@' in bonding_line:
                    break
                bonding_line = bonding_line.replace('ar', '1')  # 芳香键问题
                bonding_line = bonding_line.replace('Ar', '1')  # 芳香键问题
                ret.append([int(x) for x in bonding_line.split()[1:]])

            break

    ret = sorted([sorted([atom1 - 1, atom2 - 1]) + [bond_order] for atom1, atom2, bond_order in ret])

    # print(ret)

    for bond in add_bond:
        for existed_bond in ret:
            if bond[0] == existed_bond[0] and bond[1] == existed_bond[1]:
                break
        else:
            ret.append(bond + [1])

    ret.sort()

    if selected_atoms:
        ret = [x for x in ret if x[0] in selected_atoms and x[1] in selected_atoms]

        max_num = max(sum([bond[:2] for bond in ret], []))

        swap_pair = collections.OrderedDict()
        # 因为去掉了一些，所以后面的原子要前移
        for x in range(max_num + 1):
            swap_pair[x] = x - len([i for i in range(x) if i not in selected_atoms])

        for bond in ret:
            bond[0] = swap_pair[bond[0]]
            bond[1] = swap_pair[bond[1]]

    return ret


def coordinate_from_cube_file(cube_file):
    line_count = 0
    for line in open(cube_file):
        line_count += 1
        if line_count == 3:
            atom_count = int(line.split()[0])
            break
    coordinate_lines = []
    line_count = 0
    for line in open(cube_file):
        line_count += 1
        if 7 <= line_count <= 6 + atom_count:
            coordinate_lines.append(std_coordinate("\t".join([line.split()[0]] + line.split()[-3:])))
        if line_count > 6 + atom_count:
            break

    coordinate_object = Coordinates(coordinate_lines)
    return coordinate_object


def get_dihedral(coordinate, atom_indexes):
    """

    :param coordinate:
    :param atom_indexes: same as the Dihedral class
    :return:
    """
    if atom_indexes[1] > atom_indexes[2]:
        atom_indexes = list(reversed(atom_indexes))
    return Dihedral(coordinate, atom_indexes).dihedral


def get_distance(coordinate: Coordinates, atom_indexes, count_from_1=False):
    """

    :param coordinate:
    :param atom_indexes: start from 0, if not stated
    :return:

    Args:
        count_from_1:
        count_from_1:
    """

    if count_from_1:
        atom_indexes = [x - 1 for x in atom_indexes]

    coord1 = coordinate.coordinates_np[atom_indexes[0]]
    coord2 = coordinate.coordinates_np[atom_indexes[1]]

    return np.linalg.norm(coord1 - coord2)


def angle_np(coord1, coord2, coord3):
    """

    :param coordinate:
    :return:

    Args:
        coord3:
        coord2:
        coord1:
    """

    vector1 = coord1 - coord2
    vector2 = coord3 - coord2

    cosine_angle = np.dot(vector1, vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2))
    angle = np.degrees(np.arccos(cosine_angle))

    return angle


def get_angle(coordinate: Coordinates, atom_indexes):
    """

    :param coordinate:
    :param atom_indexes:  should be out_atom, center_atom, another_out_atom, start from 0
    :return:
    """
    coord1 = coordinate.coordinates_np[atom_indexes[0]]
    coord2 = coordinate.coordinates_np[atom_indexes[1]]
    coord3 = coordinate.coordinates_np[atom_indexes[2]]

    return angle_np(coord1, coord2, coord3)


def get_unit_vector(vector):
    return vector / np.linalg.norm(vector)


def get_normal_vector(point1, point2, point3):
    vector = np.cross(point3 - point2, point2 - point1)
    return get_unit_vector(vector)


def get_plane(coordinate_object: Coordinates, atoms):
    """
    determine the average origin and average unit normal vector from the coordinate of several (>=3) atoms
    :param coordinate_object:
    :param atoms: atom number starts from 0
    :return: an average origin and an average vector, (and a set of coordinates?)
    """

    import itertools
    normal_vectors = []

    for three_atom in itertools.combinations(atoms, 3):
        coord_nps = [coordinate_object.coordinates_np[x] for x in three_atom]
        normal_vector = get_normal_vector(*coord_nps)
        if normal_vectors and np.dot(normal_vector, normal_vectors[-1]) > 0.5:
            normal_vectors.append(normal_vector)
        else:
            normal_vectors.append(-normal_vector)

    temp = np.zeros(3)
    for i in [coordinate_object.coordinates_np[x] for x in atoms]:
        temp += i
    origin_ret = temp / len(atoms)

    temp = np.zeros(3)
    for i in normal_vectors:
        temp += i
    #    print(temp)
    normal_vector_ret = get_unit_vector(temp / len(normal_vectors))
    # print(unit_vector_ret)

    return origin_ret, \
           normal_vector_ret, \
           [coordinate_object.coordinates_np[x] for x in atoms], \
           coordinate_object.coordinates_np


def calculate_dihedral_angle(coord_np_1, coord_np_2, coord_np_3, coord_np_4):
    """
    Same as the Dihedral class, only without creating a class object, just return a number.
    :param coord_np_1:
    :param coord_np_2:
    :param coord_np_3:
    :param coord_np_4:
    :return:
    """
    vec1 = coord_np_2 - coord_np_1
    vec2 = coord_np_3 - coord_np_2
    vec3 = coord_np_4 - coord_np_3

    normal1 = np.cross(vec1, vec2)
    normal2 = np.cross(vec2, vec3)

    normal1 = normal1 / np.linalg.norm(normal1)
    normal2 = normal2 / np.linalg.norm(normal2)

    x = normal1
    y = vec2 / np.linalg.norm(vec2)
    z = np.cross(x, y)

    n2_x = np.dot(normal2, x)
    n2_y = np.dot(normal2, z)

    dihedral = -math.atan2(n2_y, n2_x) / math.pi * 180

    return dihedral


def get_xyz_by_3point_Z_matrix(atom1, atom2, atom3, length, angle, dihedral):
    """
    Convert a length/angle/dihedral relationship to a cartesian end-point
    :param atom1: atom1-atom2-atom3-ret_atom forms the dihedral relationship
    :param atom2:
    :param atom3:
    :param length: atom3 - ret_atom bond length, in angstrom
    :param angle: atom2 - atom3 - ret_atom bond length
    :param dihedral: atom1 - atom2 - atom3 - ret_atom bond length
    :return: the cartesian coordinate np.ndarray of the ret_atom
    """
    Z_matrix = """C
                  C 1 {}
                  C 2 {} 1 {}
                  C 3 {} 2 {} 1 {}"""

    dist_12 = np.linalg.norm(atom1 - atom2)
    dist_23 = np.linalg.norm(atom2 - atom3)
    angle_123 = angle_np(atom1, atom2, atom3)
    Z_matrix = Z_matrix.format(dist_12, dist_23, angle_123, length, angle, dihedral)

    # print(Z_matrix)

    from Z_Mat_to_Cartesian_Conversion import z_mat_to_cartesian
    ret = z_mat_to_cartesian(Z_matrix, atom1, atom2, atom3)
    return ret[-1][1]


def get_xyz_by_3point_Z_matrix_Coordinates_obj(molecule: Coordinates, atom_count1, atom_count2, atom_count3, length, angle, dihedral):
    """

    :param molecule:
    :param atom_count1: start from 1
    :param atom_count2:
    :param atom_count3:
    :param length:
    :param angle:
    :param dihedral:
    :return:
    """
    atom1, atom2, atom3 = molecule.coordinates_np[atom_count1 - 1], \
                          molecule.coordinates_np[atom_count2 - 1], \
                          molecule.coordinates_np[atom_count3 - 1]
    # print(atom1,atom2,atom3)
    return get_xyz_by_3point_Z_matrix(atom1, atom2, atom3, length, angle, dihedral)


class Dihedral:
    def __init__(self, coordinate: Coordinates, atom_indexes):
        """

        :param coordinate:
        :param atom_indexes:  should be left-atom, center_bond1, center_bond2, right-atom.
                                center_bond1 must be smaller than center_bond2
        :return:
        """
        # read this for the symbols http://math.stackexchange.com/questions/47059/how-do-i-calculate-a-dihedral-angle-given-cartesian-coordinates

        assert len(atom_indexes) == 4
        self.coordinate = coordinate
        self.atom_indexes = atom_indexes
        self.atom1, self.atom2, self.atom3, self.atom4 = self.atom_indexes
        self.atom_index_compare = 1E12 * self.atom1 + 1E8 * self.atom2 + 1E4 * self.atom3 + self.atom4  # 产生一个数字，用于两对象相同的快速比对，假设原子坐标不会超过10000

        assert self.atom2 < self.atom3  # 应该以此顺序传入
        self.elements = [self.coordinate.elements[index] for index in self.atom_indexes]

        # calculate dihedral
        self.coord1, self.coord2, self.coord3, self.coord4 = [self.coordinate.coordinates_np[index] for index in self.atom_indexes]

        self.vec1 = self.coord2 - self.coord1
        self.vec2 = self.coord3 - self.coord2
        self.vec3 = self.coord4 - self.coord3

        self.normal1 = np.cross(self.vec1, self.vec2)
        self.normal2 = np.cross(self.vec2, self.vec3)

        self.normal1 = self.normal1 / np.linalg.norm(self.normal1)
        self.normal2 = self.normal2 / np.linalg.norm(self.normal2)

        self.x = self.normal1
        self.y = self.vec2 / np.linalg.norm(self.vec2)
        self.z = np.cross(self.x, self.y)

        self.n2_x = np.dot(self.normal2, self.x)
        self.n2_y = np.dot(self.normal2, self.z)

        self.dihedral = -math.atan2(self.n2_y, self.n2_x) / math.pi * 180

    def __lt__(self, other):
        if self.atom2 != other.atom2:
            return self.atom2 < other.atom2
        elif self.atom3 != other.atom3:
            return self.atom3 < other.atom3
        elif self.atom1 != other.atom1:
            return self.atom1 < other.atom1
        return self.atom4 < other.atom4

    def __eq__(self, other):
        return self.atom_index_compare == other.atom_index_compare

    def __gt__(self, other):
        return not self < other and not self == other

    def __ge__(self, other):
        return not self < other

    def __le__(self, other):
        return self < other or self == other

    def __sub__(self, other):
        # return the abs() of angle difference of two dihedral angle
        # note that -180 and 180 are the same point, -170 and 170 has difference of 20
        # it will verify the atom indexes are the same
        assert self.atom_indexes == other.atom_indexes

        candidate = [abs(self.dihedral - other.get_dihedral), abs(self.dihedral + 360 - other.get_dihedral), abs(self.dihedral - 360 - other.get_dihedral)]

        return min(candidate)

    def __str__(self):
        return '-'.join([self.coordinate.elements[x] for x in self.atom_indexes]) + " " \
               + '-'.join([str(x + 1) for x in self.atom_indexes]) \
               + '  {:.2f}'.format(self.dihedral)


def calculate_geometry_element(coordinate: Coordinates, element_tuple):
    """ calculate the value for a current coordinate,
    count start from 0
    :param coordiante:
    :param element_tuple: a tuple, 2 for length, 3 for angle, 4 for dihedral
    :return:
    """

    if len(element_tuple) == 2:
        return get_distance(coordinate, element_tuple)
    elif len(element_tuple) == 3:
        return get_angle(coordinate, element_tuple)
    elif len(element_tuple) == 4:
        return get_dihedral(coordinate, element_tuple)


def get_dihedrals(coordinate: Coordinates,
                  bond_orders=(),
                  ignore_hydrogens=True,
                  return_dict=False,
                  only_pick_one_necessary=True,
                  ignore_CX3=True):
    """
    :param coordinate:
    :param bond_orders: 从mol2文件读入的bond order，list of 3-tuple，或者没有bond order也可以，list of 2-tuple；如果此参数为空，将用mogli判断的键级
    :param ignore_hydrogens: 是否计算含H的二面角，默认为否
    :param return_dict: 如果开启，将*额外*返回一个字典，用于通过四原子tuple访问二面角对象
    :param only_pick_one_necessary: 如果开启，即假设键角不变，如乙烷的3*3共9个二面角中，只挑选1个代表
    :param ignore_CX3: 如果为True，则CH3,CF3等二面角不予输出，用于构象搜索，反之，则输出，用于二面角统计
    :return: if not return dict: a list of Dihedral objects;
             else: a two tuple, the first is the above list; the second is a dict, the dict can be accessed by
                        dict[(1,2,3,4)] == dict[(4,3,2,1)]
    """

    if isinstance(coordinate, tuple) and bond_orders == []:
        # 从pool传过来的
        coordinate, bond_orders, ignore_hydrogens, return_dict, only_pick_one_necessary = coordinate

    temp_filename = 'temp.xyz'
    with open(temp_filename, 'w') as temp_structure_file:
        temp_structure_file.write(str(coordinate.atom_count))
        temp_structure_file.write("\nTemp file for Molecule object\n")
        temp_structure_file.write(str(coordinate))

    if not bond_orders:
        bonds = get_bonds(temp_filename)
        print("Warning, bond order not pre-specified in dihedral calculation")
    else:
        bonds = [x[0:2] for x in bond_orders]

    connection_table = bonds_to_connect_table(coordinate, bonds)
    single_bonding_atoms = [x for x in range(coordinate.atom_count) if len(connection_table[x]) == 1]
    hydrogens = [atom for atom in range(coordinate.atom_count) if coordinate.elements[atom] == 'H']

    ret = []

    # 选取一根键，找两边的键，做排列组合
    for bond in bonds:

        # if bond[0]==31 and bond[1]==34:
        #     print("test")

        assert bond[0] < bond[1], 'Bonds setting error.'
        left_bonding_atoms = [x for x in connection_table[bond[0]] if x != bond[1]]
        right_bonding_atoms = [x for x in connection_table[bond[1]] if x != bond[0]]

        # print(left_bonding_atoms)
        # print(right_bonding_atoms)

        # 如果键连的几个原子相同，直接忽略其二面角，如CF3整体旋转120°；对同取代烯烃相同
        have_CX3 = False
        for bonding_atoms in [left_bonding_atoms, right_bonding_atoms]:
            have_CX3 = len(bonding_atoms) in [2, 3] and \
                       not [x for x in bonding_atoms if x not in single_bonding_atoms] and \
                       len(set([coordinate.elements[x] for x in bonding_atoms])) == 1
            if have_CX3:
                break

        if have_CX3 and ignore_CX3:
            continue

        # 如果键连的三个原子中有两个原子都是单连原子且相同，则认定余下的一个为关键原子，应用于如CF2,CH2的情况
        def remove_duplicate_nonbonding_atom(bonding_atoms):
            if len(bonding_atoms) == 3:
                singles = [x for x in bonding_atoms if x in single_bonding_atoms]
                if len(singles) == 2:
                    singles_elements = [coordinate.elements[x] for x in singles]
                    duplicate_element = [x for x in singles_elements if singles_elements.count(x) > 1]
                    if duplicate_element:
                        return [x for x in bonding_atoms if not (x in singles and coordinate.elements[x] == duplicate_element[0])]
            return bonding_atoms

        if only_pick_one_necessary:
            left_bonding_atoms = remove_duplicate_nonbonding_atom(left_bonding_atoms)
            right_bonding_atoms = remove_duplicate_nonbonding_atom(right_bonding_atoms)
        # print("left",left_bonding_atoms)
        # print("right",right_bonding_atoms)

        found_one = False
        for left_atom in left_bonding_atoms:

            if found_one and only_pick_one_necessary:
                break
            if ignore_hydrogens and left_atom in hydrogens:
                # print('a')
                continue

            for right_atom in right_bonding_atoms:
                if right_atom == left_atom:  # 防止三元环A-B-C-A键角
                    continue
                if found_one and only_pick_one_necessary:
                    break
                if ignore_hydrogens and right_atom in hydrogens:
                    # print('a')
                    continue

                ret.append(Dihedral(coordinate, [left_atom] + bond + [right_atom]))
                found_one = True

    ret.sort()
    if not return_dict:
        return ret
    else:
        ret_dict = {}
        for dihedral in ret:
            ret_dict[tuple(dihedral.atom_indexes)] = dihedral
            ret_dict[tuple(reversed(dihedral.atom_indexes))] = dihedral
        return (ret, ret_dict)


def bonds_to_connect_table(coordinate: Coordinates, bonds):
    """

    :param bonds: list of 2-tuple bonds, index start from 0
    :return: a list, length same as the atom count, of lists
    """
    ret = [[] for _ in range(coordinate.atom_count)]
    for atom in range(coordinate.atom_count):
        ret[atom] = [bond for bond in bonds if atom in bond]
        ret[atom] = [bond[0] if bond[0] != atom else bond[1] for bond in ret[atom]]

    return ret


def get_connectivity_from_coordinate(coordinates: Coordinates, bond_radii_factor=1.3):
    temp_filename = 'Temp/temp' + str(hash(coordinates)) + '.xyz'
    with open(temp_filename, 'w') as temp_structure_file:
        temp_structure_file.write(str(coordinates.atom_count))
        temp_structure_file.write("\nTemp file for Molecule object\n")
        temp_structure_file.write(str(coordinates))

    bonds_detected = get_bonds(temp_filename, bond_radii_factor=1.3)
    bonds_str = ", ".join(["-".join([str(atom) for atom in x]) for x in bonds_detected])

    if os.path.isfile(temp_filename):
        os.remove(temp_filename)

    return bonds_str


class Molecule_Stereo:
    def __init__(self, coordinates: Coordinates, bond_orders=(), add_bond=""):
        """
        ZE的判断需要bond order提前定义好
        :param coordinates:
        :param bond_orders: a list of 3-tuples, (atom1, atom2, bond-order)
        :param add_bond: a str with the format of "1-2,1-5", atom count start from 0, where a (single) bond will be added if they are not bonded before

        :return:
        """

        from Python_Lib.My_Lib_Chemistry import get_bonds
        self.coordinates = coordinates
        temp_filename = 'temp' + str(hash(coordinates)) + '.xyz'
        with open(temp_filename, 'w') as temp_structure_file:
            temp_structure_file.write(str(coordinates.atom_count))
            temp_structure_file.write("\nTemp file for Molecule object\n")
            temp_structure_file.write(str(coordinates))

        self.bond_orders = bond_orders
        self.bonds_detected = get_bonds(temp_filename, add_bond=add_bond)

        if os.path.isfile(temp_filename):
            os.remove(temp_filename)

        if not self.bond_orders:
            self.bonds = self.bonds_detected
        else:
            self.bonds = [x[0:2] for x in self.bond_orders]
        self.bonds_str = ", ".join(["-".join([str(atom) for atom in x]) for x in self.bonds])

        self.has_bond_order = True if self.bond_orders else False
        self.methyl_carbons = []
        self.recognize_methyl_carbon()

        self.get_chirality()
        self.get_ZE()

    def recognize_methyl_carbon(self):
        # 包括甲基和三氟甲基
        for atom in range(self.coordinates.atom_count):
            bonding_atoms = [pair[0] if pair[0] != atom else pair[1] for pair in self.bonds if atom in pair]
            if len(bonding_atoms) == 4:
                if len([H_check for H_check in bonding_atoms if self.coordinates.elements[H_check] == 'H']) == 3:
                    self.methyl_carbons.append(atom)
                if len([H_check for H_check in bonding_atoms if self.coordinates.elements[H_check] == 'F']) == 3:
                    self.methyl_carbons.append(atom)

    def get_chirality(self):
        """

        :return: a list of chirality of each atom, 0 for no chiral, 1 for positive projection, -1 for neg
        """
        self.chirality = [0 for _ in range(self.coordinates.atom_count)]
        for atom in range(self.coordinates.atom_count):
            bonding_atoms = [pair[0] if pair[0] != atom else pair[1] for pair in self.bonds if atom in pair]
            if len(bonding_atoms) == 4:

                # 亚甲基、甲基、三氟甲基等的氢、氟容易两个互相翻转，数相同元素的数量，如果有两个无其他成键的原子（如H，卤素）就排除掉
                # 选取某个碳上连接的所有无其他键连的元素，考虑有无重复的
                non_bonding_atoms = [atom2 for atom2 in bonding_atoms if len([pair for pair in self.bonds if atom2 in pair]) == 1]
                element_of_non_bonding_atoms = [self.coordinates.elements[atom2] for atom2 in non_bonding_atoms]
                if len(set(element_of_non_bonding_atoms)) < len(element_of_non_bonding_atoms):
                    continue

                # 去除甲基碳
                if len([x for x in bonding_atoms if x in self.methyl_carbons]) > 1:
                    continue

                bonding_atoms.sort()
                bonding_coord = [self.coordinates.coordinates_np[atom] for atom in bonding_atoms]
                # 以序号最小的原子为原点，计算其他三个原子的相对坐标
                rel_coord = [bonding_coord[i] - bonding_coord[0] for i in range(1, 4)]
                # 将序号最大的向量向其他两个向量的叉乘上投影
                projection = np.dot(rel_coord[2], np.cross(*rel_coord[0:2]))
                self.chirality[atom] = int(np.sign(projection))

            # 连烯
            if len(bonding_atoms) == 2 and self.coordinates.elements[atom].lower() == 'c':
                # 某碳 A，连有且只连有两个原子，都是碳，这两个碳原子分别均只连有三个基团
                bonding_elements = [self.coordinates.elements[atom] for atom in bonding_atoms]

                # 只连有两个碳，都是碳
                if len(bonding_elements) == 2 and list(set(bonding_elements))[0].lower() == 'c':
                    # 找出连接原子，排除同碳上的相同非键原子，以中心原子为中心，去掉连烯两边的原子，判断手性
                    atom1 = bonding_atoms[0]
                    atom2 = bonding_atoms[1]
                    bonding_atoms1 = [pair[0] if pair[0] != atom1 else pair[1] for pair in self.bonds if atom1 in pair]
                    bonding_atoms2 = [pair[0] if pair[0] != atom2 else pair[1] for pair in self.bonds if atom2 in pair]
                    assert atom in bonding_atoms1
                    assert atom in bonding_atoms2
                    bonding_atoms1.remove(atom)  # 去掉自己
                    bonding_atoms2.remove(atom)  # 去掉自己
                    # element1 = self.coordinates.elements[atom1].strip().lower()
                    # element2 = self.coordinates.elements[atom2].strip().lower()

                    if len(bonding_atoms1) == 2 == len(bonding_atoms2):

                        # 亚甲基、甲基、三氟甲基等的氢、氟容易两个互相翻转，数相同元素的数量，如果有两个无其他成键的原子（如H，卤素）就排除掉
                        # 选取某个碳上连接的所有无其他键连的元素，考虑有无重复的
                        non_bonding_atoms = [test_atom for test_atom in bonding_atoms1 if len([pair for pair in self.bonds if test_atom in pair]) == 1]
                        element_of_non_bonding_atoms = [self.coordinates.elements[test_atom] for test_atom in non_bonding_atoms]
                        if len(non_bonding_atoms) == 2 and len(set(element_of_non_bonding_atoms)) == 1:
                            continue
                        non_bonding_atoms = [test_atom for test_atom in bonding_atoms2 if len([pair for pair in self.bonds if test_atom in pair]) == 1]
                        element_of_non_bonding_atoms = [self.coordinates.elements[test_atom] for test_atom in non_bonding_atoms]
                        if len(non_bonding_atoms) == 2 and len(set(element_of_non_bonding_atoms)) == 1:
                            continue

                        chiral_atoms = bonding_atoms1 + bonding_atoms2
                        chiral_atoms.sort()
                        bonding_coord = [self.coordinates.coordinates_np[atom] for atom in chiral_atoms]
                        # 以序号最小的原子为原点，计算其他三个原子的相对坐标
                        rel_coord = [bonding_coord[i] - bonding_coord[0] for i in range(1, 4)]
                        # 将序号最大的向量向其他两个向量的叉乘上投影
                        projection = np.dot(rel_coord[2], np.cross(*rel_coord[0:2]))
                        self.chirality[atom] = int(np.sign(projection))

        self.chirality_str = "".join(["P" if x > 0 else "N" if x < 0 else "-" for x in self.chirality])

    def get_ZE(self):
        self.ZE = [0 for _ in range(self.coordinates.atom_count)]
        if self.bond_orders:
            for atom1, atom2, bond_order in self.bond_orders:
                if bond_order == 2:
                    # print(atom1,atom2)
                    # 只支持C
                    # N的翻转无特殊情况被视为同一种结构，有需要的时候直接改代码
                    bonding_atoms1 = [pair[0] if pair[0] != atom1 else pair[1] for pair in self.bonds if atom1 in pair]
                    bonding_atoms2 = [pair[0] if pair[0] != atom2 else pair[1] for pair in self.bonds if atom2 in pair]
                    element1 = self.coordinates.elements[atom1].strip().lower()
                    element2 = self.coordinates.elements[atom2].strip().lower()

                    # print(element1,element2,bonding_atoms1,bonding_atoms2)

                    ######################################
                    # if you wants C=N-R Z/E inversion to be forbiddened, activate the following if statement
                    # if ((element1=='c' and len(bonding_atoms1)==3) or (element1=='n' and len(bonding_atoms1)==2)) and \
                    #    ((element2=='c' and len(bonding_atoms2)==3) or (element2=='n' and len(bonding_atoms2)==2)):

                    ######################################
                    # if you wants C=N-R Z/E inversion to be allowed, activate the following if statement
                    if (element1 == 'c' and len(bonding_atoms1) == 3) and (element2 == 'c' and len(bonding_atoms2) == 3):
                        # for R1-C1(-R2)=C2(-R3)-R4, get vector of R1-C1, and R3-C2
                        # result for C1 and C2 should be the same

                        # 亚甲基、甲基、三氟甲基等的氢、氟容易两个互相翻转，数相同元素的数量，如果有两个无其他成键的原子（如H，卤素）就排除掉
                        # 选取某个碳上连接的所有无其他键连的元素，考虑有无重复的
                        non_bonding_atoms = [test_atom for test_atom in bonding_atoms1 if len([pair for pair in self.bonds if test_atom in pair]) == 1]
                        element_of_non_bonding_atoms = [self.coordinates.elements[test_atom] for test_atom in non_bonding_atoms]
                        if len(non_bonding_atoms) == 2 and len(set(element_of_non_bonding_atoms)) == 1:
                            continue
                        non_bonding_atoms = [test_atom for test_atom in bonding_atoms2 if len([pair for pair in self.bonds if test_atom in pair]) == 1]
                        element_of_non_bonding_atoms = [self.coordinates.elements[test_atom] for test_atom in non_bonding_atoms]
                        if len(non_bonding_atoms) == 2 and len(set(element_of_non_bonding_atoms)) == 1:
                            continue

                        atom1, atom2 = sorted([atom1, atom2])
                        bonding_atoms1 = [pair[0] if pair[0] != atom1 else pair[1] for pair in self.bonds if atom1 in pair]
                        bonding_atoms2 = [pair[0] if pair[0] != atom2 else pair[1] for pair in self.bonds if atom2 in pair]
                        R1 = min([x for x in bonding_atoms1 if x not in [atom1, atom2]])
                        R3 = min([x for x in bonding_atoms2 if x not in [atom1, atom2]])

                        # R1 - atom1 = atom2 - R3

                        R1_np = self.coordinates.coordinates_np[R1]
                        atom1_np = self.coordinates.coordinates_np[atom1]
                        R3_np = self.coordinates.coordinates_np[R3]
                        atom2_np = self.coordinates.coordinates_np[atom2]

                        a1_a2 = atom2_np - atom1_np  # a1-->a2
                        a1_R1 = R1_np - atom1_np  # a1-->R1
                        a2_R2 = R3_np - atom2_np  # a2-->R2

                        normal_vector_of_R1_a1_a2 = np.cross(a1_a2, a1_R1)
                        in_plain_normal_vector_of_double_bond = np.cross(a1_a2, normal_vector_of_R1_a1_a2)
                        projection_1 = np.dot(in_plain_normal_vector_of_double_bond, a1_R1)
                        projection_2 = np.dot(in_plain_normal_vector_of_double_bond, a2_R2)
                        projection = projection_1 * projection_2

                        # the following algorithm is wrong
                        # ------------------------------------------------------------
                        # projection = np.dot(vector1,vector2)
                        # self.ZE[atom1] = int(np.sign(projection))
                        # self.ZE[atom2] = int(np.sign(projection))
                        # ------------------------------------------------------------

                        self.ZE[atom1] = int(np.sign(projection))
                        self.ZE[atom2] = int(np.sign(projection))

        self.ZE_str = "".join(["A" if x > 0 else "B" if x < 0 else "-" for x in self.ZE])
        self.stereo_str = "".join([self.ZE_str[count] if self.ZE_str[count] != '-' else self.chirality_str[count] for count in range(len(self.ZE_str))])


def print_incorrect_chiral(std_chiral, current_chiral):
    label = []
    for i in range(int(len(std_chiral) / 10) + 1):
        if i < 10:
            label.append(" " + str(i))
        else:
            label.append(str(i))
        label.append("1234567890")

    ret = "".join(label) + "\n"
    ret += "  " + "  ".join([std_chiral[x:x + 10] for x in range(0, len(std_chiral), 10)]) + '\n'
    ret += "  " + "  ".join([current_chiral[x:x + 10] for x in range(0, len(current_chiral), 10)])

    print(ret)
    return ret


# a global parameter to prevent repeated compile of re_ret patters
std_coordinate_reg_exp_patters = []
# store the possible reg_ex patterns, each pattern should return a list:
# [symbol or No., X, Y, Z]


# matching patterns:

#  C                    -0.46615   1.1295   -1.46282 "
# H16A	2.197	5.321	-4.291 (amber)
# C19	2.197	5.321	-4.291 (amber)
# C,0,0.4732857814,-1.2321049177,-0.7321261073
# 'C,2.8527268394,0.1892117596,0.7450890036'
#  O(PDBName=O,ResName=,ResNum=1) 2.19400000   -2.92000000    0.54500000
# C 0 0.4732857814 -1.2321049177 -0.7321261073

std_coordinate_reg_exp_patters.append(r'([A-Z][a-z]{0,2})\d*[A-Za-z]{0,2}(?:\(PDBName.+\))*(?:[,\s]\d)*[,\s]+(-*\d+\.\d*)[,\s]+(-*\d+\.\d*)[,\s]+(-*\d+\.\d*)')

# ---------------------------------------------------------------------
# Center     Atomic      Atomic             Coordinates (Angstroms)
# Number     Number       Type             X           Y           Z
# ---------------------------------------------------------------------
#      1          6           0        0.420470   -1.186773   -0.704665

#                Cartesian Coordinates (Ang):
# ---------------------------------------------------------------------
# Center     Atomic                     Coordinates (Angstroms)
# Number     Number                        X           Y           Z
# ---------------------------------------------------------------------
#      1          6                    0.839826   -1.280127    0.071692

std_coordinate_reg_exp_patters.append(r'\d+\s+(\d+)\s+(?:\d+\s+)*(-*\d+\.\d*)\s+(-*\d+\.\d*)\s+(-*\d+\.\d*)')

#    8   -2.94968642    0.56722265    0.82230145
std_coordinate_reg_exp_patters.append(r"^\s*(\d+)\s+(-*\d+\.\d*)\s+(-*\d+\.\d*)\s+(-*\d+\.\d*)\s*$")

# ----------------------------
# CARTESIAN COORDINATES (A.U.)
# ----------------------------
# NO LB      ZA    FRAG    MASS        X           Y           Z
# 0 C     6.0000    0    12.011         -3.225857992764711         -4.974951500825070         -1.229933675247557

# re_patterns.append(r"\s*\d+\s+([A-Z][a-z]{0,2})\s+\d+\.\d+\s+\d+\s+\d+\.\d+\s+(-*\d+\.\d*)\s+(-*\d+\.\d*)\s+(-*\d+\.\d*)")
# 上面需要转换单位，未实现

std_coordinate_reg_exp_compiles = [re.compile(x) for x in std_coordinate_reg_exp_patters]


def std_coordinate(line, gaussian_only=False):
    """
    A input line, allowed format see below
    :return: A standardized coordinate output; if no coordinate was found, return None
    """
    global std_coordinate_reg_exp_compiles

    for re_compile in std_coordinate_reg_exp_compiles:
        re_result = re_compile.findall(line)
        if re_result:
            re_result = list(re_result[0])
            if re_result[0].isdigit() and int(re_result[0]) in elements_dict:
                re_result[0] = elements_dict[int(re_result[0])]

            # Bq 原子会显示为0号，用以下语句排除一票乱七八糟的情况
            if re_result[0].isdigit() and int(re_result[0]) not in elements_dict:
                continue

            return '\t'.join(re_result)


def std_coordinate_mopac_arc(line):
    #   F     6.84338961 +1  -1.29346408 +1   9.54649274 +1
    mopac_pattern = r"([A-Z][a-z]{0,2})\d*\s+(-*\d+\.\d*)\s+\+*\-*(1|0)\s+(-*\d+\.\d*)\s+\+*\-*(1|0)\s+(-*\d+\.\d*)\s+\+*\-*(1|0)"
    re_ret = re.findall(mopac_pattern, line)
    if re_ret:
        re_ret = list(re_ret[0])
        # 去掉mopac的默认冻结标记
        re_ret.pop(-1)
        re_ret.pop(-2)
        re_ret.pop(-3)
        return '\t'.join(re_ret)


if __name__ == '__main__':
    pass
