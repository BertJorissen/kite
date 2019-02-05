#include "Generic.hpp"
#include "ComplexTraits.hpp"
#include "myHDF5.hpp"
#include "Global.hpp"
#include "Random.hpp"
#include "Coordinates.hpp"
#include "LatticeStructure.hpp"
template <typename T, unsigned D>
class Hamiltonian;
template <typename T, unsigned D>
class KPM_Vector;
#include "queue.hpp"
#include "Simulation.hpp"
#include "Hamiltonian.hpp"
#include "KPM_VectorBasis.hpp"
#include "KPM_Vector.hpp"

template <typename T,unsigned D>
void Simulation<T,D>::Gamma2D(int NRandomV, int NDisorder, std::vector<int> N_moments, 
                              std::vector<std::vector<unsigned>> indices, std::string name_dataset){
  Eigen::Matrix<T, MEMORY, MEMORY> tmp;
  // This function calculates all kinds of two-dimensional gamma matrices such
  // as Tr[V^a Tn v^b Tm] = G_nm
  //
  // The matrices are stored as
  //
  // | G_00   G_01   G_02   ...   G_0M | 
  // | G_10   G_11   G_12   ...   G_1M | 
  // | G_20   G_21   G_22   ...   G_2M | 
  // | ...    ...    ...    ...   ...  |
  // | G_N0   G_N1   G_N2   ...   G_NM | 
  //
  // For example, a 3x3 matrix would be represented as
  //
  // | G_00   G_01   G_02 | 
  // | G_10   G_11   G_12 | 
  // | G_20   G_21   G_22 | 
  //
  // This function calculates all the kinds of one-dimensional Gamma matrices
  // such as Tr[Tn]    Tr[v^xx Tn]     etc

  typedef typename extract_value_type<T>::value_type value_type;

  int num_velocities = 0;
  for(int i = 0; i < int(indices.size()); i++)
    num_velocities += indices.at(i).size();
  int factor = 1 - (num_velocities % 2)*2;

  //  --------- INITIALIZATIONS --------------
    
  KPM_Vector<T,D> kpm0(1, *this);      // initial random vector
  KPM_Vector<T,D> kpm1(2, *this); // left vector that will be Chebyshev-iterated on
  KPM_Vector<T,D> kpm2(MEMORY, *this); // right vector that will be Chebyshev-iterated on
  KPM_Vector<T,D> kpm3(MEMORY, *this); // kpm1 multiplied by the velocity

  // initialize the local gamma matrix and set it to 0
  int size_gamma = 1;
  for(int i = 0; i < 2; i++){
    if(N_moments.at(i) % 2 != 0){
      std::cout << "The number of moments must be an even number, due to limitations of the program. Aborting\n";
      exit(1);
    }
    size_gamma *= N_moments.at(i);
  }

  Eigen::Array<T, -1, -1> gamma = Eigen::Array<T, -1, -1 >::Zero(1, size_gamma);
 
  // finished initializations


    
    
  // start the kpm iteration
  long average = 0;
  for(int disorder = 0; disorder < NDisorder; disorder++){
    h.generate_disorder();
    for(unsigned it = 0; it < indices.size(); it++)
      h.build_velocity(indices.at(it), it);
    for(int randV = 0; randV < NRandomV; randV++){
        

      kpm0.initiate_vector();			// original random vector. This sets the index to zero
      kpm0.Exchange_Boundaries();
      kpm1.set_index(0);

      generalized_velocity(&kpm1, &kpm0, indices, 0);
        
      // run through the left loop MEMORY iterations at a time
      for(int n = 0; n < N_moments.at(0); n+=MEMORY){
          
        // Iterate MEMORY times. The first time this occurs, we must exclude the zeroth
        // case, because it is already calculated, it's the identity
        for(int i = n; i < n + MEMORY; i++){
          if(i!=0){
            cheb_iteration(&kpm1, i-1);
          }

          kpm3.set_index(i%MEMORY);
          generalized_velocity(&kpm3, &kpm1, indices, 1);
          kpm3.empty_ghosts(i%MEMORY);
        }
          
        // copy the |0> vector to |kpm2>
        kpm2.set_index(0);
        kpm2.v.col(0) = kpm0.v.col(0);
        for(int m = 0; m < N_moments.at(1); m+=MEMORY){

          // iterate MEMORY times, just like before. No need to multiply by v here
          for(int i = m; i < m + MEMORY; i++){
            if(i!=0){
              cheb_iteration(&kpm2, i-1);
            }
          }
          //std::cout << "index2: " << kpm2.get_index() << "\n";
          // Finally, do the matrix product and store the result in the Gamma matrix
          tmp.setZero();
          for(std::size_t ii = 0; ii < r.Sized ; ii += r.Ld[0])
            tmp += kpm3.v.block(ii,0, r.Ld[0], MEMORY).adjoint() * kpm2.v.block(ii, 0, r.Ld[0], MEMORY);
          T flatten;
          long int ind;
          for(int j = 0; j < MEMORY; j++)
            for(int i = 0; i < MEMORY; i++){
              flatten = tmp(i,j);
              ind = (m+j)*N_moments.at(0) + n+i;
              gamma(ind) += (flatten - gamma(ind))/value_type(average + 1);			
            }
        }
      }
      average++;
    }
  } 
  gamma = gamma*factor;
            
  store_gamma(&gamma, N_moments, indices, name_dataset);
};


