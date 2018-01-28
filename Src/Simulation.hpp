#ifndef _SIMULATION_HPP
#define _SIMULATION_HPP

#define DEBUG 0

int custom_find(int *arr, int arr_size, int value_to_search){
	/* This function searches array 'arr' for any occurence of number 'value to search'.
	 * If it exists, it exits and returns the index where it occurs.
	 * Otherwise, returns -1
	 */
	for(int i = 0; i < arr_size; i++){
		if(*(arr+i) == value_to_search)
			return i;
	}
	
	return -1;	
}


std::complex<double> green(int n, int sigma, std::complex<double> energy){
	const std::complex<double> i(0.0,1.0); 
	std::complex<double> sq = sqrt(1.0 - energy*energy);
	return pow(-1,n)*2.0*sigma/sq*i*exp(-sigma*n*1.0*acos(energy)*i);
}


template <typename T,unsigned D>
class GlobalSimulation {
private:
  GLOBAL_VARIABLES <T> Global;
  LatticeStructure <D> rglobal;
  
  
  // Regular quantities to calculate, such as DOS and CondXX
  std::vector <int> Quantities, NMoments, NRandomV, NDisorder; 
  
  // Other quantities that require special care, such as SingleShotXX
  std::vector <int> Quantities_special, NMoments_special, NRandomV_special, NDisorder_special, EnergyScale, MagneticField; 
  std::vector <double> gamma_special;
  Eigen::Array<double, -1, -1> singleshot_energies;
  
public:
  GlobalSimulation( char *name ) : rglobal(name) {
    Global.ghosts.resize( rglobal.get_BorderSize() );
    std::fill(Global.ghosts.begin(), Global.ghosts.end(), 0);
    
    /*
     *   /Calculation/FunctionNum:
     *
     *   DOS - denstity of states == 1,
     *   CondXX - conductivity in xx direction == 2,
     *   CondXY - conductivity in xy direction == 3,
     *   OptCond - optical conductivity == 4
     *   SpinCond - spin conductivity == 5

     * /Calculation/NumRandoms   : number of different random vector realisations,
     * /Calculation/NumMoments   : number of moments for the calculation,
     * /Calculation/NumDisorder  : number of disorder realisations.
     */
    
    // Regular quantities to calculate, such as DOS and CondXX
    H5::H5File * file         = new H5::H5File(name, H5F_ACC_RDONLY);
    H5::DataSet * dataset     = new H5::DataSet(file->openDataSet("/Calculation/FunctionNum"));
    H5::DataSpace * dataspace = new H5::DataSpace(dataset->getSpace());
    size_t NQuantities        = dataspace->getSimpleExtentNpoints();
    
    Quantities.resize (NQuantities);
    NMoments.resize   (NQuantities);
    NRandomV.resize   (NQuantities);
    NDisorder.resize  (NQuantities);
    EnergyScale.resize  (1);
    MagneticField.resize  (1);

    get_hdf5<int>(Quantities.data(), file, (char *)   "/Calculation/FunctionNum");
    get_hdf5<int>(NRandomV.data(),   file, (char *)   "/Calculation/NumRandoms");
    get_hdf5<int>(NMoments.data(),   file, (char *)   "/Calculation/NumMoments");
    get_hdf5<int>(NDisorder.data(),  file, (char *)   "/Calculation/NumDisorder");
    get_hdf5<int>(EnergyScale.data(),  file, (char *)   "/EnergyScale");
    MagneticField.at(0) = 0;
		try {
			H5::Exception::dontPrint();
			get_hdf5<int>(MagneticField.data(),  file, (char *)   "/Hamiltonian/MagneticField");
		}
		catch (H5::Exception& e){}
    
    delete dataspace;
    delete dataset;
    delete file;
    
    // What quantities from this list do we need to calculate? Let's find out
    int DOS 	 = custom_find(Quantities.data(), NQuantities, 1);
    int CondXX = custom_find(Quantities.data(), NQuantities, 2);
    int CondXY = custom_find(Quantities.data(), NQuantities, 3);

   
      
    
	// Other quantities that require special care, such as SingleShotXX
	int SingleShotXX = -1;
	int SingleShotXY = -1;
	H5::H5File * file_special	= new H5::H5File(name, H5F_ACC_RDONLY);
	
	try{
		if(DEBUG)std::cout << "start try\n";fflush(stdout);
		H5::Exception::dontPrint();
		
		// This is here just to determine the number of quantities we need to calculate
		H5::DataSet * dataset_special     	= new H5::DataSet(file_special->openDataSet("/Calculation/Calculation_spec/FunctionNum"));
		H5::DataSpace * dataspace_special 	= new H5::DataSpace(dataset_special->getSpace());
		size_t NQuantities_special  				= dataspace_special->getSimpleExtentNpoints();
		delete dataspace_special;
		delete dataset_special;
		
		Quantities_special.resize (NQuantities_special);
		NMoments_special.resize   (NQuantities_special);
		NRandomV_special.resize   (NQuantities_special);
		NDisorder_special.resize  (NQuantities_special);
		gamma_special.resize 	  (NQuantities_special);
		
		
		
		
		// We also need to determine the number of energies that we need to calculate
		H5::DataSet * dataset_energy     	= new H5::DataSet(file_special->openDataSet("/Calculation/Calculation_spec/Energy"));
		H5::DataSpace * dataspace_energy 	= new H5::DataSpace(dataset_energy->getSpace());
		hsize_t dims_out[2];		
		dataspace_energy->getSimpleExtentDims(dims_out, NULL);	
		singleshot_energies = Eigen::Array<double, -1, -1>::Zero(dims_out[0], dims_out[1]);	
		delete dataspace_energy;
		delete dataset_energy;
			
			
			
			// Now let's fetch those quantities
			get_hdf5<int>(Quantities_special.data(),	file, (char *)   "/Calculation/Calculation_spec/FunctionNum");
			get_hdf5<int>(NRandomV_special.data(),  	file, (char *)   "/Calculation/Calculation_spec/NumRandoms");
			get_hdf5<int>(NMoments_special.data(),  	file, (char *)   "/Calculation/Calculation_spec/NumMoments");
			get_hdf5<int>(NDisorder_special.data(), 	file, (char *)   "/Calculation/Calculation_spec/NumDisorder");
			get_hdf5<double>(gamma_special.data(),  	file, (char *)   "/Calculation/Calculation_spec/Gamma");
			get_hdf5<double>(singleshot_energies.data(),  	file, (char *)   "/Calculation/Calculation_spec/Energy");
			
			// Make sure the moments are a power of 2
			for(unsigned i = 0; i < NMoments_special.size(); i++)
				NMoments_special.at(i) = 2*(NMoments_special.at(i)/2);

			
			
			SingleShotXX = custom_find(Quantities_special.data(), NQuantities_special, 6);
			SingleShotXY = custom_find(Quantities_special.data(), NQuantities_special, 7);
			if(DEBUG)std::cout << "ended try\n";fflush(stdout);
    }
    catch(H5::Exception& e) {
			if(DEBUG)std::cout << "exception \n";fflush(stdout);
    }
    
		delete file_special;
		
		int CondXXX = 0;
		int hBN = 1;
		
		bool GammaXiX 	= CondXX != -1;
		bool GammaXX	= CondXX != -1;
		bool GammaXiY	= CondXY != -1;
		bool GammaXY	= CondXY != -1;
		bool Gamma		= DOS != -1;
		bool GammaXXiX	= CondXXX != -1 or hBN != -1;
		bool GammaXiXX	= CondXXX != -1 or hBN != -1;
		
		std::cout << GammaXY << " " << GammaXiY << " ";
		
		int NDisorderhBN = NDisorder.at(CondXX);
		int NRandomhBN = NRandomV.at(CondXX);
		int NMomentshBN = NMoments.at(CondXX);
		
		
    omp_set_num_threads(rglobal.n_threads);
#pragma omp parallel default(shared)
    {
		
		
      
		Simulation<T,D> simul(name, Global);
		
		#pragma omp master
		{
		Global.kpm_iteration_time = simul.time_kpm(100);
		std::cout << "kpm iteration time: " << Global.kpm_iteration_time << "\n" << std::flush;
		
		
		
		
		}
		#pragma omp barrier
	
		//double calc_time = size_gamma*Global.kpm_iteration_time*NRandomV*NDisorder;
		//std::cout << "This function will take around " << calc_time << " seconds.\n" << std::flush;
		
		
		
      if(SingleShotXX != -1){
				if(DEBUG)std::cout << "calculating of singleshotxx\n";fflush(stdout);
				Global.singleshot_cond = Eigen::Matrix<T, Eigen::Dynamic, Eigen::Dynamic > :: Zero(1, singleshot_energies.cols());
				simul.Single_Shot(EnergyScale.at(0), NRandomV_special.at(SingleShotXX), NDisorder_special.at(SingleShotXX), NMoments_special.at(SingleShotXX), singleshot_energies.row(SingleShotXX), gamma_special.at(SingleShotXX), "x,x", "SingleShotXX");
				
				if(DEBUG)std::cout << "ended singleshotxx\n";fflush(stdout);
				
			}
       
      if(SingleShotXY != -1){
				if(DEBUG)std::cout << "calculating of singleshotxy\n";fflush(stdout);
				Global.singleshot_cond = Eigen::Matrix<T, Eigen::Dynamic, Eigen::Dynamic > :: Zero(1, singleshot_energies.cols());
				simul.Single_Shot(EnergyScale.at(0), NRandomV_special.at(SingleShotXY), NDisorder_special.at(SingleShotXY), NMoments_special.at(SingleShotXY), singleshot_energies.row(SingleShotXY), gamma_special.at(SingleShotXY), "x,y", "SingleShotXY");
				if(DEBUG)std::cout << "ended singleshotxx\n";fflush(stdout);
				
			}
			
		/*if(Gamma) 	  simul.Measure_Gamma(NRandomV.at(DOS), NDisorder.at(DOS), {NMoments.at(DOS)}, "", "MU");			
		
		if(GammaXX)   simul.Measure_Gamma(NRandomV.at(CondXX), NDisorder.at(CondXX), {NMoments.at(CondXX)}, "xx", "LambdaXX");
		if(GammaXiX)  simul.Measure_Gamma(NRandomV.at(CondXX), NDisorder.at(CondXX), {NMoments.at(CondXX), NMoments.at(CondXX)}, "x,x", "GammaXX");*/
		
		if(GammaXXiX) simul.Measure_Gamma(NRandomhBN, NDisorderhBN, {NMomentshBN, NMomentshBN}, "xx,x", "GammaXXiX");
		if(GammaXiXX) simul.Measure_Gamma(NRandomhBN, NDisorderhBN, {NMomentshBN, NMomentshBN}, "x,xx", "GammaXiXX");
		if(GammaXY)   simul.Measure_Gamma(NRandomV.at(CondXY), NDisorder.at(CondXY), {NMoments.at(CondXY)}, "xy", "LambdaXY");
		if(GammaXiY)  simul.Measure_Gamma(NRandomV.at(CondXY), NDisorder.at(CondXY), {NMoments.at(CondXY), NMoments.at(CondXY)}, "x,y", "GammaXY");
		
			
			
    }
    
  };

  
};
#endif


