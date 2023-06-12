__author__ = 'LiYuanhe'

# -*- coding: utf-8 -*-
import sys
import pathlib

parent_path = str(pathlib.Path(__file__).parent.resolve())
sys.path.append(parent_path)

from Python_Lib.My_Lib_Stock import *
from Lib_Constants import *
from Lib_Coordinates import *


CP2K_Input_Node_type = TypeVar("CP2K_Input_Node_type", bound="CP2K_Input_Node")


class CP2K_Input_Node:
    def __init__(self, parent: Optional[CP2K_Input_Node_type], name: str, value: Optional[str] = None):
        """
        Tree data structure
        The root node has parent = None
        The child nodes are CP2K_Input_Node objects
        The child names can be duplicate
        If a child is access via class_instance.child_name, the last added one is returned

        Args:
            parent: The parent tree node object
            name: The name of the current node, parent.name = self
            value:
        """
        self.name = name
        self.parent: CP2K_Input_Node_type = parent
        self.ancestors: Sequence[CP2K_Input_Node_type] = []  # list of ancestor, the first one is the root, the last one is the parent
        self.value = value  # section parameter
        self.children_names: Sequence[str] = []
        self.children_objects: Sequence[CP2K_Input_Node_type] = []

        # the top tree root object
        if parent is None:
            self.root = self
        else:
            self.root = parent.root

        if self.parent:
            self.ancestors = self.parent.ancestors + [self.parent]
        else:
            self.ancestors = []

        self.previous_sibling = None
        self.next_sibling = None

    def set_child(self, key, value):
        """
        If the attribute already exist, append as a list
        """
        child_node = CP2K_Input_Node(self, key, value)
        self.children_names.append(key)
        self.children_objects.append(child_node)
        return child_node

    def get_child(self, key) -> CP2K_Input_Node_type:
        """
        If the attribute is repeatable, return the last
        """
        ret = None
        # return Last one
        for child_key, value in zip(self.children_names, self.children_objects):
            if key == child_key:
                ret = value
        return ret

    def __getattr__(self, key) -> CP2K_Input_Node_type:
        """
        As a shortcut, you can use something like self.FORCE_EVAL.SUBSYS.CELL to access child nodes, assuming:
        1. the keyword doesn't collide with exising python object name (as __getattr__ is only called when the object isn't exist)
        2. the CP2K keyword name is python-allowed
        """
        return self.get_child(key)

    def path(self) -> str:
        if not self.ancestors:
            return ""
        return ".".join([x.name for x in self.ancestors])

    def __str__(self):
        """
        Python style print for the current branch
        Returns: imitate the python style input of https://github.com/SINGROUP/pycp2k

        """
        path = self.path()
        ret = ""
        ret += f"{path}{'.' if path else ''}{self.name} = {self.value}\n"
        for name, child in zip(self.children_names, self.children_objects):
            ret += str(child)

        return ret

    def generate_CP2K_input(self) -> str:
        """
        CP2K input for the current section, not including previous structures, also not including indentation
        Returns:

        """
        ret = ""
        if self.children_names:
            ret = "&"

        ret += f"{self.name} {'' if self.value is None else self.value}\n"

        for name, child in zip(self.children_names, self.children_objects):
            for line in child.generate_CP2K_input().splitlines():
                ret += "    " + line

        if self.children_names:
            ret = f"&END {self.name}\n"

        return ret


