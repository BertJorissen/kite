/***********************************************************/
/*                                                         */
/*   Copyright (C) 2018-2022, M. Andelkovic, L. Covaci,    */
/*  A. Ferreira, S. M. Joao, J. V. Lopes, T. G. Rappoport  */
/*                                                         */
/***********************************************************/

#include <vector>
#include <iostream>
#include <complex>
#include <string>
#include <Eigen/Dense>
#include "H5Cpp.h"

#include "tools/ComplexTraits.hpp"
#include "tools/myHDF5.hpp"
#include "tools/parse_input.hpp"
#include "tools/calculate.hpp"
#include "macros.hpp"
#include "tools/messages.hpp"
//#include "compiletime_info.h"

int main(int argc, char *argv[]){
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