// Finally, do the matrix product and store the result in the Gamma matrix
template <typename T,unsigned D>
void Simulation<T,D>::Gamma3D(int NRandomV, int NDisorder, std::vector<int> N_moments, 
                              std::vector<std::vector<unsigned>> indices, std::string name_dataset){
  Eigen::Matrix<T, MEMORY, MEMORY> tmp;
  // This calculates all the kinds of three-dimensional gamma matrices
  // such as Tr[v^a Tn v^b Tm v^c Tp] = G_nmp. The output is a 2D matrix 
  // organized as follows:
  // 
  //    p=0     p=1     p=2    ...    p=P
  // 
  // | G_000   G_001   G_002   ...   G_00P | 
  // | G_100   G_101   G_102   ...   G_10P |  
  // | G_200   G_201   G_202   ...   G_20P |   m=0
  // |  ...     ...     ...    ...    ...  |  
  // | G_N00   G_N01   G_N02   ...   G_N1P |_____
  // | G_010   G_011   G_012   ...   G_01P | 
  // | G_110   G_111   G_112   ...   G_11P |  
  // | G_210   G_211   G_212   ...   G_21P |   m=1
  // |  ...     ...     ...    ...    ...  |  
  // | G_N10   G_N11   G_N12   ...   G_N0P |_____ 
  // |  ...     ...     ...    ...    ...  |
  // |  ...     ...     ...    ...    ...  |
  // |  ...     ...     ...    ...    ...  |_____
  // | G_0M0   G_0M1   G_0M2   ...   G_0MP | 
  // | G_1M0   G_1M1   G_1M2   ...   G_1MP |  
  // | G_2M0   G_2M1   G_2M2   ...   G_2MP |   m=M
  // |  ...     ...     ...    ...    ...  |  
  // | G_NM0   G_NM1   G_NM2   ...   G_NMP |_____ 
  //
  // To exemplify, in the case of a 3x3x3 matrix, 
  //
  // | G_000   G_001   G_002 |
  // | G_100   G_101   G_102 |
  // | G_200   G_201   G_202 |
  // | G_010   G_011   G_012 |
  // | G_110   G_111   G_112 |
  // | G_210   G_211   G_212 |
  // | G_020   G_021   G_022 |
  // | G_120   G_121   G_122 |
  // | G_220   G_221   G_222 |
  //
  // This matrix can be huge, and each thread will have a copy, so it's very
  // easy to use up enormous ammounts of memory. This is why the matrix is calculated
  // in blocks
  //
    
  typedef typename extract_value_type<T>::value_type value_type;
    
  //  --------- INITIALIZATIONS --------------
    
  KPM_Vector<T,D> kpm0(1, *this);           // initial random vector
  KPM_Vector<T,D> kpm_Vn(2, *this);          // left vector that will be Chebyshev-iterated on
  KPM_Vector<T,D> kpm_VnV(MEMORY, *this);    // kpmL multiplied by the velocity
  KPM_Vector<T,D> kpm_p(2, *this);          // right-most vector that will be Chebyshev-iterated on
  KPM_Vector<T,D> kpm_pVm(MEMORY, *this);         // middle vector that will be Chebyshev-iterated on
    
  // initialize the local gamma matrix and set it to 0
  int size_gamma = 1;
  for(int i = 0; i < 3; i++){
    if(N_moments.at(i) % 2 != 0){
      std::cout << "The number of moments must be an even number, due to limitations of the program. Aborting\n";
      exit(1);
    }
    size_gamma *= N_moments.at(i);
  }
#pragma omp master
  {
    Global.general_gamma = Eigen::Array<T, -1, -1>::Zero(1, size_gamma);
    Global.smaller_gamma = Eigen::Array<T, -1, -1>::Zero(MEMORY, MEMORY);
  }
#pragma omp barrier
    
  // finished initializations
    
  // start the kpm iteration
  long average = 0;
  for(int disorder = 0; disorder < NDisorder; disorder++){

    // Distribute the disorder and update the velocity matrices
    h.generate_disorder();
    for(unsigned it = 0; it < indices.size(); it++)
      h.build_velocity(indices.at(it), it);

    for(int randV = 0; randV < NRandomV; randV++){
        
        
      kpm0.initiate_vector();			// original random vector. This sets the index to zero
      kpm0.Exchange_Boundaries();
      kpm_Vn.set_index(0);

      generalized_velocity(&kpm_Vn, &kpm0, indices, 0);
        
      for(int n = 0; n < N_moments.at(0); n+=MEMORY){

        // Calculation of the left kpm vector
        for(int ni = n; ni < n + MEMORY; ni++){
          if(ni!=0) cheb_iteration(&kpm_Vn, ni-1);
           
          kpm_VnV.set_index(ni%MEMORY);
          generalized_velocity(&kpm_VnV, &kpm_Vn, indices, 1);
          kpm_VnV.empty_ghosts(ni%MEMORY);
        }
          
        // Calculation of the right kpm vector
        kpm_p.set_index(0);
        kpm_p.v.col(0) = kpm0.v.col(0);
        for(int p = 0; p < N_moments.at(2); p++){
          if(p!=0) cheb_iteration(&kpm_p, p-1);
            
          kpm_pVm.set_index(0);
          generalized_velocity(&kpm_pVm, &kpm_p, indices, 2);
          for(int m = 0; m < N_moments.at(1); m += MEMORY){
            for(int mi = m; mi < m + MEMORY; mi++)
              if(mi != 0) cheb_iteration(&kpm_pVm, mi-1);

            tmp.setZero();
            for(std::size_t ii = 0; ii < r.Sized ; ii += r.Ld[0])
              tmp += kpm_VnV.v.block(ii,0, r.Ld[0], MEMORY).adjoint() * kpm_pVm.v.block(ii, 0, r.Ld[0], MEMORY);
              
#pragma omp master
            {
              Global.smaller_gamma.setZero();
            }
#pragma omp barrier
#pragma omp critical
            {
              Global.smaller_gamma += tmp.array();
            }
#pragma omp barrier
#pragma omp master
            {
              long int index;
              for(int i = 0; i < MEMORY; i++)
                for(int j = 0; j < MEMORY; j++){
                  index = p*N_moments.at(1)*N_moments.at(0) + (m+j)*N_moments.at(0) + n+i;
                  Global.general_gamma(index) += (Global.smaller_gamma(i, j) - Global.general_gamma(index))/value_type(average + 1);
                }
            }
#pragma omp barrier
          }
        }
      }
      average++;
    }
  } 
#pragma omp master
  {
    store_gamma3D(&Global.general_gamma, N_moments, indices, name_dataset);
    
  }
#pragma omp barrier
};

