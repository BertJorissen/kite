echo "Compiling KITEx and KITE-tools. To have the full functionality,"
echo "you need to have at least version 8 of gcc. If you do not, you "
echo "will not be able to run guassian_wavepacket. To enable compiling"
echo "with this feature, please edit this file and set WAVEPACKET=1."
echo "By default, the flag WAVEPACKET is set to 0"
WAVEPACKET=0

# create the directory structure
mkdir -p build

# Common locations for the eigen headers. Edit this line if eigen is not in any of these places
eigen="-I/opt/local/include/eigen3 -I$HOME/include/eigen3 -I/usr/include/eigen3"

# Library and header locations
libraries="-L$HOME/lib -L/opt/local/lib -lhdf5_hl_cpp -lhdf5_cpp -lhdf5_hl -lhdf5"
headers="-I$HOME/include -I/opt/local/include $eigen"

# Compile KITEx
kitedir="../../cppcore/kitex/include"
include="-I$kitedir -I$kitedir/hamiltonian -I$kitedir/tools -I$kitedir/vector -I$kitedir/simulation -I$kitedir/lattice"
sources="../../cppcore/kitex/src/*.cpp ../../cppcore/kitex/src/*/*.cpp"

echo "Compiling KITEx"
cd build
mkdir kitex
cd kitex
for i in $sources; do
  echo "Compiling $i"
  g++ -DCOMPILE_WAVEPACKET=$WAVEPACKET -std=gnu++11 -O2 $i  $include $headers  -fopenmp -c
done
echo "Linking"
g++ -std=gnu++11 -O2 *.o $libraries -fopenmp -o ../KITEx
echo "Done."
cd ../..

# Compile KITE-tools
kitedir="../../cppcore/kitetools/include"
include="-I$kitedir -I$kitedir/optcond_1order -I$kitedir/optcond_2order -I$kitedir/spectral -I$kitedir/tools -I$kitedir/conddc"
sources="../../cppcore/kitetools/src/*.cpp ../../cppcore/kitetools/src/*/*.cpp"

echo "Compiling KITE-tools"
cd build
mkdir kitetools
cd kitetools
for i in $sources; do
  echo "Compiling $i"
  g++ -std=gnu++11 -O2 $i $include $headers -fopenmp -c
done
echo "Linking"
g++ -std=gnu++11 -O2 *.o $libraries -fopenmp -o ../KITE-tools
echo "Done."
cd ../..