template <typename T,unsigned D>
class Simulation  {
public:
  KPMRandom <T>          rnd;
  std::vector<T>         ghosts;
  LatticeStructure <D>   r;      
  GLOBAL_VARIABLES <T> & Global;
  char                 * name;
  Hamiltonian<T,D>       h;
  Simulation(char *filename, GLOBAL_VARIABLES <T> & Global1): r(filename),  Global(Global1), name(filename), h(*this)  {
    rnd.init_random();
    ghosts.resize(Global.ghosts.size()/r.n_threads);
  };
  
  
  void Measure_Dos(int & NRandomV, int & NDisorder) {
    typedef typename extract_value_type<T>::value_type value_type;
    Eigen::Array<T, Eigen::Dynamic, Eigen::Dynamic> mu = Eigen::Array<T, Eigen::Dynamic, Eigen::Dynamic > :: Zero(Global.mu.rows(), Global.mu.cols());
    KPM_Vector<T,D>  phi0(1, *this);
    KPM_Vector<T,D>  phi (2, *this);

    //    phi0.test_boundaries_system();

#pragma omp barrier
    long average = 0;

    for(int disorder = 0; disorder <  NDisorder; disorder++)
      {
	h.generate_disorder();
	for(int randV = 0; randV < NRandomV; randV++)
	  {
	    phi0.initiate_vector();
	    phi.set_index(0);
	    phi.v.col(0) = phi0.v.col(0);
	    phi.Exchange_Boundaries();
	    
	    phi.template Multiply<0>();
	    mu.matrix().block(0,0,1,2) +=  (phi0.v.adjoint() * phi.v - mu.matrix().block(0,0,1,2))/value_type(average + 1);
	    
	    for(int m = 2; m < mu.cols(); m += 2)
	      {	    
		phi.template Multiply<1>();
		phi.template Multiply<1>();
		mu.matrix().block(0,m,1,2) +=  (phi0.v.adjoint() * phi.v - mu.matrix().block(0,m,1,2))/value_type(average + 1);
	      }
	    average++;
	  }
	  
	  if(DEBUG)std::cout << "Finished chb iteration in DOS.\n";fflush(stdout);
	  
	  
	  
	  
	  

#pragma omp critical
	Global.mu += mu;
#pragma omp barrier
	
	
#pragma omp master
	{
		if(DEBUG)std::cout << "before creating file with name: " << name << "\n";fflush(stdout);
	  H5::H5File * file1 = new H5::H5File(name, H5F_ACC_RDWR);
	  if(DEBUG)std::cout << "before write to file\n";fflush(stdout);
	  write_hdf5(Global.mu, file1, "MU");
	  if(DEBUG)std::cout << "before delete file\n";fflush(stdout);
	  delete file1;
	  Global.mu.setZero();
	}
#pragma omp barrier	
      }
#pragma omp barrier	

	if(DEBUG)std::cout << "Left calculation of DOS\n";fflush(stdout);
  }
  
  
  
