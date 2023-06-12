# -*- coding: utf-8 -*-
__author__ = 'LiYuanhe'

# import sys
# import pathlib
# parent_path = str(pathlib.Path(__file__).parent.resolve())
# sys.path.insert(0,parent_path)

from Python_Lib.My_Lib_PyQt6 import *

import matplotlib

matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as MpFigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as MpNavToolBar
from matplotlib import pyplot


class MpWidget_All(QWidget):
    def __init__(self, parent=None, y=None):
        super(self.__class__, self).__init__()
        self.setParent(parent)

        if y is None:
            y = []

        self.setMinimumSize(QSize(300, 200))
        self.dpi = 70

        self.fig = pyplot.figure(figsize=(1, 1), dpi=self.dpi, )

        # ax = pyplot.gca()
        # ax.set_facecolor((240/256,240/256,240/256))
        self.fig.patch.set_facecolor((240 / 256, 240 / 256, 240 / 256))
        # matplotlib.rc('xtick',labelsize=15)
        # matplotlib.rc('ytick', labelsize=15)

        self.Cycle_subplot = pyplot.subplot2grid((4, 1), (0, 0))
        self.opt_subplot = pyplot.subplot2grid((4, 1), (1, 0))
        self.Converged_subplot = pyplot.subplot2grid((4, 1), (2, 0), rowspan=2)

        self.bond_length_axis = self.opt_subplot.twinx()
        self.rmsd_axis = self.Converged_subplot.twinx()

        self.bond_length_axis, self.opt_subplot = self.opt_subplot, self.bond_length_axis

        self.marker_size = 4

        self.opt_subplot.clear()
        self.opt_subplot.plot(range(len(y)), y, 'r')
        self.Cycle_subplot.clear()
        self.Cycle_subplot.plot(range(len(y)), y, 'r')
        self.Converged_subplot.clear()
        self.Converged_subplot.plot(range(len(y)), y, 'r')

        self.fig.subplots_adjust(top=0.94, bottom=0.06, hspace=0.24, wspace=0.12, left=0.11, right=0.89)

        self.canvas = MpFigureCanvas(self.fig)
        self.canvas.setParent(self)

        self.canvas.draw()

        self.mpl_toolbar = MpNavToolBar(self.canvas, self)

        self.mpl_toolbar.setIconSize(QSize(18, 18))
        self.mpl_toolbar.layout().setSpacing(6)

        self.vLayout = QVBoxLayout()
        self.vLayout.setContentsMargins(0, 0, 0, 0)
        self.vLayout.addWidget(self.canvas)
        self.vLayout.addWidget(self.mpl_toolbar)
        self.setLayout(self.vLayout)

        self.converged_data = []
        self.cycle_energy = []
        self.last_print = []  # record the printing of bond length, prevent redundant bonding printing
        self.opt_data = []

        self.fluctuation_warned = False
        self.opt_limit = (-1, 0)
        self.setParent(parent)

    def opt_Update(self, opt_energies, atom_count=50, bond_length_list=(), show_bond_length=True):
        """

        :param opt_energies:
        :param atom_count:
        :param bond_length_list:
        :param show_bond_length:
        :return:
        """

        assert opt_energies, 'Opt Energy List is Empty'

        self.bond_length_list = bond_length_list

        printing_str = ""

        for bond in bond_length_list:
            # 最多取25个看大致趋势，不要输出太多数字
            spacing = int(len(bond) / 25) + 1
            printing_str += " ".join(["{:.2f}".format(x) for count, x in enumerate(bond) if count % spacing == 0]) + "\n"
        if printing_str != self.last_print:
            print(printing_str)
            self.last_print = printing_str

        self.bond_length_axis.clear()
        if show_bond_length:
            for bond in bond_length_list:
                self.bond_length_axis.plot(range(1, len(bond) + 1), bond, '#888888', markersize=self.marker_size)
                self.bond_length_axis.scatter(range(1, len(bond) + 1), bond, marker='o', color='#888888', s=self.marker_size)

        self.opt_energy_count = len(opt_energies)
        self.origin_opt_energy = copy.deepcopy(opt_energies)
        self.atom_count = atom_count
        self.bond_length_list = bond_length_list
        self.show_bond_length = show_bond_length
        opt_energies = [x * 2625.499 for x in opt_energies]

        # print(opt_Energy)
        # generate logarithm Y scale
        # to prevent log(0)
        presume_dist_to_converge = 0.001
        Opt_Energy_sorted = sorted(list(set(opt_energies)))
        if len(Opt_Energy_sorted) > 2:
            presume_dist_to_converge = Opt_Energy_sorted[1] - Opt_Energy_sorted[0]

        opt_energies = [math.log10(x - min(opt_energies) + presume_dist_to_converge) for x in opt_energies]

        #
        # # 0.001 to prevent log(0)
        # opt_Energy = [math.log10(x-min(opt_Energy)+0.001)+3 for x in opt_Energy]
        # # remove last point to prevent off-scale low at the beginning phase of optimization
        # if len(opt_Energy)>1:
        #     opt_Energy[-1] = opt_Energy[-2]

        # print(opt_Energy)

        self.opt_subplot.clear()
        self.opt_subplot.plot(range(1, len(opt_energies) + 1), opt_energies, 'r')
        self.opt_subplot.plot(range(1, len(opt_energies) + 1), opt_energies, 'bo', markersize=self.marker_size)

        self.max = max(opt_energies)
        self.min = min(opt_energies)

        self.opt_data = copy.deepcopy(opt_energies)

        if opt_energies:
            self.opt_limit = find_approate_y_limit(opt_energies, origin_data=self.origin_opt_energy, atom_count=atom_count)
        else:
            self.opt_limit = (-1, 0)

        if (len(self.opt_limit) > 2):
            self.opt_subplot.plot(opt_energies.index(min(opt_energies)) + 1, min(opt_energies), 'o', color='#FFA400', markersize=self.marker_size)

            if self.opt_limit[2] == " Energy Fluctuation! ":
                self.opt_subplot.text(0.5, 0.95, self.opt_limit[2], horizontalalignment='center', verticalalignment='top',
                                      fontsize=10, transform=self.opt_subplot.transAxes,
                                      bbox=dict(facecolor='red', alpha=0.5))
                self.opt_subplot.plot((0, len(opt_energies) + 2), (self.opt_limit[3], self.opt_limit[3]), 'g--')

            elif self.opt_limit[2] == "Possible Energy Fluctuation.":
                self.opt_subplot.plot((0, len(opt_energies) + 2), (self.opt_limit[3], self.opt_limit[3]), 'g--')

            elif "Global Minimum" in self.opt_limit[2]:
                self.opt_subplot.text(0.50, 0.95, self.opt_limit[2], horizontalalignment='center', verticalalignment='top',
                                      fontsize=10, transform=self.opt_subplot.transAxes,
                                      bbox=dict(facecolor='yellow', alpha=0.5))

        self.opt_subplot.set_ylim(*self.opt_limit)
        # self.opt_subplot.set_xlim(0, len(opt_Energy) + 2)

        if len(opt_energies) > 50:
            self.opt_subplot.set_xlim(len(opt_energies) - 50, len(opt_energies) + 2)
        else:
            self.opt_subplot.set_xlim(0, len(opt_energies) + 2)

        if self.bond_length_list:
            self.max_bond_length = max(sum(self.bond_length_list, []))
            self.min_bond_length = min(sum(self.bond_length_list, []))
            self.delta_bond_length = self.max_bond_length - self.min_bond_length
            self.delta_bond_length = max(self.delta_bond_length, 0.1)  # 防止纵坐标宽度为0
            self.bond_length_axis.set_ylim(self.min_bond_length - self.delta_bond_length * 0.2, self.max_bond_length + self.delta_bond_length * 0.5)

        self.canvas.draw()

    def opt_zoom_out(self):
        if self.opt_data:
            self.delta = self.max - self.min
            self.opt_subplot.set_ylim(self.min - self.delta * 0.2, self.max + self.delta * 0.5)
            self.opt_subplot.set_xlim(0, len(self.opt_data) + 2)
            if self.bond_length_list:
                self.max_bond_length = max(sum(self.bond_length_list, []))
                self.min_bond_length = min(sum(self.bond_length_list, []))
                self.delta_bond_length = self.max_bond_length - self.min_bond_length
                self.bond_length_axis.set_ylim(self.min_bond_length - self.delta_bond_length * 0.2, self.max_bond_length + self.delta_bond_length * 0.5)

            self.canvas.draw()

    def opt_zoom_back(self):
        if hasattr(self, "origin_opt_energy") and hasattr(self, "atom_count") and hasattr(self, "bond_length_list") and hasattr(self, "show_bond_length"):
            self.opt_Update(self.origin_opt_energy, self.atom_count, self.bond_length_list, self.show_bond_length)

    def Cycle_Update(self, cycle_energies=()):

        cycle_energies = [x * 2625.499 for x in cycle_energies]

        # generate logarithm Y scale
        # to prevent log(0)
        presume_dist_to_converge = 1E-7
        Cycle_Energy_sorted = sorted(list(set(cycle_energies)))
        if len(Cycle_Energy_sorted) > 2:
            presume_dist_to_converge = Cycle_Energy_sorted[1] - Cycle_Energy_sorted[0]

        cycle_energies = [math.log10(x - min(cycle_energies) + presume_dist_to_converge) for x in cycle_energies]
        # # remove last point to prevent off-scale low at the beginning phase of optimization
        # if len(Cycle_Energy)>1:
        #     Cycle_Energy[-1] = Cycle_Energy[-2]

        self.cycle_energy = cycle_energies

        self.Cycle_subplot.clear()
        X = range(1, len(cycle_energies) + 1)
        Y = cycle_energies

        self.Cycle_subplot.plot(X, Y, 'r')
        self.Cycle_subplot.plot(X, Y, 'bo', markersize=5)

        self.cycle_max = max(cycle_energies)
        self.cycle_min = min(cycle_energies)

        try:
            self.Cycle_limit = find_scf_process_y_limit(cycle_energies)
        except Exception:
            self.cycle_delta = self.cycle_max - self.cycle_min
            self.Cycle_limit = [self.cycle_min - self.cycle_delta * 0.2, self.cycle_max + self.cycle_delta * 0.2, len(self.cycle_energy) + 1]

        self.length = len(cycle_energies)

        self.Cycle_subplot.set_ylim(*self.Cycle_limit[:2])

        range_min = self.Cycle_limit[2]
        range_max = self.Cycle_limit[2] + int((self.length - self.Cycle_limit[2]) * 1.1) + 1
        if range_max - range_min >= 6:
            self.Cycle_subplot.set_xlim(range_min, range_max)
        else:
            self.Cycle_subplot.set_xlim(max(0, len(cycle_energies) - 6), len(cycle_energies) + 1)

        self.canvas.draw()

    def cycle_zoom_out(self):
        if self.cycle_energy:
            self.cycle_delta = self.cycle_max - self.cycle_min
            self.Cycle_subplot.set_ylim(self.cycle_min - self.cycle_delta * 0.2, self.cycle_max + self.cycle_delta * 0.2)
            self.Cycle_subplot.set_xlim(0, len(self.cycle_energy) + 1)
            self.canvas.draw()

    def cycle_zoom_back(self):
        if hasattr(self, "cycle_energy") and hasattr(self, "Cycle_limit"):
            if self.cycle_energy:
                self.Cycle_subplot.set_ylim(*self.Cycle_limit[:2])

                range_min = self.Cycle_limit[2]
                range_max = self.Cycle_limit[2] + int((self.length - self.Cycle_limit[2]) * 1.1) + 1
                if range_max - range_min >= 6:
                    self.Cycle_subplot.set_xlim(range_min, range_max)
                else:
                    self.Cycle_subplot.set_xlim(max(0, len(self.cycle_energy) - 6), len(self.cycle_energy) + 1)

                self.canvas.draw()

    def Converged_Update(self, data=(), geometries=()):

        import pathlib
        Lib_path = str(pathlib.Path(__file__).parent.resolve())
        sys.path.append(Lib_path)
        from RMSD_by_cartesian import generate_rmsd_list

        self.original_converged_data = copy.deepcopy(data)
        self.rmsd_geometries = copy.deepcopy(geometries)

        self.converged_data = data
        self.converged_data_backup = copy.deepcopy(data)

        self.converged_max = max([max(i) for i in data])
        self.converged_min = min([min(i) for i in data])
        self.converged_count = len(data)

        self.rmsd_axis.clear()
        self.rmsd = []
        if geometries:
            self.rmsd = generate_rmsd_list(geometries[-1], geometries[:-1], print_percentage=False)

        self.Converged_subplot.clear()
        self.Converged_subplot.plot((0, len(data) + 2), (1, 1), 'g--')

        # (set, i, num) set: which criteria, i: which step, num: value
        Data_tuple = [(criteria, i, num) for i, this_list in enumerate(data) for criteria, num in enumerate(this_list)]
        Data_Converged = ([i + 1 for criteria, i, num in Data_tuple if num <= 1], [num for criteria, i, num in Data_tuple if num <= 1])
        Data_Not_Converged = [(criteria, i + 1, num) for criteria, i, num in Data_tuple if num > 1]

        color = ['#FFA400', 'b', 'r', 'm', '#888888']
        label = ["Max F", "RMS F", "Max D", "RMS D", 'Energy']

        for criteria in range(len(data[0])):
            data_this_set = [x[criteria] for x in data]
            self.Converged_subplot.plot(range(1, len(data) + 1), data_this_set, color=color[criteria], label=label[criteria])

            plot_x = [item[1] for item in Data_Not_Converged if item[0] == criteria]
            plot_y = [item[2] for item in Data_Not_Converged if item[0] == criteria]
            if len(data[0]) == 4:
                self.Converged_subplot.plot(plot_x, plot_y, 'o', color=color[criteria], markersize=self.marker_size)
            elif len(data[0]) == 5:
                self.Converged_subplot.scatter(plot_x, plot_y, marker='o', color=color[criteria], s=self.marker_size)

        if self.rmsd:
            self.rmsd_axis.plot(range(1, len(self.rmsd) + 1), self.rmsd, color='#00aaaa', label='RMSD')
            # self.rmsd_axis.set_ylim(-0.005, max(max(self.rmsd[-50:]) + (max(self.rmsd[-50:])-min(self.rmsd[-50:]))*3,0.5))
            self.rmsd_axis.set_ylim(-0.005, 1.2)

        if self.converged_count > 50:
            self.Converged_subplot.set_xlim(len(data) - 50, len(data) + 2)
        else:
            self.Converged_subplot.set_xlim(0, len(data) + 2)

        self.upperLimit = max([max(x[-30:]) for x in data])

        self.Converged_subplot.set_ylim(10 ** (-2), self.upperLimit * 10)
        self.Converged_subplot.set_yscale('log')
        # self.Converged_subplot.legend(loc='upper left',bbox_to_anchor=(0.02,0.98))
        if len(data[0]) == 4:
            self.Converged_subplot.legend(borderaxespad=0., bbox_to_anchor=(0., 0.98), loc='upper left', ncol=2)
        elif len(data[0]) == 5:
            self.Converged_subplot.legend(borderaxespad=0., bbox_to_anchor=(0., 0.98), loc='upper left', ncol=3)

        if len(data[0]) == 4:
            self.Converged_subplot.plot(Data_Converged[0], Data_Converged[1], 'o', color='#00D600', markersize=self.marker_size)
        elif len(data[0]) == 5:
            self.Converged_subplot.scatter(Data_Converged[0], Data_Converged[1], marker='o', color='#00D600', s=self.marker_size)

        self.canvas.draw()

    def converged_zoom_out(self):
        if self.converged_data:
            self.converged_delta = self.converged_max / self.converged_min
            self.Converged_subplot.set_ylim(min(self.converged_min / self.converged_delta ** 0.2, 10 ** (-2)), self.converged_max * self.converged_delta ** 0.2)
            self.Converged_subplot.set_xlim(0, self.converged_count + 1)
            self.canvas.draw()

        self.rmsd_axis.set_ylim(-0.005, 1.2)
        # if hasattr(self,"rmsd") and self.rmsd:
        # self.rmsd_axis.set_ylim(-0.005, max(max(self.rmsd) + (max(self.rmsd)-min(self.rmsd))*3,0.5))

    def converged_zoom_back(self):
        if hasattr(self, "converged_data") and hasattr(self, "rmsd_geometries"):
            self.Converged_Update(self.converged_data, self.rmsd_geometries)
        # if self.converged_data:
        #     self.Converged_subplot.set_ylim(10**(-2),self.upperLimit*10**0.2)
        #     if self.converged_count>50:
        #         self.Converged_subplot.set_xlim(self.converged_count -50, self.converged_count + 2)
        #     else:
        #         self.Converged_subplot.set_xlim(0, self.converged_count + 2)
        #     self.canvas.draw()


