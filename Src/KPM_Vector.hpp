template <typename T, unsigned D>
class KPM_VectorBasis {
protected:
  int index;
  const int memory;
  Simulation<T,D> & simul;
  
  
public:
  Eigen::Matrix <T, Eigen::Dynamic,  Eigen::Dynamic > v;
  KPM_VectorBasis(int mem,  Simulation<T,D> & sim) :
    memory(mem), simul(sim) {
    index  = 0;
    v = Eigen::Matrix <T, Eigen::Dynamic,  Eigen::Dynamic >::Zero(simul.r.Sized, memory);
  };
  
  void set_index(int i) {index = i;};
  void inc_index() {index = (index + 1) % memory;};  
  unsigned get_index(){return index;};

  // Define aux_wr for complex T 
  template <typename U = T>
  typename std::enable_if<is_tt<std::complex, U>::value, U>::type aux_wr(unsigned long x ) {
    typedef typename extract_value_type<U>::value_type value_type;
    return U(value_type(x), value_type(2*x));
  };

  // Define aux_wr for non complex T 
  template <typename U = T>
  typename std::enable_if<!is_tt<std::complex, U>::value, U>::type aux_wr(unsigned long x ) {
    return U(x);
  };
  

  bool aux_test(T & x, T & y ) {
    return (abs(x - y) > std::numeric_limits<double>::epsilon());
  };
  
  
};


template <typename T, unsigned D>
class KPM_Vector : public KPM_VectorBasis <T,D> {
public:
  KPM_Vector(int mem, Simulation<T,D> & sim) :
    KPM_VectorBasis<T,D>(mem,sim){};
  
  void initiate_vector() {};
  template <unsigned MULT>
  void Multiply(){};
  template <unsigned MULT>
  void Multiply2(){};
  void test_boundaries_system() {};
  void Exchange_Boundaries() {};
  inline void  HaIteration() { Multiply<0>(); };
  inline void  ChIteration() { Multiply<1>(); };
  void Velocity( T *, T *, int );
  T VelocityInternalProduct( T *  , T * , int);  
};


