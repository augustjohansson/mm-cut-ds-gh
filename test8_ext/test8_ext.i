%module  test8_ext
//%module (directors="1") test8_ext

//%feature("director");

%{
#include <iostream>





class Sum {
public:
  virtual double sum(double a, double b){
    return a+b;
  }
};


double use_Sum(Sum& sum, double a, double b) {
  return sum.sum(a,b);
}

%}

//%feature("autodoc", "1");


%init%{

%}




//

class Sum {
public:
  virtual double sum(double a, double b){
    return a+b;
  }
};


double use_Sum(Sum& sum, double a, double b) {
  return sum.sum(a,b);
}
;

