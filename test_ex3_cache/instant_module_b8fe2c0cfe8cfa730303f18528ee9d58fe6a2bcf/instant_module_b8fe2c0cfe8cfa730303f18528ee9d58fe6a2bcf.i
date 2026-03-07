%module  instant_module_b8fe2c0cfe8cfa730303f18528ee9d58fe6a2bcf
//%module (directors="1") instant_module_b8fe2c0cfe8cfa730303f18528ee9d58fe6a2bcf

//%feature("director");

%{
#include <iostream>

#include <numpy/arrayobject.h>



void sum (int x1, int y1, double* array1, int xy2, double* array2){
  for (int i=0; i<x1; i++)
    for (int j=0; j<y1; j++)
      array2[i*y1 + j] = array1[i*y1 + j]*2;
}
    
%}

//%feature("autodoc", "1");
%include "numpy.i"

%init%{

import_array();

%}




//
%apply (int DIM1, int DIM2, double* IN_ARRAY2) {(int x1, int y1, double* array1)};

%apply (int DIM1, double* ARGOUT_ARRAY1) {(int xy2, double* array2)};


void sum (int x1, int y1, double* array1, int xy2, double* array2){
  for (int i=0; i<x1; i++)
    for (int j=0; j<y1; j++)
      array2[i*y1 + j] = array1[i*y1 + j]*2;
}
    ;

