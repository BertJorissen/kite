#include <stdio.h>
#include <omp.h>
#include <time.h>
#include <Eigen/Dense>
#include <Eigen/Eigenvalues>
#include "H5Cpp.h"
#include <H5Group.h>
#include <complex>
#include <random>
#include <vector>
#include <iostream>
#include <fstream>
#include <algorithm>
#include <typeinfo>
#include <type_traits>
#include <complex>
#include <iostream>
#include <chrono>
#include <thread>
#include <cmath>
#include <math.h>
#include <initializer_list>

#define MEMORY   10
#define PATTERNS  4
#define NGHOSTS   2
#ifndef STRIDE
#define STRIDE    128
#endif


#define outcol "\033[1;31m"
#define outres "\033[0m"

#define DEBUG 1
#define VERBOSE 0

#ifdef VERBOSE
#if VERBOSE==1
#define verbose_message(VAR) std::cout<<VAR<<std::flush
#else
#define verbose_message(VAR) 
#endif
#else
#define verbose_message(VAR) 
#endif

#ifdef DEBUG
#if DEBUG==1
#define debug_message(VAR) std::cout << outcol << VAR << outres << std::flush
#else
#define debug_message(VAR) 
#endif
#else
#define debug_message(VAR) 
#endif

template<typename T, unsigned D>
class Simulation;
#include "Global.hpp"
#include "ComplexTraits.hpp"
#include "myHDF5.hpp"
#include "Random.hpp"
#include "LatticeStructure.hpp"
#include "Hamiltonian.hpp"
#include "KPM_Vector.hpp"
#include "KPM_Vector2D.hpp"
#include "Simulation.hpp"

typedef int indextype;



int main(int argc, char *argv[])
{  
  debug_message("Starting program. The messages in red are debug messages. They may be turned off by setting DEBUG 0 in main.cpp\n");
  std::cout << "The Stride is set to " << STRIDE << std::endl ;
  /* Define General characteristics of the data */  
  int precision = 1, dim, is_complex;

  H5::H5File *file = new H5::H5File(argv[1], H5F_ACC_RDONLY);
  get_hdf5(&is_complex, file, (char *) "/IS_COMPLEX");
  get_hdf5(&precision,  file, (char *) "/PRECISION");
  get_hdf5(&dim,        file, (char *) "/DIM");
  
  std::vector <int> MagneticField;      
  MagneticField.resize  (1);
  MagneticField.at(0) = 0;
  try {
		H5::Exception::dontPrint();
		get_hdf5<int>(MagneticField.data(),  file, (char *)   "/Hamiltonian/MagneticField");
	}
	catch (H5::Exception& e){}
  
  // Magnetic field requires complex-valued functions. Make sure the user knows about this
	if(MagneticField.at(0) == 1 and !is_complex){
		std::cout << "If you want to include a magnetic field, please use complex-valued functions. ";
		std::cout << "This may be done by setting the 'complex' flag to True in the lattice_building python script.\n";
		exit(1);		
  }
	
  
  file->close();
  
  if(dim < 1 || dim > 3)
    exit(0);
  
  if(precision < 0 || precision > 2)
    exit(0);
  
  if(is_complex < 0 || is_complex > 1)
    exit(0);

  int index =   dim - 1 + 3 * precision + is_complex * 3 * 3; 

  switch (index ) {
    /*
     * Float Real 
     *//*
  case 0:
    {
      class GlobalSimulation <float, 1u> h(argv[1]);
      break;
    }*/
  case 1:
    {
      class GlobalSimulation <float, 2u> h(argv[1]);
      break;
    }/*
  case 2:
    {
      class GlobalSimulation <float, 3u> h(argv[1]);
      break;
    }
  case 3:
    {
      class GlobalSimulation <double, 1u> h(argv[1]);
      break;
    }*/
  case 4:
    {
      class GlobalSimulation <double, 2u> h(argv[1]);
      break;
    }/*
  case 5:
    {
      class GlobalSimulation <double, 3u> h(argv[1]);
      break;
    }
  case 6:
    {
      class GlobalSimulation <long double, 1u> h(argv[1]);
      break;
    }
  case 7:
    {
      class GlobalSimulation <long double, 2u> h(argv[1]);
      break;
    }
  case 8:
    {
      class GlobalSimulation <long double, 3u> h(argv[1]);
      break;
    }
    
     
  case 9:
    {
      class GlobalSimulation <std::complex<float>, 1u> h(argv[1]);
      break;
    }
  case 10:
    {
      class GlobalSimulation <std::complex<float>, 2u> h(argv[1]);
      break;
    }
  case 11:
    {
      class GlobalSimulation <std::complex<float>, 3u> h(argv[1]);
      break;
    }*/
  case 12:
    {
      class GlobalSimulation <std::complex<double>, 1u> h(argv[1]);
      break;
    }
  case 13:
    {
      class GlobalSimulation <std::complex<double>, 2u> h(argv[1]);
      break;
    }
  case 14:
    {
      class GlobalSimulation <std::complex<double>, 3u> h(argv[1]);
      break;
    }/*
  case 15:
    {
      class GlobalSimulation <std::complex<long double>, 1u> h(argv[1]);
      break;
    }
  case 16:
    {
      class GlobalSimulation <std::complex<long double>, 2u> h(argv[1]);
      break;
    }
  case 17:
    {
      class GlobalSimulation <std::complex<long double>, 3u> h(argv[1]);
      break;
    }*/

  default:
    exit(0);
  } 
  
  debug_message("Program ended with success!\n");
  return 1;
}