template <typename T,unsigned D>
void Simulation<T,D>::Gamma1D(int NRandomV, int NDisorder, int N_moments,
    std::vector<std::vector<unsigned>> indices, std::string name_dataset){
  std::cout << "got to line " << __LINE__ << " in file " << __FILE__ << "\n" << std::flush;

  int num_velocities = 0;
  for(int i = 0; i < int(indices.size()); i++)
    num_velocities += indices.at(i).size();
  int factor = 1 - (num_velocities % 2)*2;
  std::cout << "got to line " << __LINE__ << " in file " << __FILE__ << "\n" << std::flush;
    
  // Initialize the KPM vectors that will be needed to run the 1D Gamma matrix
  KPM_Vector<T,D> kpm0(1, *this);
  KPM_Vector<T,D> kpm1(2, *this);
		
  // Make sure the local gamma matrix is zeroed
  Eigen::Array<T, -1, -1> gamma = Eigen::Array<T, -1, -1 >::Zero(1, N_moments);
  Eigen::Matrix<T, 1, 2> tmp =  Eigen::Matrix < T, 1, 2> ::Zero();		

  long average = 0;
  for(int disorder = 0; disorder < NDisorder; disorder++){
    h.generate_disorder();

    for(unsigned it = 0; it < indices.size(); it++){
      h.build_velocity(indices.at(it), it);
    }

    for(int randV = 0; randV < NRandomV; randV++){
        
      kpm0.initiate_vector();			// original random vector
  std::cout << "got to line " << __LINE__ << " in file " << __FILE__ << "\n" << std::flush;
      kpm1.set_index(0);
      kpm1.v.col(0) = kpm0.v.col(0);
      kpm1.Exchange_Boundaries();

      if(indices.size() != 0)
        generalized_velocity(&kpm1, &kpm0, indices, 0);

      kpm0.v.col(0) = factor*kpm0.v.col(0); // This factor is due to the fact that this Velocity operator is not self-adjoint
      kpm0.empty_ghosts(0);

			
  std::cout << "got to line " << __LINE__ << " in file " << __FILE__ << "\n" << std::flush;
      kpm1.template Multiply<0>();		
  std::cout << "got to line " << __LINE__ << " in file " << __FILE__ << "\n" << std::flush;
      tmp.setZero();
  std::cout << "got to line " << __LINE__ << " in file " << __FILE__ << "\n" << std::flush;
      for(std::size_t ii = 0; ii < r.Sized ; ii += r.Ld[0])
        tmp += kpm0.v.block(ii,0, r.Ld[0], 1).adjoint() * kpm1.v.block(ii, 0, r.Ld[0], 2);
  std::cout << "got to line " << __LINE__ << " in file " << __FILE__ << "\n" << std::flush;

      gamma.matrix().block(0,0,1,2) += (tmp - gamma.matrix().block(0,0,1,2))/value_type(average + 1);			
  std::cout << "got to line " << __LINE__ << " in file " << __FILE__ << "\n" << std::flush;
	
      for(int m = 2; m < N_moments; m += 2){
        kpm1.template Multiply<1>();
        kpm1.template Multiply<1>();
        tmp.setZero();
        for(std::size_t ii = 0; ii < r.Sized ; ii += r.Ld[0])
          tmp += kpm0.v.block(ii,0, r.Ld[0], 1).adjoint() * kpm1.v.block(ii, 0, r.Ld[0], 2);

        gamma.matrix().block(0, m,1,2) += (tmp - gamma.matrix().block(0,m,1,2))/value_type(average + 1);

      }
  std::cout << "got to line " << __LINE__ << " in file " << __FILE__ << "\n" << std::flush;

      average++;
    }
  } 

  std::cout << "got to line " << __LINE__ << " in file " << __FILE__ << "\n" << std::flush;
  store_gamma1D(&gamma, name_dataset);
}

