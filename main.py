## This script performs node voltage analysis on a SPICE file
## to generate its transfer function 

import sympy as sp
import sys

filename = sys.argv[1]
input_var = sys.argv[2]
output_var = sys.argv[3]

sp.init_printing()

TO_IGNORE = ["*", \
             ".backanno", \
             ".end"]

# Each entry in node_list is of the form
# key: a string representing the node's name
# value: list of currents (SymPy variables), where positive current
#        indicates current flowing INTO the node
node_list = {}

equations = []

unknowns = []

values = {}

# Laplace variable
s = sp.symbols("s")

def add_positive_current_to_node(node, current):
    if node in node_list.keys():
        node_list[node].append(current)
        unknowns.append(sp.symbols("V" + node))
    else:
        node_list[node] = [current]

def add_negative_current_to_node(node, current):
    if node in node_list.keys():
        node_list[node].append(-1 * current)
        unknowns.append(sp.symbols("V" + node))
    else:
        node_list[node] = [-1 * current]

def add_voltage_source(Vnode_1, Vnode_2, Vsrc_symbol, Vsrc_current):
    # A voltage source imposes the constraint that the difference
    # between its positive and negative nodes is equal to its value
    voltage_constraint = sp.Eq(Vsrc_symbol, Vnode_1 - Vnode_2)
    equations.append(voltage_constraint)
    unknowns.append(Vsrc_current)

def add_component(component, value):

    value = value.lower()

    # replace the "mu" symbol used for "micro"
    # with the letter "u"
    value = value.replace("µ", "u")

    value = value.strip("h")
    value = value.strip("f")
    value = value.strip("r")
    value = value.strip("v")
    value = value.strip("a")
    
    parsed_val = 0

    if value.isnumeric():
        parsed_val = int(value)
    elif value.endswith("meg"):
        parsed_val = int(value[:-3]) * 10**6
    elif value.endswith("mil"):
        parsed_val = int(value[:-3]) * 25.4 * 10**-6
    elif value.endswith("t"):
        parsed_val = int(value[:-1]) * 10**12
    elif value.endswith("g"):
        parsed_val = int(value[:-1])* 10**9
    elif value.endswith("k"):
        parsed_val = int(value[:-1]) * 10**3
    elif value.endswith("m"):
        parsed_val = int(value[:-1]) * 10**-3
    elif value.endswith("u"):
        parsed_val = int(value[:-1]) * 10**-6
    elif value.endswith("n"):
        parsed_val = int(value[:-1]) * 10**-9
    elif value.endswith("p"):
        parsed_val = int(value[:-1]) * 10**-12
    elif value.endswith("f"):
        parsed_val = int(value[:-1]) * 10**-15
    else:
        raise ValueError("Could not interpret value " + value + " for component " + component)
    
    values[component] = parsed_val


def handle_spice_line(line):

    if line[0] in TO_IGNORE:
        return

    # The direction of current flowing through any component is defined
    # as positive when it flows from the node listed first in the SPICE
    # line to the node listed as the second in the SPICE line
    
    component_type = line[0][0]

    if component_type == "R" \
        or component_type == "C" \
        or component_type == "L":

        name = line[0]
        node_1 = line[1]
        node_2 = line[2]
        value = line[3]
        
        Vnode_1 = sp.symbols("V" + node_1) if node_1 != "0" else 0
        Vnode_2 = sp.symbols("V" + node_2) if node_2 != "0" else 0
        symbol = sp.symbols(name)

        if component_type == "R":
            Z = symbol
        elif component_type == "C":
            Z = 1 / (s * symbol)
        elif component_type == "L":
            Z = s * symbol

        I = (Vnode_1 - Vnode_2) / Z
        
        # This is current flowing OUT of node 1
        # and INTO node 2, so it is defined as
        # NEGATIVE current for node 1 and
        # POSITIVE current for node 2
        add_negative_current_to_node(node_1, I)
        add_positive_current_to_node(node_2, I)

        add_component(name, value)

    elif component_type == "V":
        name = line[0]
        node_1 = line[1]
        node_2 = line[2]
        value = line[3]

        Vnode_1 = sp.symbols("V" + node_1) if node_1 != "0" else 0
        Vnode_2 = sp.symbols("V" + node_2) if node_2 != "0" else 0
        symbol = sp.symbols(name)

        I = sp.symbols("I" + name)

        # This is current flowing OUT of node 1
        # and INTO node 2, so it is defined as
        # NEGATIVE current for node 1 and
        # POSITIVE current for node 2
        add_negative_current_to_node(node_1, I)
        add_positive_current_to_node(node_2, I)

        add_voltage_source(Vnode_1, Vnode_2, symbol, I)

        add_component(name, value)


    elif component_type == "I":
        name = line[0]
        node_1 = line[1]
        node_2 = line[2]
        value = line[3]

        I = sp.symbols("I" + name)

        # This is current flowing OUT of node 1
        # and INTO node 2, so it is defined as
        # NEGATIVE current for node 1 and
        # POSITIVE current for node 2
        add_negative_current_to_node(node_1, I)
        add_positive_current_to_node(node_2, I)

        add_component(name, value)     


def generate_KCL_equations():
    for node in node_list.keys():
        currents = node_list[node]

        # Kirchhoff's current law
        KCL_eq = sp.Eq(sum(currents), 0)
        equations.append(KCL_eq)

def solve_equations(output_var):
    sol = sp.solve(equations, output_var)
    return sol

def find_transfer_function(input_var, output_var):
    input_sym = sp.symbols(input_var)
    output_sym = sp.symbols(output_var)

    input_var_expression = sols[input_sym]
    output_var_expression = sols[output_sym]

    transfer_func = output_var_expression / input_var_expression
    return transfer_func

def print_equations():
    print("EQUATIONS ============================================================")
    for eq in equations:
        sp.pprint(eq)
    print()

def print_sols(sols):
    print("SOLUTIONS ============================================================")
    for sol in sols:
        sp.pprint(sp.Eq(sol, sols[sol]))
    print()

def print_transfer_func(input_var, output_var, transfer_func):
    print("TRANSFER FUNCTION ====================================================")
    
    input_sym = sp.symbols(input_var)
    output_sym = sp.symbols(output_var)

    sp.pprint(sp.Eq(output_sym / input_sym, transfer_func))

    print()

def print_component_values():
    print("COMPONENTS ==========================================================")

    for component in values.keys():
        print(component + " has a value of " + str(values[component]), end='')

        if component.startswith("R"):
            print(" ohms")
        elif component.startswith("L"):
            print(" H")
        elif component.startswith("C"):
            print(" C")
        elif component.startswith("V"):
            print(" V")
        elif component.startswith("I"):
            print(" A")
        else:
            print()
    print()


with open(filename) as netlist_file:
    lines = netlist_file.readlines()

    for line in lines:
        tokens = line.split(" ")
        tokens = [token.strip() for token in tokens]
        
        handle_spice_line(tokens)

    print_component_values()

    generate_KCL_equations()
    print_equations()

    sols = solve_equations(unknowns)
    print_sols(sols)

    transfer_func = find_transfer_function(input_var, output_var)
    print_transfer_func(input_var, output_var, transfer_func)

