__author__ = 'LiYuanhe'

# -*- coding: utf-8 -*-
import os
import pathlib
import sys

parent_path = str(pathlib.Path(__file__).parent.resolve())
sys.path.append(parent_path)

from Python_Lib.My_Lib_PyQt6 import *
from Lib_Coordinates import *
from Lib_CP2K import *
from Lib_Gaussian import *
from Lib_GUI import *
from Lib_MOPAC import *
from Lib_ORCA import *
from Lib_xTB import *
import numpy as np

fluctuation_message = ""  # 用于记录震荡的提示，重复的不要输出
opt_flucturation_threshold_shown = False


class Date_Class:
    def __init__(self, link='', datetime_str='', cycle=0, energy=0):
        self.link = link
        self.cycle = cycle
        self.energy = energy

        try:
            self.datetime = datetime.strptime(datetime_str, "%a %b %d %H:%M:%S %Y")
        except Exception:
            pass


def count_pass_through(data, threshold):
    ret = 0
    for count in range(len(data) - 1):
        if (data[count] - threshold) * (data[count + 1] - threshold) < 0:
            ret += 1
    return ret


def unify_basis(input_str: str):
    """
    Unify multiple writing of the same basis, like 6-31G(d,p) and 6-31G*, def-TZVP and TZVP
    :param input_str:
    :return:
    """
    if not isinstance(input_str, str):
        print(input_str)
    input_str = input_str.lower()
    if input_str.endswith("(d,p)"):
        input_str = input_str.replace("(d,p)", '**')
    elif input_str.endswith("(d)"):
        input_str = input_str.replace("(d)", '*')
    elif input_str.startswith('def2-'):
        input_str = input_str.replace('def2-', 'def2')
    elif input_str.startswith('def-'):
        input_str = input_str.replace('def-', '')
    if input_str.startswith('sv(p)'):
        input_str = input_str.replace('sv(p)', 'sv')
    return input_str


def unify_method(input_str: str):
    input_str = input_str.lower()
    input_str = input_str.replace('pbe1pbe', 'pbe0')
    input_str = input_str.replace('pbepbe', 'pbe')
    input_str = ''.join([x for x in input_str if 'a' <= x <= 'z' or "0" <= x <= '9'])
    if input_str.startswith('u') or input_str.startswith('r'):  # 去掉开壳层闭壳层标记
        input_str = input_str[1:]
    return input_str


def load_factor_database(filename="校正因子.xlsx"):
    import pyexcel
    scaling_factor_database = pyexcel.get_records(file_name=filename)
    for line in scaling_factor_database:
        # 储存一个原始的，一个最后的
        line['Basis'] = [line['Basis'], unify_basis(line['Basis'])]
        line['Method'] = [line['Method'], unify_method(line['Method'])]

    return scaling_factor_database


