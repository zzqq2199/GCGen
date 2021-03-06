#include <stdint.h>
#include <iostream>
using namespace std;

template<typename T>
class Random{
private:
    uint32_t _a;
    uint32_t _c;
    uint32_t _x;
public:
    Random(const uint32_t seed){
        _a=1103515245;
        _c=12345;
        _x = seed;
    }
    uint32_t rand(){
        _x = _a*_x + _c;
        return _x;
    }

    T operator()(T lower_bound, T upper_bound){
        return static_cast<T>(rand()%(upper_bound-lower_bound+1))+lower_bound;
    }
};
template<>
class Random<float>{
private:
    uint32_t _a;
    uint32_t _c;
    uint32_t _x;

    uint32_t _max;
    double _max_double;
public:
    Random(const uint32_t seed){
        _a=1103515245;
        _c=12345;
        _x = seed;
        _max = ~0;
        _max_double = static_cast<double>(_max);
    }
    uint32_t rand(){
        _x = _a*_x + _c;
        return _x;
    }
public:
    float operator()(float lower_bound, float upper_bound){
        return static_cast<float>(rand()/(_max_double/(upper_bound-lower_bound)))+lower_bound;
    }
};

int main(){
    Random<int> random(1);
    for (int i = 0; i < 16; i++)
        cout << random(3,8) << '\t';
    cout<<endl;

    Random<float> random_float(2);
    for (int i =0; i<16; i++){
        cout<<random_float(0,2) << '\t';
    }
    cout<<endl;

    return 0;
}