class CP2K_Input:
    def __init__(self, input_file: Optional[str] = None, input_content: Union[str, list, None] = None):
        """

        Args:
            input_data: can be a file, or the content of the file as one string or as a list of lines
        """
        self.input_file = input_file

        if input_file is not None:
            with open(input_file) as input_file_object:
                self.input_lines = input_file_object.read().splitlines()

        elif isinstance(input_content, str):
            self.input_lines = input_content.splitlines()
        else:
            self.input_lines = input_content

        self.input_object = CP2K_Input_Node(None, "ROOT")

        self.coordinate = None

        self.preprocess_input(self.input_lines)
        self.build_input_nodes()
        self.get_coordinate()
        # print(self.input_object.generate_CP2K_input())

    def __str__(self):
        return str(self.input_object)

    def generate_CP2K_input(self):
        return self.input_object.generate_CP2K_input()

    def get_coordinate(self):
        from Lib_Coordinates import Coordinates
        charge = self.input_object.FORCE_EVAL.DFT.Charge.value
        multiplicity = self.input_object.FORCE_EVAL.DFT.Multiplicity.value

        cell = self.input_object.FORCE_EVAL.SUBSYS.CELL
        vector_A = cell.A.value
        vector_B = cell.B.value
        vector_C = cell.C.value
        atoms = []
        coordinates: CP2K_Input_Node = self.input_object.FORCE_EVAL.SUBSYS.COORD
        for element, child in zip(coordinates.children_names, coordinates.children_objects):
            atoms.append(element + ' ' + child.value)
        self.coordinate = Coordinates(atoms, charge, multiplicity, periodic_cell=(vector_A, vector_B, vector_C))

    def set_coordinate(self, coordinate):
        # TODO
        pass

    def write_gjf(self, output_filepath):
        if self.coordinate is None:
            print("Coordinate not exist.")
        else:
            self.coordinate.gjf_file(filename=output_filepath)

    def open_gview(self):
        if self.coordinate is None:
            print("Coordinate not exist.")
        else:
            self.coordinate.open_GView()

    def change_project_name(self,project_name):
        self.input_object.GLOBAL.PROJECT = project_name

    def set_SCF_restart(self):
        project_name = self.input_object.GLOBAL.PROJECT
        self.input_object.FORCE_EVAL.DFT.WFN_RESTART_FILE_NAME = project_name+"-RESTART.wfn"
        self.input_object.FORCE_EVAL.DFT.SCF.SCF_GUESS = "RESTART"

    def set_Hessian_restart(self,RESTART_FILE_NAME):
        project_name = self.input_object.GLOBAL.PROJECT
        self.input_object.MOTION.GEO_OPT.BFGS.RESTART_HESSIAN = "T"
        self.input_object.MOTION.GEO_OPT.BFGS.RESTART_FILE_NAME = RESTART_FILE_NAME

    def preprocess_input(self, input_lines):
        """
        Adapted from github.com/SINGROUP/pycp2k

        Preprocess the input file. Concatenate .inc files into the main
        input file and explicitly state all variables.
        """
        input_lines = [x.strip() for x in input_lines]

        # Merge include files to input
        extended_input = input_lines[:]  # Make a copy
        i_line = 0
        for line in input_lines:
            if line.startswith("@INCLUDE") or line.startswith("@include"):
                split = line.split(None, 1)
                includepath = split[1]
                basedir = os.path.dirname(input_file)
                input_file = os.path.join(basedir, includepath)
                input_file = os.path.abspath(input_file)
                if not os.path.isfile(input_file):
                    logging.warning("Could not find the include file '{}' stated in the CP2K input file. Continuing without it.".format(input_file))
                    continue

                # Get the content from include file
                included_lines = []
                with open(input_file, "r") as includef:
                    for line in includef:
                        included_lines.append(line.strip())
                    del extended_input[i_line]
                    extended_input[i_line:i_line] = included_lines
                    i_line += len(included_lines)
            i_line += 1

        # Gather the variable definitions
        variables = {}
        input_set_removed = []
        for i_line, line in enumerate(extended_input):
            if line.startswith("@SET") or line.startswith("@set"):
                components = line.split(None, 2)
                name = components[1]
                value = components[2]
                variables[name] = value
                logging.debug("Variable '{}' found with value '{}'".format(name, value))
            else:
                input_set_removed.append(line)

        # Place the variables
        variable_pattern = r"\$\{(\w+)\}|\$(\w+)"
        compiled = re.compile(variable_pattern)
        reserved = ("include", "set", "if", "endif")
        input_variables_replaced = []
        for line in input_set_removed:
            results = compiled.finditer(line)
            new_line = line
            offset = 0
            for result in results:
                options = result.groups()
                first = options[0]
                second = options[1]
                if first:
                    name = first
                elif second:
                    name = second
                if name in reserved:
                    continue
                value = variables.get(name)
                if not value:
                    logging.error("Value for variable '{}' not set.".format(name))
                    continue
                len_value = len(value)
                len_name = len(name)
                start = result.start()
                end = result.end()
                beginning = new_line[:offset + start]
                rest = new_line[offset + end:]
                new_line = beginning + value + rest
                offset += len_value - len_name - 1
            input_variables_replaced.append(new_line)

        self.input_lines = input_variables_replaced
        return self.input_lines

    def build_input_nodes(self):
        """
        Adapted from github.com/SINGROUP/pycp2k

        Parses a CP2K input file into an object tree.

        Return an object tree representation of the input augmented with the
        default values and lone keyword values from the x_cp2k_input.xml file
        which is version specific. Keyword aliases are also mapped to the same
        data.

        The cp2k input is largely case-insensitive. In the input tree, we wan't
        only one standard way to name things, so all section names and section
        parameters will be transformed into upper case.

        To query the returned tree use the following functions:
            get_keyword("GLOBAL/PROJECT_NAME")
            get_parameter("GLOBAL/PRINT")
            get_default_keyword("FORCE_EVAL/SUBSYS/COORD")

        Args:
            : A string containing the contents of a CP2K input file. The
            input file can be stored as string as it isn't that big.

        Returns:
            The input as an object tree.
        """

        section_stack = []  # 记录当前路径
        section_objects = []
        path = ""

        for line in self.input_lines:
            # Remove comments and whitespaces
            line = line.split('!', 1)[0].split('#', 1)[0].strip()
            if not line:
                continue

            # Ignore variables and includes that might still be here for some reason
            if line.startswith('@'):
                continue

            # Section starts
            if line[0] == '&' and not line.upper().startswith('&END'):
                parts = line.split(' ', 1)
                name = parts[0][1:].upper()
                # handling - + and 0-9

                # Creation of section objects
                if len(section_stack) == 0:
                    parent_object = self.input_object
                else:
                    parent_object = section_objects[-1]

                # Save the section parameters
                section_value = parts[1].strip() if len(parts) > 1 else None
                section = parent_object.set_child(name, section_value)
                section_objects.append(section)
                section_stack.append(name)
                #
                # # Form the path
                # path = ""
                # for index, item in enumerate(section_stack):
                #     if index != 0:
                #         path += '/'
                #     path += item

            # Section ends
            elif line.upper().startswith('&END'):
                section_stack.pop()
                section_objects.pop()

            # Contents (keywords, default keywords)
            else:
                split = line.split(None, 1)
                if len(split) <= 1:
                    keyword_value = ""
                else:
                    keyword_value = split[1]
                keyword_name = split[0].capitalize()
                section.set_child(keyword_name, keyword_value)


# a = CP2K_Input(r"D:\Gaussian\JP_ZJC_Crystal_Packing_Energy_Decomposition\rod_hybrid_opt_PBE0_422_Supercell.inp")
# a.open_gview()

class CP2K_Output:
    def __init__(self, input_file: Optional[str] = None, input_content: Union[str, list, None] = None):
        self.input_file = input_file

        if input_file is not None:
            with open(input_file) as input_file_object:
                self.input_lines = input_file_object.read().splitlines()

        elif isinstance(input_content, str):
            self.input_lines = input_content.splitlines()
        else:
            self.input_lines = input_content


        self._last_coordinate = None
        self._project_name = None

    @property
    def project_name(self):
        if self._project_name is None:
            for line in self.input_lines:
                if line.startswith(" GLOBAL| Project name"):
                    self._project_name =line.removeprefix(" GLOBAL| Project name").strip()
                    break
        return self._project_name

    @property
    def last_coordinate(self):
        if self._last_coordinate is None:



