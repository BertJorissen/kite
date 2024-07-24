/***********************************************************/
/*                                                         */
/*   Copyright (C) 2018-2022, M. Andelkovic, L. Covaci,    */
/*  A. Ferreira, S. M. Joao, J. V. Lopes, T. G. Rappoport  */
/*                                                         */
/***********************************************************/


#include <Eigen/Dense>
#include <complex>
#include <H5Cpp.h>
#include <vector>
#include "tools/parse_input.hpp"
#include "tools/systemInfo.hpp"
#include "conddc/conductivity_dc.hpp"
#include "tools/functions.hpp"
#include <fstream>
#include <cmath>
#include <omp.h>
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

template <typename T, unsigned DIM>
Eigen::Matrix<std::complex<T>, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor> conductivity_dc<T, DIM>::fill_delta(){

  Eigen::Matrix<std::complex<T>, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor> greenR;
  greenR = Eigen::Matrix<std::complex<T>, Eigen::Dynamic, Eigen::Dynamic>::Zero(Moments_G, NEnergies);

  // Imaginary part of the Green's function: Dirac delta
  T factor;
  std::complex<T> complexEnergy;
  for(int i = 0; i < NEnergies; i++){
    complexEnergy = std::complex<T>(energies(i), deltascat);
    for(int m = 0; m < Moments_G; m++){
      factor = static_cast<T>(-1.0/(1.0 + static_cast<T>(m==0))/M_PI);
      greenR(m, i) = green(m, 1, complexEnergy).imag()*factor;
    }
  }
  return greenR;
}

template <typename T, unsigned DIM>
Eigen::Matrix<std::complex<T>, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> conductivity_dc<T, DIM>::fill_dgreenR(){
  std::complex<T> complexEnergyP;

  Eigen::Matrix<std::complex<T>, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> dgreenR;
  dgreenR = Eigen::Matrix<std::complex<T>, Eigen::Dynamic, Eigen::Dynamic>::Zero(NEnergies, Moments_D);

  T factor;
  for(int i = 0; i < NEnergies; i++){
    complexEnergyP = std::complex<T>(energies(i), scat);
    for(int m = 0; m < Moments_D; m++){
      factor = static_cast<T>(1.0/(1.0 + static_cast<T>(m==0)));
      dgreenR(i, m) = dgreen<T>(m,  1, complexEnergyP)*factor;
    }
  }
  return dgreenR;
}


template <typename T, unsigned DIM>
Eigen::Matrix<std::complex<T>, Eigen::Dynamic, Eigen::Dynamic> conductivity_dc<T, DIM>::triple_product(
  Eigen::Matrix<std::complex<T>, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor> greenR,
  Eigen::Matrix<std::complex<T>, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> dgreenR){

  // GammaE has NE elements
  Eigen::Array<std::complex<T>, Eigen::Dynamic, Eigen::Dynamic> GammaE;
  GammaE = Eigen::Array<std::complex<T>, Eigen::Dynamic, Eigen::Dynamic>::Zero(NEnergies, 1);

  omp_set_num_threads(NumThreads);
#pragma omp parallel firstprivate(greenR)
  {

#pragma omp for schedule(static, 1) nowait
    for(int thread = 0; thread < NumThreads; thread++){
      int localMoments = Moments_D/NumThreads;

      Eigen::Matrix<std::complex<T>, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> LocalGamma;
      Eigen::Matrix<std::complex<T>, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> local_dgreenR;
      Eigen::Matrix<std::complex<T>, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor> GammaEN;
      Eigen::Array<std::complex<T>, Eigen::Dynamic, Eigen::Dynamic> LocalGammaE;

      LocalGamma = Gamma_Padded.matrix().block(thread*localMoments, 0, localMoments, Moments_G);
      local_dgreenR = dgreenR.matrix().block(0, thread*localMoments, NEnergies, localMoments);

      // GammaEN has NE * ND/T elements
      GammaEN = LocalGamma*greenR;

      // LocalGammaE has NE elements
      LocalGammaE = Eigen::Array<std::complex<T>, Eigen::Dynamic, Eigen::Dynamic>::Zero(NEnergies, 1);
      for(int i = 0; i < NEnergies; i++)
        LocalGammaE(i) = std::complex<T>(local_dgreenR.row(i)*GammaEN.col(i));

#pragma omp critical
      {
      GammaE += 2*LocalGammaE.imag();
      }
    }
#pragma omp barrier
  }
  return GammaE;

}



template <typename U, unsigned DIM>
Eigen::Matrix<std::complex<U>, Eigen::Dynamic, 1> conductivity_dc<U, DIM>::calc_cond(Eigen::Matrix<std::complex<U>, Eigen::Dynamic, Eigen::Dynamic> GammaE){

  Eigen::Matrix<std::complex<U>, Eigen::Dynamic, 1> condDC;
  Eigen::Matrix<std::complex<U>, Eigen::Dynamic, 1> integrand;


  condDC = Eigen::Matrix<std::complex<U>, Eigen::Dynamic, 1>::Zero(NFermiEnergies, 1);
  integrand = Eigen::Matrix<std::complex<U>, Eigen::Dynamic, 1>::Zero(NEnergies, 1);

  U fermi;
  for(int i = 0; i < NFermiEnergies; i++){
    fermi = fermiEnergies(i);
    for(int j = 0; j < NEnergies; j++){
      integrand(j) = GammaE(j)*fermi_function(energies(j), fermi, beta);
    }
    condDC(i) = integrate(energies, integrand);
  }

  return condDC;
}



