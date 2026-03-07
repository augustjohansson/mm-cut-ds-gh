%module  instant_module_d329d37b7a34f155ec36923f529a4aea9613c42d
//%module (directors="1") instant_module_d329d37b7a34f155ec36923f529a4aea9613c42d

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