  void Measure_Cond(int & NRandomV, int & NDisorder, std::string indices, std::string name_dataset) {
		/*
		 * Calculate the gamma matrix gammaxx = Tr[v^x T_n v^x T_m] 
		 * used to calculate the longitudinal conductivity
		 */
		 
		// Process the indices
		if(DEBUG)std::cout << "Calculating cond\n";
		std::vector<int> first_indices, second_indices;
		
		int comma_location = indices.find_first_of(',');
	
		std::string first_string, second_string;
		first_string = indices.substr(0, comma_location);
		second_string = indices.substr(comma_location+1);		
		first_indices.resize(first_string.size()); 
		second_indices.resize(second_string.size());
		
		if(DEBUG)std::cout << "strings: " << first_string << " "<< second_string << "\n";
		
		for(unsigned int i = 0; i < first_string.size(); i++){
			if(first_string[i]=='y')
				first_indices.at(i) = 1;
			else
				first_indices.at(i) = 0;
		}
		
		for(unsigned  int i = 0; i < second_string.size(); i++){
			if(second_string[i]=='y')
				second_indices.at(i) = 1;
			else
				second_indices.at(i) = 0;
		}
			/*
		for(unsigned  int i = 0; i < first_string.size(); i++)
			std::cout << "first_indices: " << first_indices.at(i) << "\n";
			
		for(unsigned  int i = 0; i < second_string.size(); i++)
			std::cout << "second_indices: " << second_indices.at(i) << "\n";
		*/
		
		
		//Done processing the indices
		
		
		
		
		 
		
    typedef typename extract_value_type<T>::value_type value_type;
    KPM_Vector<T,D>  phi0(1, *this);
    KPM_Vector<T,D> phi_n(2, *this);
    KPM_Vector<T,D> phi_m(2, *this);
		
		//make sure the local gamma matrix is zeroed
		Eigen::Array<T, -1, -1> gamma = Eigen::Array<T, -1, -1 > :: Zero(Global.gamma.rows(), Global.gamma.cols());
		//gamma.setZero();
		
		
		/* We want to calculate <0|vmvn|0>
		 * Define |n> = n|0> and store it. 
		 * After having |n> stored, define |n'> = v |n>, which will act as the new |0> for m
		 * Now, having |n'>, define |m> = m |n'>. These may all be calculated using 
		 * Chebyshev's recursion relations. So, for a fixed |n>, we have found all the |m>
		 * Since |m> = m v n |0>, what remains is to do the dot product <0|v|m>, which
		 * gives us the Gamma-matrix-element we sought. After this, we go back to |n>. Using 
		 * the recursion relations, we may find the next |n+1>, and repeat the process all over again
		 * */
		
		int N_cheb_moments = gamma.cols(); //assuming cols=rows
		//std::cout << "calculating vmvn\n";fflush(stdout);
	
    long average = 0;
    for(int disorder = 0; disorder < NDisorder; disorder++){
			h.generate_disorder();
			for(int randV = 0; randV < NRandomV; randV++){
				
				phi0.initiate_vector();					
				phi_n.set_index(0);
				phi_n.v.col(0) = phi0.v.col(0); 
				phi_n.Exchange_Boundaries(); 	
				//phi_n.Velocity(phi0.v.col(0).data(), phi_n.v.col(phi_n.get_index()).data(), 0);
				//replace |phi0> by v |phi0>
				
				
				// DONT FORGET V IS NOT HERMITIAN, so multiplication by <n| gives a minus sign
				if(first_indices.size() == 1){
					//std::cout << indices << "first index has 1\n";
					phi_n.Velocity(phi0.v.col(0).data(), phi_n.v.col(phi_n.get_index()).data(), first_indices.at(0));
					phi0.v.col(0) = -phi0.v.col(0); // compensating the fact that V is anti-hermitian
				}
				
				if(first_indices.size() == 2){
					//std::cout << indices << "first index has 2\n";
					phi_n.Velocity2(phi0.v.col(0).data(), phi_n.v.col(phi_n.get_index()).data(), first_indices.at(0), first_indices.at(1));
					//this one is hermitian, no problem here
				}
				
				phi0.empty_ghosts(0);
				
				
				// actually we should have multiplied by the adjoint of the velocity. 
				// Since we forgot the "i" in V, adjoint(Velocity) = -Velocity
				// The only difference is an overall minus sign
				
				
				for(int n = 0; n < N_cheb_moments; n += 1){
					phi_m.set_index(0);
					
					if(second_indices.size() == 1){
						//std::cout << indices <<"second index has 1\n";
						phi_n.Velocity(phi_m.v.col(phi_m.get_index()).data(), phi_n.v.col(phi_n.get_index()).data(), second_indices.at(0)); 
					}
					
					if(second_indices.size() == 2){
						//std::cout << indices << "second index has 2\n";
						phi_n.Velocity2(phi_m.v.col(phi_m.get_index()).data(), phi_n.v.col(phi_n.get_index()).data(), second_indices.at(0), second_indices.at(1)); 
					}
					
					phi_m.Exchange_Boundaries(); 
					phi_m.template Multiply<0>();					
					gamma.matrix().block(n,0,1,2) += (phi0.v.adjoint() * phi_m.v - gamma.matrix().block(n,0,1,2))/value_type(average + 1);
					//std::cout << "(" << n << " " << 0 << ")\t" << gamma.matrix().block(n,0,1,2) << "\n";
					
					
					for(int m = 2; m < N_cheb_moments; m += 2)
					{
						phi_m.template Multiply<1>();
						phi_m.template Multiply<1>();
						
						gamma.matrix().block(n,m,1,2) += (phi0.v.adjoint() * phi_m.v - gamma.matrix().block(n,m,1,2))/value_type(average + 1);
						//std::cout << "(" << n << " " << m << ")\t" << gamma.matrix().block(n,m,1,2) << "\n";
					}
					
					// all done with |m>, now we return to |n>
					
					if(n == 0)
						phi_n.template Multiply<0>(); //first cheb iteration, multiply by the hamiltonian
					else if(n < N_cheb_moments - 1)
						phi_n.template Multiply<1>(); 
				}
				average++;
			}
		}
		
		
		// the gamma matrix has been calculated. Now we're going to use the 
		// property that gamma is hermitian: gamma_nm=gamma_mn*
	
		
#pragma omp critical

		//std::cout << "IMPORTANT ! ! !:\n V is not hermitian. Make sure you take this into account\n";
		// in this case there's no problem. both V are anti-hermitic, so the minus signs cancel
		if(first_indices.size()==1 && second_indices.size()==1)
			Global.gamma.matrix() += (gamma.matrix() + gamma.matrix().adjoint())/2.0;
			
		// not here, though
		else
			Global.gamma.matrix() += (gamma.matrix() - gamma.matrix().adjoint())/2.0;
		
#pragma omp barrier

    
#pragma omp master
    {
      H5::H5File * file = new H5::H5File(name, H5F_ACC_RDWR);
			write_hdf5(Global.gamma, file, name_dataset);
      delete file;
      
      // make sure the global matrix is zeroed
      Global.gamma.setZero();
    }
#pragma omp barrier
  }