def fluctuation_determine(data=None, atom_count=-1, silent=False):
    """

    Args:
        data:
        atom_count: 对较大的分子，应增加许可的循环数量
        silent:

    Returns:

    """
    global fluctuation_message
    global opt_flucturation_threshold_shown
    if data is None:
        data = []

    # 曲线最小值为第n值，取集合data[n:]的min，max
    # 对任意min,max能量间的阈值，计算折线穿越阈值的次数，超过一定次数报震荡

    # 对data[n:]排序，相邻数区间内的穿越次数是相同的，遍历取最大即可。
    if not data:
        return ("", 0)
    min_index = data.index(min(data))
    test_sub_list = data[min_index:]
    test_sub_list.sort()
    thresholds = [(test_sub_list[i] + test_sub_list[i + 1]) / 2 for i in range(len(test_sub_list) - 1)] + [data[-1]]

    throughs = [count_pass_through(data, x) for x in thresholds]

    max_through = max(throughs)
    max_through_threshold = thresholds[throughs.index(max(throughs))]

    # print(max_through)

    threshold = atom_count / 3 if atom_count > 50 else 16
    if not opt_flucturation_threshold_shown:
        if not silent:
            print("Using fluctuation threshold", threshold)
        opt_flucturation_threshold_shown = True
    if max_through > threshold:  # 16 and 1/3 is an arbitrary sensitivity control number
        new_fluctuation_message = get_print_str("Fluctuation detected! Max fluctuation count:", max_through, " Threshold:", max_through_threshold)
        if new_fluctuation_message != fluctuation_message:
            if not silent:
                print("Fluctuation detected! Max fluctuation count:", max_through, " Threshold:", max_through_threshold)
            fluctuation_message = new_fluctuation_message
        return ("Definitive Fluctuation.", max_through_threshold)
    elif max_through > threshold / 2:
        new_fluctuation_message = get_print_str("Possible Fluctuation! Max fluctuation count:", max_through, " Threshold:", max_through_threshold)
        if new_fluctuation_message != fluctuation_message:
            if not silent:
                print("Possible Fluctuation! Max fluctuation count:", max_through, " Threshold:", max_through_threshold)
            fluctuation_message = new_fluctuation_message
        return ("Possible Fluctuation.", max_through_threshold)
    else:
        return ("", max_through_threshold)


def read_comp_config():
    """
    read computer configurations from Comp_configs.txt
    :return:a list of dict, each dict contains the information like system, path, etc.
    """

    with open('Comp_configs.txt') as file:
        file = file.readlines()
    file = [x.strip() for x in file][2:]  # 删掉说明行
    file = split_list_by_item(file, "")

    ret = []

    for computer in file:
        temp = collections.OrderedDict()
        temp['title'] = computer[0]
        temp["system"] = computer[1].lstrip("system=")
        temp['path'] = computer[2].lstrip("path=")
        temp['mem'] = float(computer[3].lstrip("mem="))
        temp['proc'] = int(computer[4].lstrip("proc="))

        ret.append(temp)

    return ret


