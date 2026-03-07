%module  instant_module_3a46f54e117a2ae6b719946a32db722ad11d5165
//%module (directors="1") instant_module_3a46f54e117a2ae6b719946a32db722ad11d5165

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

