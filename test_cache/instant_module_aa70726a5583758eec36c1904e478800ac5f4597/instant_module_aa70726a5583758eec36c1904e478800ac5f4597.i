%module  instant_module_aa70726a5583758eec36c1904e478800ac5f4597
//%module (directors="1") instant_module_aa70726a5583758eec36c1904e478800ac5f4597

//%feature("director");

%{
#include <iostream>





double sum(double a, double b)
{
  return a+b;
}
    
%}

//%feature("autodoc", "1");


%init%{

%}




//

double sum(double a, double b)
{
  return a+b;
}
    ;