class MECP_output:
    # only one step orca was supported
    def __init__(self, output):
        if isinstance(output, str) and file_type(output) == Filetype.MECP_output_folder:
            report_file_path = os.path.join(os.path.realpath(output), 'ReportFile')
            with open(report_file_path) as file:
                self.lines = file.readlines()

        self.normal_termination = False

        self.is_optimization = True
        self.opt_energies = []
        self.converged = [[], [], [], [], []]
        self.opt_coordinates = []

        self.coordinates = []
        self.electronic_energy = 0

        self.charge = 999
        self.multiplicity = 999

        self.coords = []  # list of Coordinate Class Object
        self.get_coords()

        # self.keywords = []
        # self.level = []
        # self.get_keywords()

        self.geom_steps = []  # contain list of [list of lines] <-- each step of optimization

        self.geom_steps = split_list(self.lines, lambda x: "Geometry at Step" in x, include_separator=True)[1:]

        self.get_opt_energies()
        self.get_opt_coords()
        self.get_converged()

        self.process()

        # self.level_str = '/'.join(self.level)

    def get_opt_coords(self):
        re_pattern1 = "Geometry at Step"
        re_pattern2 = "Initial Geometry"
        for step_content in self.geom_steps:
            for count, line in enumerate(step_content):
                if re_pattern1 in line or re_pattern2 in line:
                    coordinate_lines = []
                    for line2 in step_content[count + 1]:
                        if std_coordinate(line2):
                            coordinate_lines.append(line2)
                        else:
                            break
                    self.opt_coordinates.append(Coordinates(coordinate_lines))
                    break

    def get_opt_energies(self):

        re_pattern = r"Difference in E\:\s+(-*[0-9]+\.[0-9]+)"
        for step_content in self.geom_steps:
            for line in reversed(step_content):
                re_ret = re.findall(re_pattern, line)
                if re_ret:
                    self.opt_energies.append(''.join(re_ret[0]))
                    break

        self.opt_energies = [float(x) for x in self.opt_energies]

    def get_converged(self):
        for step_count, step_content in enumerate(self.geom_steps):
            for count, line in enumerate(step_content):
                if "Convergence Check" in line:

                    for k, line2 in enumerate(step_content[count + 1:count + 6]):
                        re_ret = re.findall(r"-*\d\.\d+", line2)
                        if len(re_ret) == 2:
                            value = abs(float(re_ret[0])) / float(re_ret[1])
                            # print(value)
                            if value < 0:
                                value = -value
                            if value < 0.01:
                                value = 0.01  # 防止log时出现负无穷
                            self.converged[k].append(value)

                    break

        # 调整顺序为
        # ["Max F","RMS F","Max D","RMS D",'Energy']

        self.converged = self.converged[:4] + [[x ** 0.5 for x in self.converged[4]]]

        # 从[[...],[...],[...],[...]] 换成 [[ , , , ]...]
        self.converged = [[self.converged[x][step] for x in range(5)] for step in range(len(self.converged[0]))]

    def process(self):
        for count, line in enumerate(self.lines):
            if "The MECP Optimization has CONVERGED" in line:
                self.normal_termination = True
                energies_for_first_state = []
                for energy_lines in self.lines:
                    re_ret = re.findall(r"Energy of First State\:\s+(-*[0-9]+\.[0-9]+)", energy_lines)
                    if re_ret:
                        energies_for_first_state.append(''.join(re_ret[0]))
                #                       print(energies_for_first_state)
                energies_for_first_state = [float(x) * Hartree__KJ_mol for x in energies_for_first_state]
                self.electronic_energy = energies_for_first_state[-1]

    #                print(self.electronic_energy/Hartree__KJ_mol)

    # def get_keywords(self):
    #     for line in self.input_file_lines:
    #         if line.strip().startswith('!'):
    #             self.keywords+=line.strip().strip('!').split()
    #     self.keywords = [x.lower() for x in self.keywords]
    #     self.method = []
    #     self.basis = []
    #     for keyword in self.keywords:
    #         for functional in functional_keywords_of_orca:
    #             if keyword.lower()==functional.lower() or 'ri-'+keyword.lower()==functional.lower():
    #                 self.method.append(functional)
    #         for basis in basis_set_keywords_of_orca:
    #             if keyword.lower()==basis.lower():
    #                 self.basis.append(basis)
    #     self.method = [x if not x.lower().startswith('ri-') else x[3:] for x in self.method]
    #     self.method = list(set(self.method))
    #     self.basis = list(set(self.basis))
    #
    #     self.level = self.method+self.basis

    # def read_charge_and_multiplet(self):
    #     # acquire changes
    #     for count,line in enumerate(self.lines):
    #         charge_re_result =re.findall(r'''Total Charge +Charge +.... +(\d)+''',line) # match " Total Charge           Charge          ....    0"
    #         multiplet_re_result = re.findall(r'''Multiplicity +Mult +.... +(\d)+''',line) # match "Multiplicity           Mult            ....    1"
    #         input_re_result = re.findall(r'''\* +xyz \+(\d+) +(\d+)''',line) # match "* xyz 0   1"
    #
    #         if len(charge_re_result)==1:
    #             self.charge = int(charge_re_result[0])
    #         elif len(multiplet_re_result)==1:
    #             self.multiplicity = int(multiplet_re_result[0])
    #         elif len(input_re_result)==1:
    #             self.charge,self.multiplicity = input_re_result[0]
    #             self.charge = int(self.charge)
    #             self.multiplicity = int(self.multiplicity)

    def get_coords(self):
        marks = {r"Geometry at Step": 1, r"Initial Geometry": 1}  # ,r"CARTESIAN COORDINATES \(A\.U\.\)":3 需要调单位，暂未实现
        # see the discription in the Gaussian version of this function
        # Numbers are the value till the coordinates starts (coordinate start from the next line is 1)

        for count, line in enumerate(self.lines):
            for mark in marks:
                if re.findall(mark, line):

                    coords = []

                    for coord_line in self.lines[count + marks[mark]:]:
                        if std_coordinate(coord_line):  # 确认这一行中存在坐标
                            coords.append(coord_line)
                        else:
                            break
                    if coords:
                        self.coords.append(Coordinates(coords, self.charge, self.multiplicity))

        if self.coords:
            self.coordinates = self.coords[-1]
        else:
            self.coordinates = Coordinates()


