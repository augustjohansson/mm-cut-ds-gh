%module  test19_ext
//%module (directors="1") test19_ext

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

