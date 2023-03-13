## This script performs node voltage analysis on a SPICE file
## to generate its transfer function 

import sympy as sp
import sys

filename = sys.argv[1]

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

    elif component_type == "V":
        name = line[0]
        node_1 = line[1]
        node_2 = line[2]

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


    elif component_type == "I":
        name = line[0]
        node_1 = line[1]
        node_2 = line[2]

        I = sp.symbols("I" + name)

        # This is current flowing OUT of node 1
        # and INTO node 2, so it is defined as
        # NEGATIVE current for node 1 and
        # POSITIVE current for node 2
        add_negative_current_to_node(node_1, I)
        add_positive_current_to_node(node_2, I)        


def generate_KCL_equations():
    for node in node_list.keys():
        currents = node_list[node]

        # Kirchhoff's current law
        KCL_eq = sp.Eq(sum(currents), 0)
        equations.append(KCL_eq)

def solve_equations(output_var):
    sol = sp.solve(equations, output_var)
    return sol

def print_equations():
    for eq in equations:
        sp.pprint(eq)

def print_sols(sols):
    for sol in sols:
        sp.pprint(sp.Eq(sol, sols[sol]))

with open(filename) as netlist_file:
    lines = netlist_file.readlines()

    for line in lines:
        tokens = line.split(" ")
        
        handle_spice_line(tokens)

    generate_KCL_equations()
    print_equations()

    sols = solve_equations(unknowns)
    print_sols(sols)