def find_scf_process_y_limit(energies: list):
    # input a list of energy, give the appropriate y limit,
    #  to show reasonable amount of point, but also reasonable resolution
    # example: -2130.1126, -2140.287717, -1685.757423, -2081.089339, -2093.857316, -2111.060361,
    #          -2161.96741, ... , -2177.487028, -2177.487284, -2177.487504, -2177.487689, -2177.487812,
    #          -2177.48801, -2177.488204, -2177.488437,
    # give something like [-2177.49, -2177.48]

    # the last point must be insight

    # return a three-tuple: [y-limit_min, y-limit_max, x_limit_min]

    if len(energies) <= 2:
        dist = abs(energies[-1] - energies[0])
        return [min(energies) - dist * 1.3 - 0.01, max(energies) + dist * 1.3 + 0.01, 0]

    # 从最后一个元素依次前数，所需区间有多大
    pos_interval = [(min(energies[-x:]), max(energies[-x:])) for x in range(2, len(energies) + 1)]
    pos_interval = [(x[0] - (x[1] - x[0]) * 0.3, x[1] + (x[1] - x[0]) * 0.3) for x in pos_interval]  # 扩大30%

    # 区间内有哪些元素
    interval_element = [[x for x in energies if interval[0] <= x <= interval[1]]
                        for interval in pos_interval]  # 能显示多少个值
    interval_element = [sorted(x) for x in interval_element]

    # 分辨率
    interval_resolution = []
    for interval in interval_element:

        if interval[-1] == interval[0]:
            interval_resolution.append(0)
        else:
            ret = [(interval[x + 1] - interval[x]) / (interval[-1] - interval[0]) for x in range(len(interval) - 1)]
            ret = sum([x ** (-2) for x in ret]) / len(ret)  # 取二次倒数平均，以去除特别大的interval的影响
            interval_resolution.append(ret ** (-1 / 2))

    score = []
    for count in range(len(interval_element)):
        # 平均分辨率乘以元素个数，即，如果是线性的曲线，可以全部显示
        # 在分辨率上给了0.9次方，稍微倾向于数量
        score.append((len(interval_element[count])) ** 1.3 * (interval_resolution[count]))

    # 认定区间只包含两个元素的情况无效，认定区间不包含最低点的情况无效
    for count, interval_element_content in enumerate(interval_element):
        if len(interval_element_content) == 2:
            score[count] = 0
        if min(energies) not in interval_element_content:
            score[count] = 0

    # for i in score:
    #     print(i)

    for count in range(len(interval_element) - 1, -1, -1):
        if score[count] > [x for x in score if x][0] * 0.1:  # 把前面的零值去掉
            ret_index = count
            break
    else:
        ret_index = score.index(max(score))

    high = interval_element[ret_index][-1]
    low = interval_element[ret_index][0]
    dist = high - low
    ret = [low - dist * 0.2, high + dist * 0.2]

    x_min = 0
    for i in range(len(energies)):
        if ret[0] <= energies[i] <= ret[1]:
            x_min = i
            break

    return ret + [x_min]