def file_type(filename):
    if os.path.isdir(filename):
        files = list(os.listdir(filename))
        if "ReportFile" in files:
            return Filetype.MECP_output_folder
    if filename_class(filename).append.lower() in ['gjf', 'com']:
        return Filetype.gaussian_input

    if filename_class(filename).append.lower() == 'log':
        return Filetype.gaussian_output

    if filename_class(filename).append.lower() == 'inp':
        return Filetype.orca_input

    if filename_class(filename).append.lower() == 'orca':
        return Filetype.orca_output

    if filename_class(filename).append.lower() in ['mopac', 'arc']:
        return Filetype.mopac_output

    if filename_class(filename).append.lower() == 'out':
        # fast determine required for MOPAC files
        with open(filename, encoding='utf-8', errors='ignore') as file:
            for count, line in enumerate(file):
                if count > 20:
                    break
                if "**                                MOPAC2012                                  **" in line:
                    return Filetype.mopac_output
                if "**                                MOPAC2016                                  **" in line:
                    return Filetype.mopac_output

        with open(filename, encoding='utf-8', errors='ignore') as file:
            for line in file:
                line = line.strip().lower()
                # remove filename lines like %rwf, %chk, %base to prevent "!" or "#" appear in filename
                if True in [line.startswith(key) for key in ['%rwf', "%chk", '%base', "%oldchk"]]:
                    continue
                if line.startswith('Entering Gaussian System'.lower()):
                    return Filetype.gaussian_output
                if line.startswith("Gaussian 09, Revision ".lower()):
                    return Filetype.gaussian_output
                if line.startswith("* O   R   C   A *".lower()):
                    return Filetype.orca_output
                if line.startswith('#'):
                    return Filetype.gaussian_output

    # MECP 输出，形如下面的一个单几何结构文件
    #   8    0.66744144    2.46069271   -0.31465362
    #   6   -0.37688619    1.56742458    0.03329066#
    if os.path.isfile(filename):
        with open(filename, encoding='utf-8', errors='ignore') as file_content:
            file_content = file_content.readlines()
            if len(file_content) < 10000:
                file_content = remove_blank([x.strip() for x in file_content])
                if all([re.findall(r"^\s*(\d+)\s+(-*\d+\.\d*)\s+(-*\d+\.\d*)\s+(-*\d+\.\d*)\s*$", line) for line in file_content]):
                    return Filetype.MECP_output

    # if filename_class(filename).append.lower() == 'out':
    #     with open(filename,encoding='utf-8',errors='ignore') as file:
    #         for count,line in enumerate(file):
    #             line = line.strip().lower()
    #             #remove filename lines like %rwf, %chk, %base to prevent "!" or "#" appear in filename
    #             if True in [line.startswith(key) for key in ['%rwf',"%chk",'%base',"%oldchk"]]:
    #                 continue
    #             if line.startswith('Entering Gaussian System'.lower()):
    #                 return Filetype.gaussian_output
    #             if line.startswith("Gaussian 09, Revision ".lower()):
    #                 return Filetype.gaussian_output
    #             if line.startswith("* O   R   C   A *".lower()):
    #                 return Filetype.orca_output
    #             if line.startswith('#'):
    #                 return Filetype.gaussian_output
    #             if "**                                MOPAC2012                                  **".lower() in line:
    #                 return Filetype.mopac_output
    #             if "**                                MOPAC2016                                  **".lower() in line:
    #                 return Filetype.mopac_output