template <typename U, unsigned DIM>
void conductivity_dc<U, DIM>::save_to_file(Eigen::Matrix<std::complex<U>, Eigen::Dynamic, Eigen::Dynamic> condDC){

  std::complex<U> cond;
  U energy;
  std::ofstream myfile;
  myfile.open(filename);
  for(int i=0; i < NFermiEnergies; i++){
    energy = static_cast<U>(fermiEnergies(i) * systemInfo.energy_scale + systemInfo.energy_shift);
    cond = condDC(i);
    myfile  << energy << " " << cond.real() << " " << cond.imag() << "\n";
  }
  
  myfile.close();


}

template Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor> conductivity_dc<float, 1u>::fill_delta();
template Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor> conductivity_dc<float, 2u>::fill_delta();
template Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor> conductivity_dc<float, 3u>::fill_delta();

template Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor> conductivity_dc<double, 1u>::fill_delta();
template Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor> conductivity_dc<double, 2u>::fill_delta();
template Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor> conductivity_dc<double, 3u>::fill_delta();

template Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor> conductivity_dc<long double, 1u>::fill_delta();
template Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor> conductivity_dc<long double, 2u>::fill_delta();
template Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor> conductivity_dc<long double, 3u>::fill_delta();






template Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> conductivity_dc<float, 1u>::fill_dgreenR();
template Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> conductivity_dc<float, 2u>::fill_dgreenR();
template Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> conductivity_dc<float, 3u>::fill_dgreenR();

template Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> conductivity_dc<double, 1u>::fill_dgreenR();
template Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> conductivity_dc<double, 2u>::fill_dgreenR();
template Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> conductivity_dc<double, 3u>::fill_dgreenR();

template Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> conductivity_dc<long double, 1u>::fill_dgreenR();
template Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> conductivity_dc<long double, 2u>::fill_dgreenR();
template Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> conductivity_dc<long double, 3u>::fill_dgreenR();




template Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic> conductivity_dc<float, 1u>::triple_product(Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor>, Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor>);
template Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic> conductivity_dc<float, 2u>::triple_product(Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor>, Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor>);
template Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic> conductivity_dc<float, 3u>::triple_product(Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor>, Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor>);

template Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic> conductivity_dc<double, 1u>::triple_product(Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor>, Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor>);
template Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic> conductivity_dc<double, 2u>::triple_product(Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor>, Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor>);
template Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic> conductivity_dc<double, 3u>::triple_product(Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor>, Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor>);

template Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic> conductivity_dc<long double, 1u>::triple_product(Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor>, Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor>);
template Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic> conductivity_dc<long double, 2u>::triple_product(Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor>, Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor>);
template Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic> conductivity_dc<long double, 3u>::triple_product(Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor>, Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor>);




template Eigen::Matrix<std::complex<float>, Eigen::Dynamic, 1> conductivity_dc<float, 1u>::calc_cond(Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic>);
template Eigen::Matrix<std::complex<float>, Eigen::Dynamic, 1> conductivity_dc<float, 2u>::calc_cond(Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic>);
template Eigen::Matrix<std::complex<float>, Eigen::Dynamic, 1> conductivity_dc<float, 3u>::calc_cond(Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic>);

template Eigen::Matrix<std::complex<double>, Eigen::Dynamic, 1> conductivity_dc<double, 1u>::calc_cond(Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic>);
template Eigen::Matrix<std::complex<double>, Eigen::Dynamic, 1> conductivity_dc<double, 2u>::calc_cond(Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic>);
template Eigen::Matrix<std::complex<double>, Eigen::Dynamic, 1> conductivity_dc<double, 3u>::calc_cond(Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic>);

template Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, 1> conductivity_dc<long double, 1u>::calc_cond(Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic>);
template Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, 1> conductivity_dc<long double, 2u>::calc_cond(Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic>);
template Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, 1> conductivity_dc<long double, 3u>::calc_cond(Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic>);



template void conductivity_dc<float, 1u>::save_to_file(Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic>);
template void conductivity_dc<float, 2u>::save_to_file(Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic>);
template void conductivity_dc<float, 3u>::save_to_file(Eigen::Matrix<std::complex<float>, Eigen::Dynamic, Eigen::Dynamic>);

template void conductivity_dc<double, 1u>::save_to_file(Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic>);
template void conductivity_dc<double, 2u>::save_to_file(Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic>);
template void conductivity_dc<double, 3u>::save_to_file(Eigen::Matrix<std::complex<double>, Eigen::Dynamic, Eigen::Dynamic>);

template void conductivity_dc<long double, 1u>::save_to_file(Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic>);
template void conductivity_dc<long double, 2u>::save_to_file(Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic>);
template void conductivity_dc<long double, 3u>::save_to_file(Eigen::Matrix<std::complex<long double>, Eigen::Dynamic, Eigen::Dynamic>);