def find_approate_y_limit(data=None, origin_data=None, threshold=6, checkMin=True, atom_count=-1):
    if data is None:
        data = []
    if not origin_data:
        origin_data = data

    if len(data) == 1:
        return (data[0] - 0.01, data[0] + 0.01)
    else:
        fluc_determine_result = fluctuation_determine(data, atom_count=atom_count)
        if checkMin:
            maxData = max(data[data.index(min(data)):])
            DataInterval = maxData - min(data)

            if fluc_determine_result[0] == "Definitive Fluctuation.":
                return (min(data) - DataInterval * 0.1, maxData + DataInterval * 1.5, " Energy Fluctuation! ", fluc_determine_result[1])
            if min(data) != data[-1] and (origin_data[-1] - min(origin_data)) * 2625.499 > 0.01:
                dis_to_global_minimum = (origin_data[-1] - min(origin_data)) * 2625.499

                delta = [abs(data[-1] - num) for num in data]
                delta.sort()
                delta = [x for x in delta if x != 0]

                data_span = max(data) - min(data)
                if len(delta) <= threshold:
                    if dis_to_global_minimum > 0.01:
                        dis_to_global_minimum = "{0:.2f}".format(dis_to_global_minimum)
                        return (min(data) - data_span * 0.3, min(data) + data_span * 1.5, " Global Minimum is " + dis_to_global_minimum + " kJ/mol lower! ")
                    else:
                        return (min(data) - data_span * 0.3, min(data) + data_span * 1.5, "hahaha")
                else:
                    if dis_to_global_minimum > 0.01:
                        dis_to_global_minimum = "{0:.2f}".format(dis_to_global_minimum)
                        return (min(data) - DataInterval * 0.3, maxData + min(DataInterval * 10, data_span * 1.5),
                                " Global Minimum is " + dis_to_global_minimum + " kJ/mol lower! ")
                    else:
                        return (min(data) - DataInterval * 0.3, maxData + min(DataInterval * 10, data_span * 1.5), "hahaha")
            if fluc_determine_result[0] == "Possible Fluctuation.":
                return (min(data) - DataInterval * 0.1, maxData + DataInterval * 1.5, "Possible Energy Fluctuation.", fluc_determine_result[1])

        delta = [abs(data[-1] - num) for num in data]
        delta.sort()
        delta = [x for x in delta if x != 0]
        data_span = max(data) - min(data)
        if len(delta) > threshold:
            return (min(data) - delta[threshold - 1] * 0.3, min(data) + min(delta[threshold - 1] * 10, data_span * 1.5))

        # 少于threshold个数据
        data_span = max(data) - min(data)
        return (min(data) - data_span * 0.3, min(data) + data_span * 1.5)

        # matrix = [(len(data)-1, i, abs(data[-1] - num)) for i, num in enumerate(data)]
        # matrix.sort(key=lambda x: x[2])
        # matrix = [x for x in matrix if x!=0]
        # if len(matrix) > threshold:
        #     return (min(data) - matrix[threshold][2] * 0.3, min(data) + matrix[threshold][2] * 5)
        # else:
        #     return (min(data) - matrix[-1][2] * 0.3, min(data) + matrix[-1][2] * 5)


if __name__ == '__main__':
    pass
