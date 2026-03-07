%module  instant_module_980c475d95605c52850dc22efa6e2eb0b123f0e4
//%module (directors="1") instant_module_980c475d95605c52850dc22efa6e2eb0b123f0e4

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