	void Measure_Gamma(int NRandomV, int NDisorder, std::vector<int> N_moments, std::string indices_string, std::string name_dataset) {
		if(DEBUG) std::cout << "Entered Measure_Gamma.\n" << std::flush;
		/* Calculates the Gamma matrix of parameters given by 'indices_string'. These matrices
		are used to calculate various properties of the quantum system, such as the density
		of states and the optical conductivity. The Gamma matrix is a multi-dimensional matrix 
		defined by:
		
			Gamma{i1, i2, ... , iN}(n1, n2, ..., nN) = < v^i1  T_n1(H)  v^i2  T_n2(H) ... v^iN  T_nN(H) >
			
		The first argument is the parameters and the second argument is the matrix indices. Here's 
		a quick rundown of what each of these objects means:
		 
			T_n(H) is the n-th order Chebyshev polynomial of the Hamiltonian matrix H
			
		Note that each i in the parameters actually stands for a set of letters, such as x, or xx, or xyyxxy.
		Unwinding those, v^{ij...mn} represents the  nested commutator of the position operator:
		
			v^{x} = [x,H],  v^{xy} = [x,[y,H]],  v^{yyy} = [y,[y,[y,H]]],  etc...
			
		Note that these velocity operators do not have the imaginary number in their definition, so they are not
		hermitian. When the parameter of v is empty, it is treated as the identity operator: v^{} = 1.		
		Some valid parameters for the Gamma matrix are: 
		
			""  		->  		   G^{}(n) = < Tn(H) > 
			"x"			->			  G^{x}(n) = < v^x  Tn(H) >
			"xyyyxyx"	->		G^{xyyyxyx}(n) = < v^xyyyxyx  Tn(H) >
			"xy,y"		->		 G^{xy,y}(n,m) = < v^x  Tn(H)  v^y  Tm(H) >
			","			->			G^{,}(n,m) = < Tn(H)  Tm(H) >
			"y,,y,"		->	G^{y,,y,}(n,m,p,q) = < v^y  Tn(H)  Tm(H)  v^y  Tp(H)  Tq(H) >
			etc...		->	etc...
		
		These parameters should NOT contain anything else other than the characters ',', 'x' and 'y',
		not even whitespace characters. The dimension of the Gamma matrix is the number of commas + 1 */
		
		
		
		
		// First of all, we need to process the indices_string into something the program can use
		// Each element of this vector is a list of the indices of a generalized velocity operator
		std::vector<std::vector<int>> indices = process_string(indices_string);
		int dim = indices.size();
		
		if(DEBUG){
			std::cout << "\nIndices:\n";
			for(unsigned i = 0; i < indices.size(); i++){
				for(unsigned j = 0; j < indices.at(i).size(); j++){
					std::cout << indices.at(i).at(j) << "\t";
				}
				std::cout << "\n";
			}
			std::cout << "Gamma matrix dimension: " << dim << "\n";
			
			
			std::cout << "Number of moments: \n";
			for(unsigned i = 0; i < N_moments.size(); i++){
				std::cout << N_moments.at(i) << "\n";
			}
			std::cout << "N_moments size: " << N_moments.size() << "\n";
		}
		
		// Check if the dimensions match
		if(dim != int(N_moments.size())){
			std::cout << "Dimension of the Gamma matrix does not match the number of chebyshev moments. Aborting.\n";
			exit(0);
		}
			
		// Determine the size of the gamma matrix we want to calculate
		int size_gamma = 1;
		for(int i = 0; i < dim; i++){
			if(N_moments.at(i) % 2 != 0){
				std::cout << "The number of moments must be an even number, due to limitations of the program. Aborting\n";
				exit(0);
			}
			size_gamma *= N_moments.at(i);
		}
		
		// Estimate of the time it'll take to run this function
		
		
		
		
		
		// Initialize the KPM vectors that will be needed to run the program 
		std::vector<KPM_Vector<T,D>> kpm_vector;
		kpm_vector.push_back(KPM_Vector<T,D> (1, *this));
		for(int i = 0; i < dim; i++)
			kpm_vector.push_back(KPM_Vector<T,D> (2, *this));
		
		
		
		// Define some pointers to make the code easier to read
		KPM_Vector<T,D> *kpm0 = &kpm_vector.at(0);
		KPM_Vector<T,D> *kpm1 = &kpm_vector.at(1);
		T * kpm0data = kpm0->v.col(0).data();
		T * kpm1data = kpm1->v.col(kpm1->get_index()).data();
		int axis0, axis1;
			
			
			
		// Make sure the local gamma matrix is zeroed
		Eigen::Array<T, -1, -1> gamma = Eigen::Array<T, -1, -1 >::Zero(1, size_gamma);
		
		long average = 0;
		for(int disorder = 0; disorder < NDisorder; disorder++){
			h.generate_disorder();
			for(int randV = 0; randV < NRandomV; randV++){
				
				kpm0->initiate_vector();			// original random vector
				kpm1->set_index(0);
				kpm1->v.col(0) = kpm0->v.col(0);
				kpm1->Exchange_Boundaries();
				
				// Check which generalized velocity operator needs to be calculated. 
				// This replaces the original random vector |0> by v|0> 
				if(DEBUG)std::cout << "First multiplication by the Velocity.\n";
				switch(indices.at(0).size()){
					case 0:
						if(DEBUG)std::cout << "case 0\n";
						break;
					case 1:
						
						if(DEBUG)std::cout << "case 1\n";
						axis0 = indices.at(0).at(0);
						kpm0->Velocity(kpm0data, kpm1data, axis0);  
						kpm0->empty_ghosts(0);
						kpm0->v.col(0) = -kpm0->v.col(0); // This minus sign is due to the fact that this Velocity operator is not self-adjoint
						
						
						break;
					
					case 2:
						if(DEBUG)std::cout << "case 2\n";
						axis0 = indices.at(0).at(0);
						axis1 = indices.at(0).at(1);
						
						kpm0->Velocity2(kpm0data, kpm1data, axis0, axis1);  
						kpm0->empty_ghosts(0);
						break;
						
					case 3:
						std::cout << "The matrix you're trying to calculate requires an operator that is not yet implemented: Velocity3.\n";
						exit(0);
						
					default:
						std::cout << "The matrix you're trying to calculate requires an operator that is not yet implemented.\n";
						exit(0);
				
				}
					
				long index_gamma = 0;
				recursive_KPM(1, dim, N_moments, &average, &index_gamma, indices, &kpm_vector, &gamma);
				
				
				average++;
			}
		} 
		
		
		store_gamma(&gamma, N_moments, indices, name_dataset);
		
		
		if(DEBUG)std::cout << "Left Measure_Gamma.\n" << std::flush;
  }
	