template <typename T,unsigned D>
void Simulation<T,D>::GammaGeneral(int NRandomV, int NDisorder, std::vector<int> N_moments,
                                   std::vector<std::vector<unsigned>> indices, std::string name_dataset){
    
  int dim = indices.size();
		
  // Check if the dimensions match
  if(dim != int(N_moments.size())){
    std::cout << "Dimension of the Gamma matrix does not match the number of chebyshev moments. Aborting.\n";
    exit(1);
  }
			
  // Determine the size of the gamma matrix we want to calculate
  int size_gamma = 1;
  for(int i = 0; i < dim; i++){
    if(N_moments.at(i) % 2 != 0){
      std::cout << "The number of moments must be an even number, due to limitations of the program. Aborting\n";
      exit(1);
    }
    size_gamma *= N_moments.at(i);
  }
		
		
  // Initialize the KPM vectors that will be needed to run the program 
  std::vector<KPM_Vector<T,D>*> kpm_vector(dim+1);
  kpm_vector.at(0) = new KPM_Vector<T,D> (1, *this);
  for(int i = 0; i < dim; i++)
    kpm_vector.at(i+1) = new KPM_Vector<T,D> (2, *this);
		
		
  // Define some pointers to make the code easier to read
  KPM_Vector<T,D> *kpm0 = kpm_vector.at(0);
  KPM_Vector<T,D> *kpm1 = kpm_vector.at(1);
			
  // Make sure the local gamma matrix is zeroed
  Eigen::Array<T, -1, -1> gamma = Eigen::Array<T, -1, -1 >::Zero(1, size_gamma);

  long average = 0;
  for(int disorder = 0; disorder < NDisorder; disorder++){
    h.generate_disorder();
    for(unsigned it = 0; it < indices.size(); it++)
      h.build_velocity(indices.at(it), it);

    for(int randV = 0; randV < NRandomV; randV++){
        
      kpm0->initiate_vector();			// original random vector
      kpm1->set_index(0);
      kpm1->v.col(0) = kpm0->v.col(0);
      kpm1->Exchange_Boundaries();

      // replace <0| by  <0|v. Note that v is not self-adjoint in this formulation
      generalized_velocity(kpm0, kpm1, indices, 0);
      int factor = 1 - (indices.at(0).size() % 2)*2;		
      kpm0->v.col(0) = factor*kpm0->v.col(0); // This factor is due to the fact that this Velocity operator is not self-adjoint

      kpm0->empty_ghosts(0);
      long index_gamma = 0;
      recursive_KPM(1, dim, N_moments, &average, &index_gamma, indices, &kpm_vector, &gamma);
      average++;
    }
  } 
		
		
  store_gamma(&gamma, N_moments, indices, name_dataset);
		
  // delete the kpm_vector
  delete kpm_vector.at(0);
  for(int i = 0; i < dim; i++)
    delete kpm_vector.at(i+1);
	
}

