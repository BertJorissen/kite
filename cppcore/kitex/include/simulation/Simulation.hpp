/***********************************************************/
/*                                                         */
/*   Copyright (C) 2018-2022, M. Andelkovic, L. Covaci,    */
/*  A. Ferreira, S. M. Joao, J. V. Lopes, T. G. Rappoport  */
/*                                                         */
/***********************************************************/

#ifndef SIMULATION_HPP
#define SIMULATION_HPP

template <typename T> using ema = Eigen::Array<T, Eigen::Dynamic, Eigen::Dynamic, 0, -1, -1>;

template <typename T,unsigned D>
class Simulation : public ComplexTraits<T> {
public:
  using ComplexTraits<T>::assign_value;
  using ComplexTraits<T>::myconj;
  typedef typename extract_value_type<T>::value_type value_type;
  KPMRandom <T>          rnd;
  std::vector<T>         ghosts;
  LatticeStructure <D>   r;      
  GLOBAL_VARIABLES <T> & Global;
  char                 * name;
  Hamiltonian<T,D>       h;
  
  Simulation(char *, GLOBAL_VARIABLES <T> &);

  //void Measure_Gamma(measurement_queue);

  void Gamma1D(int, int, int, std::vector<std::vector<unsigned>>, std::string );
  void Gamma2D(int, int, std::vector<int>,  std::vector<std::vector<unsigned>>, std::string );
  void Gamma3D(int, int, std::vector<int>,  std::vector<std::vector<unsigned>>, std::string );
  void GammaGeneral(int, int, const std::vector<int>&, const std::vector<std::vector<unsigned>>&, const std::string& );
  void recursive_KPM(int, int, std::vector<int>, long *, long *,  const std::vector<std::vector<unsigned>>&,
          std::vector<KPM_Vector<T,D>*> *, Eigen::Array<T, Eigen::Dynamic, Eigen::Dynamic> *);
  void store_gamma(Eigen::Array<T, Eigen::Dynamic, Eigen::Dynamic> *, std::vector<int>,  std::vector<std::vector<unsigned>>, std::string );
  void store_gamma1D(Eigen::Array<T, Eigen::Dynamic, Eigen::Dynamic> *, std::string );
  void store_gamma3D(Eigen::Array<T, Eigen::Dynamic, Eigen::Dynamic> *, std::vector<int>, std::vector<std::vector<unsigned>>, std::string );
  std::vector<std::vector<unsigned>> process_string(std::string);
  double time_kpm(int);

  void calc_singleshot();
  void singleshot(Eigen::Array<double, Eigen::Dynamic, 1> energies,
  Eigen::Array<double, Eigen::Dynamic, 1> gammas,
  Eigen::Array<int, Eigen::Dynamic, 1> preserve_disorders,
  Eigen::Array<int, Eigen::Dynamic, 1> moments,
  int NDisorder, int NRandom, std::string direction_string);

  
  void calc_conddc();
  void CondDC(int, int, int, int);
  
  void calc_condopt();
  void CondOpt(int, int, int, int);

  void calc_condopt2();
  void CondOpt2(int, int, int, int, int);

  void calc_DOS();
  void DOS(int, int, int);
  void store_MU(Eigen::Array<T, Eigen::Dynamic, Eigen::Dynamic> *);

  void Gaussian_Wave_Packet();
  void calc_wavepacket();

  void LMU(int, int, Eigen::Array<unsigned long, Eigen::Dynamic, 1>);
  void calc_LDOS();
  void store_LMU(Eigen::Array<T, Eigen::Dynamic, Eigen::Dynamic> *);
	
  void calc_ARPES();
  void ARPES(int NDisorder, int NMoments, Eigen::Array<double, Eigen::Dynamic, Eigen::Dynamic> & k_vectors, Eigen::Matrix<T, Eigen::Dynamic, 1> & weight);
  void store_ARPES(ema<T> *);
};
#endif SIMULATION_HPP