%module  test19_signature_module
//%module (directors="1") test19_signature_module

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

