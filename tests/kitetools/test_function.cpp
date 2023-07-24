#include <iostream>
#include <Eigen/Dense>
#include "../../cppcore/kitetools/src/tools/functions.cpp"

// g++ test_function.cpp -I/usr/include/eigen3 -o out && ./out

int main(){
    unsigned N = 7;
    Eigen::Matrix<double, Eigen::Dynamic, 1> xs;
    Eigen::Matrix<std::complex<double>, Eigen::Dynamic, 1> ys;

    xs = Eigen::Matrix<double, Eigen::Dynamic, 1>::LinSpaced(N,0,1);
    ys = Eigen::Matrix<std::complex<double>, Eigen::Dynamic, 1>::Zero(N);

    for(unsigned i = 0; i < N; i++){
        ys(i) = xs(i)*xs(i)*xs(i)*xs(i);
        //ys(i) = xs(i)*xs(i)*xs(i);
        //ys(i) = xs(i)*xs(i);
        //ys(i) = xs(i);
    }

    std::complex<double> integral;
    integral = integrate(xs, ys);
    std::cout << integral << "\n";

}