	void recursive_KPM(int depth, int max_depth, std::vector<int> N_moments, long *average, long *index_gamma, std::vector<std::vector<int>> indices, std::vector<KPM_Vector<T,D>> *kpm_vector, Eigen::Array<T, -1, -1> *gamma){
		typedef typename extract_value_type<T>::value_type value_type;
		
		
		if(depth != max_depth){
			KPM_Vector<T,D> *kpm1 = &kpm_vector->at(depth);
			KPM_Vector<T,D> *kpm2 = &kpm_vector->at(depth + 1);
			
			T * kpm1data;
			T * kpm2data;
			int axis1, axis2;
			
			//std::cout << "first branch. Depth: " << depth << "\n" << std::flush;
			
			
			for(int p = 0; p < N_moments.at(depth - 1); p++){
				kpm2->set_index(0);
				switch(indices.at(depth).size()){
					case 0:
						//std::cout << "case0\n";
						break;
					case 1:
						//std::cout << "case1\n";
						axis1 = indices.at(depth).at(0);
						kpm1data = kpm1->v.col(kpm1->get_index()).data();
						kpm2data = kpm2->v.col(kpm2->get_index()).data();
						
						//std::cout << "indices.at(" << depth << "): " << axis1 << "\n";
						kpm2->Velocity(kpm2data, kpm1data, axis1); 
						
						break;
						
					case 2:
						//std::cout << "case2\n";
						axis1 = indices.at(depth).at(0);
						axis2 = indices.at(depth).at(1);
						kpm1data = kpm1->v.col(kpm1->get_index()).data();
						kpm2data = kpm2->v.col(kpm2->get_index()).data();
						
						kpm2->Velocity2(kpm2data, kpm1data, axis1, axis2); 
						
						break;
						
					default:
						//std::cout << "The matrix you're trying to calculate requires an operator that is not yet implemented.\n";
						exit(0);
						
				}
				
				
				recursive_KPM(depth + 1, max_depth, N_moments, average, index_gamma, indices, kpm_vector, gamma);
				//std::cout << "left second branch\n";
				if(p == 0){
					//std::cout << "p=0\n";
					kpm1->template Multiply<0>(); 
				}
				else if(p < N_moments.at(depth-1) - 1){
					//std::cout << "p!=0\n";
					kpm1->template Multiply<1>(); 
				}
			
			}
			
		} else {
			KPM_Vector<T,D> *kpm0 = &kpm_vector->at(0);
			KPM_Vector<T,D> *kpm1 = &kpm_vector->at(depth);
			
			//std::cout << "second branch. Depth: " << depth << "\n" << std::flush;
			kpm1->template Multiply<0>();			
			gamma->matrix().block(0,*index_gamma,1,2) += (kpm0->v.adjoint() * kpm1->v - gamma->matrix().block(0,*index_gamma,1,2))/value_type(*average + 1);			
			*index_gamma += 2;
			
			for(int m = 2; m < N_moments.at(depth - 1); m += 2)
			{
				kpm1->template Multiply<1>();
				kpm1->template Multiply<1>();
				gamma->matrix().block(0, *index_gamma,1,2) += (kpm0->v.adjoint() * kpm1->v - gamma->matrix().block(0,*index_gamma,1,2))/value_type(*average + 1);
				//std::cout << "product: " << kpm0->v.adjoint() * kpm1->v << "\n";
				
				*index_gamma += 2;
			}
			
		}
	}
	
	
	std::vector<std::vector<int>> process_string(std::string indices_string){
		// First of all, split the indices string by commas ','
		std::vector<std::string> strings;
		int end_pos = 0;
		while(end_pos != -1){
			end_pos = indices_string.find(',');
			strings.push_back(indices_string.substr(0, end_pos));
			indices_string = indices_string.substr(end_pos + 1, indices_string.size() - end_pos - 1);
		}
		
		int dim = strings.size();
		/*
		for(int i = 0; i < dim; i++)
			std::cout << strings.at(i) << "\n";*/
		
		
		
		
		
		std::vector<std::vector<int>> indices;
		
		for(int i = 0; i < dim; i++){
			
			int len_str = strings.at(i).size();
			int single_digit;
			std::vector<int> temp;
			
			for(int j = 0; j < len_str; j++){
				char single_char = strings.at(i)[j];
				
				if(single_char == 'x'){
					single_digit = 0;
				} else {
					if(single_char == 'y'){
						single_digit = 1;
					} else {
						// This block should never run
						std::cout << "Please enter a valid expression.\n";
						exit(0);
					}
				} 
				temp.push_back(single_digit);
				}
				
			indices.push_back(temp);
			   
			}
			
			
		return indices;
		}

