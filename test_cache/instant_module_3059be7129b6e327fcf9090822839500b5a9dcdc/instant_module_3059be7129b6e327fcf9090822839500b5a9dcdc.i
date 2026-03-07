%module  instant_module_3059be7129b6e327fcf9090822839500b5a9dcdc
//%module (directors="1") instant_module_3059be7129b6e327fcf9090822839500b5a9dcdc

//%feature("director");

%{
#include <iostream>




double add(double c, double d){ return c+d; }
%}

//%feature("autodoc", "1");


%init%{

%}




//
double add(double c, double d){ return c+d; };

