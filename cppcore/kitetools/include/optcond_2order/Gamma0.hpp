/***********************************************************/
/*                                                         */
/*   Copyright (C) 2018-2022, M. Andelkovic, L. Covaci,    */
/*  A. Ferreira, S. M. Joao, J. V. Lopes, T. G. Rappoport  */
/*                                                         */
/***********************************************************/


template <typename U, unsigned DIM>
Eigen::Matrix<std::complex<U>, Eigen::Dynamic, Eigen::Dynamic> conductivity_nonlinear<U, DIM>::Gamma0contract(){

  Eigen::Matrix<std::complex<U>, Eigen::Dynamic, Eigen::Dynamic> omega_energies;
  Eigen::Matrix<std::complex<U>, Eigen::Dynamic, Eigen::Dynamic> temp;

  omega_energies = Eigen::Matrix<std::complex<U>, Eigen::Dynamic, Eigen::Dynamic>::Zero(N_energies, N_omegas);
  temp = Eigen::Matrix<std::complex<U>, Eigen::Dynamic, Eigen::Dynamic>::Zero(1,1);

  return omega_energies;
}