	void store_gamma(Eigen::Array<T, -1, -1> *gamma, std::vector<int> N_moments, std::vector<std::vector<int>> indices, std::string name_dataset){
		if(DEBUG)std::cout << "Entered store_gamma.\n" << std::flush;
		/* Depending on the type of Gamma matrix we're calculating, there may be some symmetries
		 * among the matrix entries that could be taken into account.
		 * 
		 * */
		H5::H5File * file = new H5::H5File(name, H5F_ACC_RDWR);
		long int size_gamma = gamma->cols();
		int dim = indices.size();
		
		
		// Number of commutators inside the Gamma matrix. 
		// V^{x}  = [x,H]		-> one commutator
		// V^{xy} = [x,[y,H]]	-> two commutators
		// This is important because the commutator is anti-hermitian. So, an odd number of commutators
		// means that the conjugate of the Gamma matrix has an overall minus sign
		int num_velocities = 0;
		for(int i = 0; i < int(indices.size()); i++)
			num_velocities += indices.at(i).size();
		//std::cout << "num_velocities: " << num_velocities << "\n";
		
		int factor = 1 - (num_velocities % 2)*2;
		
		//std::cout << "gamma: " << *gamma << "\n";
		
		switch(dim){
			case 2:
			{
				//std::cout << "gamma_matrix dimension: " << dim << "\n";
				// Put the data of the Gamma matrix in a 2D matrix 
				Eigen::Array<T,-1,-1> general_gamma = Eigen::Map<Eigen::Array<T,-1,-1>>(gamma->data(), N_moments.at(0), N_moments.at(1));
				#pragma omp master
				{
					Global.general_gamma = Eigen::Array<T, -1, -1 > :: Zero(N_moments.at(0), N_moments.at(1));
				}
				#pragma omp barrier
				
				
				
				// Gather the data from all the threads, one by one.
				// There are some additional symmetry operations that we can take advantage of.
				// In the case of two indices: Gamma{x,y}(n,m) = Gamma{x,y}(n,m)*, that is, it's self-adjoint.
				// The factor is -1 when the matrix is anti-hermitian and 1 when hermitian
				#pragma omp critical
				Global.general_gamma.matrix() += (general_gamma.matrix() + factor*general_gamma.matrix().adjoint())/2.0;
				#pragma omp barrier
				
				break;
			}
				
			case 1:
			{
				//std::cout << "gamma_matrix dimension: " << dim << "\n" << std::flush;
				Eigen::Array<T,-1,-1> general_gamma = Eigen::Map<Eigen::Array<T,-1,-1>>(gamma->data(), 1, size_gamma);
				#pragma omp master
				{
					Global.general_gamma = Eigen::Array<T, -1, -1 > :: Zero(1, size_gamma);
				}
				#pragma omp barrier
				
				
				//std::cout << "here1\n" << std::flush;
				// Gather the data from all the threads, one by one.
				
				#pragma omp critical
				Global.general_gamma += general_gamma;
				#pragma omp barrier
				
				//std::cout << "here2\n" << std::flush;
			
				break;
			}
			/*
			case 3:
			
				break;
				*/
			default:
				std::cout << "You're trying to store a matrix that is not expected by the program. Exiting.\n";
				exit(0);
		
		}
		
		
		//std::cout << "global_general_gamma: " << Global.general_gamma << "\n";
		
		#pragma omp master
		{
			write_hdf5(Global.general_gamma, file, name_dataset);
		}
		
		delete file;
		
		//std::cout << "here3\n" << std::flush;
		std::cout << "Left store_gamma.\n" << std::flush;
	}

