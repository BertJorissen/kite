#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <H5Cpp.h>
#include <H5Group.h>
#include "Generic.hpp"

template<typename T, unsigned D>
class Simulation;
#include "simulation/Global.hpp"
#include "tools/ComplexTraits.hpp"
#include "tools/myHDF5.hpp"
#include "tools/Random.hpp"
#include "lattice/Coordinates.hpp"
#include "lattice/LatticeStructure.hpp"
#include "hamiltonian/Hamiltonian.hpp"
#include "vector/KPM_VectorBasis.hpp"
#include "vector/KPM_Vector.hpp"
#include "tools/queue.hpp"
#include "simulation/Simulation.hpp"
#include "simulation/SimulationGlobal.hpp"
#include "tools/messages.hpp"


#include <vector>
#include <iostream>
#include <complex>
#include <string>
#include <Eigen/Dense>

#include "tools/parse_input.hpp"
#include "tools/calculate.hpp"
#include "macros.hpp"
#include "compiletime_info.h.in"

typedef int indextype;



int parse_main_kitex(char* path, int index){
    print_header_message();
    print_info_message();
    print_flags_message();

    verbose_message("\nStarting program...\n\n");
    debug_message("Starting program. The messages in red are debug messages. They may be turned off by setting DEBUG 0 in main.cpp\n");

    // Decide which version of the program should run. This depends on the
    // precision, the dimension and whether or not we want complex functions.
    switch (index ) {
        case 0:
        {
            class GlobalSimulation <float, 1u> h(path); // float real 1D
            break;
        }
        case 1:
        {
            class GlobalSimulation <float, 2u> h(path); // float real 2D
            break;
        }
        case 2:
        {
            class GlobalSimulation <float, 3u> h(path); // float real 3D
            break;
        }
        case 3:
        {
            class GlobalSimulation <double, 1u> h(path); // double real 1D
            break;
        }
        case 4:
        {
            class GlobalSimulation <double, 2u> h(path); //double real 2D. You get the picture.
            break;
        }
        case 5:
        {
            class GlobalSimulation <double, 3u> h(path);
            break;
        }
        case 6:
        {
            class GlobalSimulation <long double, 1u> h(path);
            break;
        }
        case 7:
        {
            class GlobalSimulation <long double, 2u> h(path);
            break;
        }
        case 8:
        {
            class GlobalSimulation <long double, 3u> h(path);
            break;
        }
        case 9:
        {
            class GlobalSimulation <std::complex<float>, 1u> h(path);
            break;
        }
        case 10:
        {
            class GlobalSimulation <std::complex<float>, 2u> h(path);
            break;
        }
        case 11:
        {
            class GlobalSimulation <std::complex<float>, 3u> h(path);
            break;
        }
        case 12:
        {
            class GlobalSimulation <std::complex<double>, 1u> h(path);
            break;
        }
        case 13:
        {
            class GlobalSimulation <std::complex<double>, 2u> h(path);
            break;
        }
        case 14:
        {
            class GlobalSimulation <std::complex<double>, 3u> h(path);
            break;
        }
        case 15:
        {
            class GlobalSimulation <std::complex<long double>, 1u> h(path);
            break;
        }
        case 16:
        {
            class GlobalSimulation <std::complex<long double>, 2u> h(path);
            break;
        }
        case 17:
        {
            class GlobalSimulation <std::complex<long double>, 3u> h(path);
            break;
        }
        default:
        {
            std::cout << "Unexpected parameters. Please use valid values for the precision, dimension and 'complex' flag.";
            std::cout << "Check if the code has been compiled with support for complex functions. Exiting.\n";
            exit(1);
        }
    }

    verbose_message("Done.\n");
    return 0;
}


int original_main_kite_tools(int argc, char *argv[]){
    if(argc < 2){
        std::cout << "No configuration file found. Exiting.\n";
        exit(1);
    }
    shell_input variables(argc, argv);
    print_header_message();
    print_info_message();
    print_flags_message();

    verbose_message("\nStarting program...\n\n");

    choose_simulation_type(argv[1], variables);
    verbose_message("Complete.\n");
    return 0;
}

int parse_main_kite_tools(const std::vector<std::string>& args) {
    std::vector<char*> argv;
    std::string program_name("KITE-tools");

    argv.push_back(const_cast<char *>(program_name.c_str()));
    for (auto &s : args) argv.push_back(const_cast<char *>(s.c_str()));
    return original_main_kite_tools(static_cast<int>(argv.size()), argv.data());
}


PYBIND11_MODULE(kitecore, m) {
    m.doc() = "pybind11 kite plugin"; // optional module docstring

    m.def("kitex", &parse_main_kitex, "Function that computes the moments from a HDF5 configuration file ");
    m.def("kite_tools", &parse_main_kite_tools, "Function that reconstructs a function from HDF5 configuration file");
}