template <typename T,unsigned D>
void Simulation<T,D>::store_gamma1D(Eigen::Array<T, -1, -1> *gamma, 
                                  std::string name_dataset){
  debug_message("Entered store_gamma\n");
  // The whole purpose of this function is to take the Gamma matrix calculated by



  long int size_gamma = gamma->cols();
#pragma omp master
  Global.general_gamma = Eigen::Array<T, -1, -1 > :: Zero(1, size_gamma);
#pragma omp barrier
#pragma omp critical
  Global.general_gamma += *gamma;
#pragma omp barrier

    
#pragma omp master
  {
    H5::H5File * file = new H5::H5File(name, H5F_ACC_RDWR);
    write_hdf5(Global.general_gamma, file, name_dataset);
    delete file;
  }
#pragma omp barrier    

    
  debug_message("Left store_gamma\n");
}


template <typename T,unsigned D>
void Simulation<T,D>::store_gamma(Eigen::Array<T, -1, -1> *gamma, std::vector<int> N_moments, 
                                  std::vector<std::vector<unsigned>> indices, std::string name_dataset){
  debug_message("Entered store_gamma\n");
  // The whole purpose of this function is to take the Gamma matrix calculated by



  long int size_gamma = gamma->cols();
  int dim = indices.size();

		
  // Number of commutators inside the Gamma matrix. 
  // V^{x}  = [x,H]		-> one commutator
  // V^{xy} = [x,[y,H]]	-> two commutators
  // This is important because the commutator is anti-hermitian. So, an odd number of commutators
  int num_velocities = 0;
  for(int i = 0; i < int(indices.size()); i++)
    num_velocities += indices.at(i).size();
  int factor = 1 - (num_velocities % 2)*2;
		
  switch(dim){
  case 2: {
    Eigen::Array<T,-1,-1> general_gamma = Eigen::Map<Eigen::Array<T,-1,-1>>(gamma->data(), N_moments.at(0), N_moments.at(1));
#pragma omp master
    Global.general_gamma = Eigen::Array<T, -1, -1 > :: Zero(N_moments.at(0), N_moments.at(1));
#pragma omp barrier
#pragma omp critical
    Global.general_gamma.matrix() += (general_gamma.matrix() + factor*general_gamma.matrix().adjoint())/2.0;
#pragma omp barrier
    break;
  }
  case 1: {
    Eigen::Array<T,-1,-1> general_gamma = Eigen::Map<Eigen::Array<T,-1,-1>>(gamma->data(), 1, size_gamma);
#pragma omp master
    Global.general_gamma = Eigen::Array<T, -1, -1 > :: Zero(1, size_gamma);
#pragma omp barrier
#pragma omp critical
    Global.general_gamma += general_gamma;
#pragma omp barrier
    break;
  }
  default:
    std::cout << "You're trying to store a matrix that is not expected by the program. Exiting.\n";
    exit(1);
  }
    

    
#pragma omp master
  {
    H5::H5File * file = new H5::H5File(name, H5F_ACC_RDWR);
    write_hdf5(Global.general_gamma, file, name_dataset);
    delete file;
  }
#pragma omp barrier    

    
  debug_message("Left store_gamma\n");
}