	double time_kpm(int N_average){
		/* This function serves to provide an estimate of the time it takes for each kpm iteration
		 * 
		*/
		
		KPM_Vector<T,D> kpm0(1, *this);
		KPM_Vector<T,D> kpm1(2, *this);
		
		
		kpm0.initiate_vector();
		kpm1.set_index(0);
		kpm1.v.col(0) = kpm0.v.col(0);
		kpm1.template Multiply<0>(); 
		
		auto t0 =  std::chrono::high_resolution_clock::now();
		for(int i = 0; i < N_average; i++)
			kpm1.template Multiply<1>(); 
		auto t1 =  std::chrono::high_resolution_clock::now();
		
		std::chrono::duration<double> time_span = std::chrono::duration_cast<std::chrono::duration<double>>(t1 - t0);
		return time_span.count()/N_average;
		
		
	}

  void Measure_Lambda(int & NRandomV, int & NDisorder, std::string indices, std::string filename_dataset) {
		
		/* This function calculates Tr[ V^ab T_n ], the analogue in tight binding
		 * of the diamagnetic term. The calculation is almost identical with the
		 * calculation of the density of states (go figure). The only difference resides
		 * in multiplying the left-most phi0 by Velocity2 before doing the dot product
		 * with phi. Velocity2 = v^ab
		 * */
		 
		if(DEBUG)std::cout << "entered LAMBDA\n";fflush(stdout);
		
		// Process the indices
		std::vector<int> first_indices;
		first_indices.resize(indices.size()); 
		if(DEBUG)std::cout << "strings: " << indices << "\n";fflush(stdout);
		
		for(unsigned int i = 0; i < indices.size(); i++){
			if(indices[i]=='y')
				first_indices.at(i) = 1;
			else
				first_indices.at(i) = 0;
		}
		for(unsigned  int i = 0; i < indices.size(); i++)
			if(DEBUG)std::cout << "first_indices: " << first_indices.at(i) << "\n";fflush(stdout);
		
		
		
		//Done processing the indices
		Eigen::Array<T, -1, -1> lambda = Eigen::Array<T, -1, -1 > :: Zero(Global.lambda.rows(),Global.lambda.cols());
		
		typedef typename extract_value_type<T>::value_type value_type;


		//make sure the local matrix is zeroed to be used again
		lambda.setZero();
    
    KPM_Vector<T,D> phi0(1, *this);
    KPM_Vector<T,D>  phi(2, *this);

    
    long average = 0;
    for(int disorder = 0; disorder < NDisorder; disorder++)
		{
			h.distribute_AndersonDisorder();
			for(int randV = 0; randV < NRandomV; randV++)
				{
					phi0.initiate_vector();
					phi.set_index(0);	
					phi.v.col(0) = phi0.v.col(0);
					phi.Exchange_Boundaries();
					
					
					
					// check which operator needs to be calculated.
					if(first_indices.size()==1){
						phi.Velocity(phi0.v.col(0).data(), phi.v.col(phi.get_index()).data(), first_indices.at(0));
						phi0.empty_ghosts(0);
					}
					
					if(first_indices.size()==2){
						phi.Velocity2(phi0.v.col(0).data(), phi.v.col(phi.get_index()).data(), first_indices.at(0), first_indices.at(1));
						phi0.empty_ghosts(0);
					}
					
					
					phi.template Multiply<0>();
					lambda.matrix().block(0,0,1,2) +=  (phi0.v.adjoint() * phi.v - lambda.matrix().block(0,0,1,2))/value_type(average + 1);
					
					for(int m = 2; m < lambda.cols(); m += 2)
					{	    
						phi.template Multiply<1>();
						phi.template Multiply<1>();
						lambda.matrix().block(0,m,1,2) +=  (phi0.v.adjoint() * phi.v - lambda.matrix().block(0,m,1,2))/value_type(average + 1);
					}
					average++;
				}
    }
    
     
#pragma omp critical

		Global.lambda += lambda;
    
#pragma omp barrier

    
#pragma omp master
    {
      H5::H5File * file = new H5::H5File(name, H5F_ACC_RDWR);
			write_hdf5(Global.lambda, file, filename_dataset);
      delete file;
      
			//make sure the global matrix is zeroed to be used again later
			Global.lambda.setZero();
    }
#pragma omp barrier
  }

