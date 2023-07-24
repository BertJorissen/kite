/***********************************************************/
/*                                                         */
/*   Copyright (C) 2018-2022, M. Andelkovic, L. Covaci,    */
/*  A. Ferreira, S. M. Joao, J. V. Lopes, T. G. Rappoport  */
/*                                                         */
/***********************************************************/

#include <Eigen/Dense>
#include <string>
#include <vector>
#include "H5Cpp.h"
#include "tools/parse_input.hpp"
#include "tools/systemInfo.hpp"
#include "optcond_2order/conductivity_2order.hpp"

template <typename U, unsigned DIM>
Eigen::Matrix<std::complex<U>, Eigen::Dynamic, Eigen::Dynamic> conductivity_nonlinear<U, DIM>::Gamma0contract(){

  Eigen::Matrix<std::complex<U>, Eigen::Dynamic, Eigen::Dynamic> omega_energies;
  Eigen::Matrix<std::complex<U>, Eigen::Dynamic, Eigen::Dynamic> temp;

  omega_energies = Eigen::Matrix<std::complex<U>, Eigen::Dynamic, Eigen::Dynamic>::Zero(N_energies, N_omegas);
  temp = Eigen::Matrix<std::complex<U>, Eigen::Dynamic, Eigen::Dynamic>::Zero(1,1);

  return -omega_energies;
}


// Instantiations
template Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic> conductivity_nonlinear<float, 1u>::Gamma0contract();
template Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic> conductivity_nonlinear<float, 2u>::Gamma0contract();
template Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic> conductivity_nonlinear<float, 3u>::Gamma0contract();

template Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic> conductivity_nonlinear<double, 1u>::Gamma0contract();
template Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic> conductivity_nonlinear<double, 2u>::Gamma0contract();
template Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic> conductivity_nonlinear<double, 3u>::Gamma0contract();

template Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic> conductivity_nonlinear<long double, 1u>::Gamma0contract();
template Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic> conductivity_nonlinear<long double, 2u>::Gamma0contract();
template Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic> conductivity_nonlinear<long double, 3u>::Gamma0contract();