template <typename T,unsigned D>
void Simulation<T,D>::store_gamma3D(Eigen::Array<T, -1, -1> *gamma, std::vector<int> N_moments, 
                                    std::vector<std::vector<unsigned>> indices, std::string name_dataset){
  debug_message("Entered store_gamma3d\n");
  // The whole purpose of this function is to take the Gamma matrix calculated by
  // Gamma3D, check if there are any symmetries among the 
  // matrix elements and then store the matrix in an HDF file.
    
  int dim = indices.size();

		
  // Number of commutators inside the Gamma matrix. 
  // V^{x}  = [x,H]		-> one commutator
  // V^{xy} = [x,[y,H]]	-> two commutators
  // This is important because the commutator is anti-hermitian. So, an odd number of commutators
  // means that the conjugate of the Gamma matrix has an overall minus sign
  int num_velocities = 0;
  for(int i = 0; i < int(indices.size()); i++)
    num_velocities += indices.at(i).size();
  int factor = 1 - (num_velocities % 2)*2;
  int N0 = N_moments.at(0);
  int N1 = N_moments.at(1);
  int N2 = N_moments.at(2);
  Eigen::Array<T,-1,-1> general_gamma;
  general_gamma = Eigen::Map<Eigen::Array<T,-1,-1>>(gamma->data(), N0*N1, N2);
  Eigen::Array<T,-1,-1> storage_gamma; 
  storage_gamma = Eigen::Array<T,-1,-1>::Zero(N0*N1, N2);
    
  switch(dim){
  case 3:{
    // Check if all the directions are the same. In this case, there are 
    // six symmetries that may be taken advantage of ('*' denotes complex conjugation)
    // G_nmp  = G_mpn = G_pnm 
    // G_nmp* = G_pmn = G_mnp = G_npm 
    if(indices.at(0) == indices.at(1) and indices.at(0) == indices.at(2)){
      for(int n = 0; n < N0; n++){
        for(int m = 0; m < N1; m++){
          for(int p = 0; p < N2; p++){
            storage_gamma(n + N0*m,p) += general_gamma(n + N0*m,p)/T(6.0);
            storage_gamma(n + N0*m,p) += general_gamma(m + N0*p,n)/T(6.0);
            storage_gamma(n + N0*m,p) += general_gamma(p + N0*n,m)/T(6.0);

            storage_gamma(n + N0*m,p) += T(factor/6.0)*myconj(general_gamma(p + N0*m,n));
            storage_gamma(n + N0*m,p) += T(factor/6.0)*myconj(general_gamma(n + N0*p,m));
            storage_gamma(n + N0*m,p) += T(factor/6.0)*myconj(general_gamma(m + N0*n,p));
          }
        }
      }
          
    } 
        
    // Now check if any two directions are the same
    // Check if the two first directions are the same but different from the third
    if(indices.at(0) == indices.at(1) and indices.at(0) != indices.at(2) and N1 == N2){
      for(int n = 0; n < N0; n++){
        for(int m = 0; m < N1; m++){
          for(int p = 0; p < N2; p++){
            storage_gamma(n + N0*m,p) += general_gamma(n + N0*m,p)/T(2.0);
            storage_gamma(n + N0*m,p) += T(factor/2.0)*myconj(general_gamma(n + N0*p,m));
          }
        }
      }
    }
        
    // Check if the first and last directions are the same but different from the second
    if(indices.at(0) == indices.at(2) and indices.at(0) != indices.at(1) and N0 == N2){
      for(int n = 0; n < N0; n++){
        for(int m = 0; m < N1; m++){
          for(int p = 0; p < N2; p++){
            storage_gamma(n + N0*m,p) += general_gamma(n + N0*m,p)/T(2.0);
            storage_gamma(n + N0*m,p) += T(factor/2.0)*myconj(general_gamma(m + N0*n,p));
          }
        }
      }
    }
        
    // Check if the last two directions are the same but different from the first
    if(indices.at(2) == indices.at(1) and indices.at(0) != indices.at(2) and N0 == N1){
      for(int n = 0; n < N0; n++){
        for(int m = 0; m < N1; m++){
          for(int p = 0; p < N2; p++){
            storage_gamma(n + N0*m,p) += general_gamma(n + N0*m,p)/T(2.0);
            storage_gamma(n + N0*m,p) += T(factor/2.0)*myconj(general_gamma(p + N0*m, n));
          }
        }
      }
    }
        
    // Check if all the directions are different
    if(indices.at(0) != indices.at(1) and indices.at(0) != indices.at(2) and indices.at(1) != indices.at(2)){
      storage_gamma += general_gamma;
    }

    break;
  }
  default:
    std::cout << "You're trying to store a matrix that is not expected by the program. Exiting.\n";
    exit(1);
  }
    
    
    
  H5::H5File * file = new H5::H5File(name, H5F_ACC_RDWR);
  write_hdf5(storage_gamma, file, name_dataset);
  delete file;

      
  debug_message("Left store_gamma\n");
};


template class Simulation<float ,1u>;
template class Simulation<double ,1u>;
template class Simulation<long double ,1u>;
template class Simulation<std::complex<float> ,1u>;
template class Simulation<std::complex<double> ,1u>;
template class Simulation<std::complex<long double> ,1u>;

template class Simulation<float ,3u>;
template class Simulation<double ,3u>;
template class Simulation<long double ,3u>;
template class Simulation<std::complex<float> ,3u>;
template class Simulation<std::complex<double> ,3u>;
template class Simulation<std::complex<long double> ,3u>;

template class Simulation<float ,2u>;
template class Simulation<double ,2u>;
template class Simulation<long double ,2u>;
template class Simulation<std::complex<float> ,2u>;
template class Simulation<std::complex<double> ,2u>;
template class Simulation<std::complex<long double> ,2u>;
 