class Filetype:
    gaussian_input = "Gaussian Input *##*(@#"
    orca_input = "ORCA INPUT *##*(@#"
    gaussian_output = "Gaussian Output *##*(@#"
    orca_output = "ORCA Output *##*(@#"
    mopac_input = 'MOPAC INPUT *##*(@#'
    mopac_output = 'MOPAC Output *##*(@#'
    MECP_output = "MECP Output %#&*(^%&#"
    MECP_output_folder = "MECP Output Folder %#&agasdgsd*(^%&#"
    xTB_coordinate_indicator = 'xTB_coordinate_indicator#$*)@($&@)(*%^)@('
    input = [gaussian_input, orca_input]
    output = [gaussian_output, orca_output]
    valid = input + output


class XYZ_file:
    def __init__(self, path, last_only=False, end_condition=None, equal_atom_count=False, terminal_countdown=100):
        """
        Read an standard xyz file, give the components
        :param path:
        :param equal_atom_count: 目前不支持原子数不等的XYZ, 默认认为原子数不等，会耗时多；如果确认文件中原子数都相等，可以快很多
        :param terminal_countdown: 达到end_condition 之后，再接受多少个结构，防止轨迹突然中止
        """

        self.filename = path
        self.coordinates = []
        self.titles = []
        self.energies = []  # you need to call the method to extract the energy

        if last_only:
            atom_count = int(open(self.filename).readline().strip())
            input_file_lines = read_last_n_lines_fast(self.filename, atom_count + 2).splitlines()
            self.titles.append(input_file_lines[1])
            self.coordinates.append(Coordinates(input_file_lines[2:], is_xtb=(self.filename.endswith("xtbscan.traj.xyz") or
                                                                              self.filename.endswith("xtbopt_traj.xyz") or
                                                                              self.filename.endswith("xtbopt_final.xyz"))))
        else:
            with open(self.filename) as input_file_lines:
                input_file_lines = input_file_lines.readlines()

            countdown_now = -1
            lines_processed = -1
            for count, line in enumerate(input_file_lines):
                if countdown_now == 0:
                    break
                if count >= lines_processed:
                    self.atom_count = int(line)
                    self.titles.append(input_file_lines[count + 1])
                    current_coordinate = Coordinates(input_file_lines[count + 2:count + 2 + self.atom_count], is_xtb=self.filename.endswith(".xtbopt_traj.xyz"))
                    self.coordinates.append(current_coordinate)
                    lines_processed = count + self.atom_count + 2
                    if end_condition:
                        if end_condition(current_coordinate) and countdown_now == -1:
                            countdown_now = terminal_countdown
                    if countdown_now != -1:
                        countdown_now -= 1

        if self.coordinates:
            self.last_coordinate = self.coordinates[-1]
        else:
            self.last_coordinate = None

    def read_energies(self):
        """
        Read back energies given in the title from a ConfSearch extract
        Example:
            G01_M001_-638159.00
            G02_M001_7.31
            G03_M001_11.26
        """

        for title in self.titles:
            re_ret = re.findall(r"G\d+_M001_(-*\d+\.\d+)", title)
            assert len(re_ret) == 1
            self.energies.append(float(re_ret[0]))

        self.energies = [(x if count == 0 else x + self.energies[0]) for count, x in enumerate(self.energies)]

        assert len(self.energies) == len(self.coordinates)

    def write(self):
        ret = ""
        assert len(self.titles) == len(self.coordinates)
        for count, title in enumerate(self.titles):
            coordinate = self.coordinates[count]
            ret += str(self.atom_count) + '\n'
            ret += title
            ret += str(coordinate) + '\n'
        return ret

    def gjf_file_for_last(self):
        return self.coordinates[-1].gjf_file(filename=self.filename + '.gjf')


if __name__ == "__main__":
    pass
