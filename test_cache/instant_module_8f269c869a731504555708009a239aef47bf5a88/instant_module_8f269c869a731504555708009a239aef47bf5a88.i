%module  instant_module_8f269c869a731504555708009a239aef47bf5a88
//%module (directors="1") instant_module_8f269c869a731504555708009a239aef47bf5a88

//%feature("director");

%{
#include <iostream>




double add(double a, double b){ return a+b; }
%}

//%feature("autodoc", "1");


%init%{

%}




//
double add(double a, double b){ return a+b; };