  void Single_Shot(double EScale, int & NRandomV, int & NDisorder, int N_cheb_moments, Eigen::Array<double, -1, 1> energy_array, double finite_gamma, std::string indices, std::string name_dataset) {
		/*
		 * Calculate the longitudinal conductivity for a single value of the energy
		 */
		 
		//std::cout << "energies: " << energy_array << "\n";
		 
		// Process the indices
		if(DEBUG)std::cout << "entered singleshot\n";
		std::vector<int> first_indices, second_indices;
		
		int comma_location = indices.find_first_of(',');
	
		std::string first_string, second_string;
		first_string = indices.substr(0, comma_location);
		second_string = indices.substr(comma_location+1);		
		first_indices.resize(first_string.size()); 
		second_indices.resize(second_string.size());
		
		if(DEBUG)std::cout << "strings: " << first_string << " "<< second_string << "\n";
		
		for(unsigned int i = 0; i < first_string.size(); i++){
			if(first_string[i]=='y')
				first_indices.at(i) = 1;
			else
				first_indices.at(i) = 0;
		}
		
		for(unsigned  int i = 0; i < second_string.size(); i++){
			if(second_string[i]=='y')
				second_indices.at(i) = 1;
			else
				second_indices.at(i) = 0;
		}
			/*
		for(unsigned  int i = 0; i < first_string.size(); i++)
			std::cout << "first_indices: " << first_indices.at(i) << "\n";
			
		for(unsigned  int i = 0; i < second_string.size(); i++)
			std::cout << "second_indices: " << second_indices.at(i) << "\n";
		
		*/
		
		//Done processing the indices
		
		
		
		
		 
		
    typedef typename extract_value_type<T>::value_type value_type;
    KPM_Vector<T,D> phi0(1, *this);
    KPM_Vector<T,D> phi (2, *this);
    
    KPM_Vector<T,D> phi1(2, *this);
    KPM_Vector<T,D> phi2(2, *this);
		
	
		//int a = 4;
		//int b = 4;
		
    Eigen::Array<T, -1, -1> cond_array;
    int N_energies = energy_array.cols()*energy_array.rows(); //one of them is one. I don't know if it's the columns or the rows, but it doesn't matter
    //~ std::cout << "before cond array\n";fflush(stdout);
    cond_array = Eigen::Array<T, -1, -1>::Zero(1, Global.singleshot_cond.cols());
    
    if(DEBUG)std::cout << "gonna start calculating\n";fflush(stdout);
    
    for(int ener = 0; ener < N_energies; ener++){
			std::complex<double> energy(energy_array(ener), finite_gamma);
			if(DEBUG)std::cout << "finished setting complex energy\n";fflush(stdout);
			long average = 0;
			for(int disorder = 0; disorder < NDisorder; disorder++){
				if(DEBUG)std::cout << "before disorder\n";fflush(stdout);
					h.generate_disorder();
					if(DEBUG)std::cout << "after disorder\n";fflush(stdout);
					for(int randV = 0; randV < NRandomV; randV++){
						
						if(DEBUG)std::cout << "started calculating the first vector\n";fflush(stdout);
																		
						phi0.initiate_vector();					
						phi0.Exchange_Boundaries(); 	
						
						// calculate the left vector
						phi.set_index(0);				
						
						
						// |phi> = v |phi_0>
						phi.Velocity(phi.v.col(0).data(), phi0.v.col(0).data(), first_indices.at(0));	
						if(DEBUG)std::cout << "multiplied by velocity\n";fflush(stdout);
						phi.Exchange_Boundaries();	
						//~ phi1.v.col(0) = phi.v.col(phi.get_index())*(a==0);
						phi1.v.col(0) = phi.v.col(phi.get_index())*green(0, 1, energy).imag()/2.0;
									
						phi.template Multiply<0>();		
						//~ phi1.v.col(0) += phi.v.col(1)*(a==1);
						phi1.v.col(0) += phi.v.col(1)*green(1, 1, energy).imag();
						
						if(DEBUG)std::cout << "finished first cheb\n";fflush(stdout);
						
						for(int n = 2; n < N_cheb_moments; n++){		
							phi.template Multiply<1>();
							//~ phi1.v.col(0) += phi.v.col(phi.get_index())*(a==n);
							phi1.v.col(0) += phi.v.col(phi.get_index())*green(n, 1, energy).imag();
						}
						
						// multiply phi1 by the velocity operator again. 
						// We need a temporary vector to mediate the operation, which will be |phi>
						phi.v.col(0) = phi1.v.col(0);
						phi.Velocity(phi1.v.col(0).data(), phi.v.col(0).data(), second_indices.at(0));
						phi1.empty_ghosts(0);
						
						if(DEBUG)std::cout << "Finished calculating the first vector\n";fflush(stdout);
						
						// calculate the right vector
						phi.set_index(0);			
						phi.v.col(0) = phi0.v.col(0);
						
						//~ phi2.v.col(0) = phi.v.col(phi.get_index())*(b==0);
						phi2.v.col(0) = phi.v.col(phi.get_index())*green(0, 1, energy).imag()/2.0;
									
						phi.template Multiply<0>();		
						//~ phi2.v.col(0) += phi.v.col(1)*(b==1);
						phi2.v.col(0) += phi.v.col(1)*green(1, 1, energy).imag();
						
						for(int n = 2; n < N_cheb_moments; n++){		
							phi.template Multiply<1>();
							//~ phi2.v.col(0) += phi.v.col(phi.get_index())*(b==n);
							phi2.v.col(0) += phi.v.col(phi.get_index())*green(n, 1, energy).imag();
						}
						
						cond_array(ener) += (T(phi1.v.col(0).adjoint()*phi2.v.col(0)) - cond_array(ener))/value_type(average+1);						
						average++;
						
						if(DEBUG)std::cout << "Finished calculating the second vector\n";fflush(stdout);
				}
			}
		}
		
		//std::cout << "gamma_00\n" << gamma.matrix().block(0,0,3,1) << "\n";fflush(stdout);
		
		// the gamma matrix has been calculated. Now we're going to use the 
		// property that gamma is hermitian: gamma_nm=gamma_mn*
	
		
#pragma omp critical

		//std::cout << "IMPORTANT ! ! !:\n V is not hermitian. Make sure you take this into account\n";
		// in this case there's no problem. both V are anti-hermitic, so the minus signs cancel
		Global.singleshot_cond += cond_array;
		
			
#pragma omp barrier

    
#pragma omp master
    {
			
			// Fixing the factor
			double unit_cell_area = fabs(r.rLat.determinant());
      unsigned int number_of_orbitals = r.Orb; 	// This is necessary because the normalization factor inside the random 
																								// vectors is not the number of lattice sites N but the number of states, 
																								// which is N*number_of_orbitals
      unsigned int spin_degeneracy = 1;
      
      double factor = -4.0*spin_degeneracy*number_of_orbitals/M_PI/unit_cell_area;	// This is in units of sigma_0, hence the 4
      Global.singleshot_cond *= factor;
      
      // Create array to store the data
      Eigen::Array<double, -1, -1> store_data;
      store_data = Eigen::Array<double, -1, -1>::Zero(2, Global.singleshot_cond.cols());
      
      for(int ener = 0; ener < N_energies; ener++){
				store_data(0, ener) = energy_array.real()(ener)*EScale;
				store_data(1, ener) = Global.singleshot_cond.real()(ener);
			}
			

			
      H5::H5File * file = new H5::H5File(name, H5F_ACC_RDWR);
			write_hdf5(store_data, file, name_dataset);
      delete file;
      
      // make sure the global matrix is zeroed
      Global.singleshot_cond.setZero();
      if(DEBUG)std::cout << "left singleshot\n";fflush(stdout);
    }
#pragma omp barrier
  }
	
  
};


  
