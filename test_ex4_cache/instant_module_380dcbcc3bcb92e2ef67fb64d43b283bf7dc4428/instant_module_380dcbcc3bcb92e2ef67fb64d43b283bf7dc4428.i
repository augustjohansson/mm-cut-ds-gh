%module  instant_module_380dcbcc3bcb92e2ef67fb64d43b283bf7dc4428
//%module (directors="1") instant_module_380dcbcc3bcb92e2ef67fb64d43b283bf7dc4428

//%feature("director");

%{
#include <iostream>

#include <numpy/arrayobject.h>



void sum (int x1, int y1, long* array1, int x2, int* array2, int x3, double* array3){
  for (int i=0; i<x1; i++){
    array3[i] = 0;
    for (int j=0; j<y1; j++)
      array3[i] += array1[i*y1 + j]*array2[j];
  }
}
    
%}

//%feature("autodoc", "1");
%include "numpy.i"

%init%{

import_array();

%}




//
%apply (int DIM1, int DIM2, long* IN_ARRAY2) {(int x1, int y1, long* array1)};

%apply (int DIM1, int* INPLACE_ARRAY1) {(int x2, int* array2)};

%apply (int DIM1, double* ARGOUT_ARRAY1) {(int x3, double* array3)};


void sum (int x1, int y1, long* array1, int x2, int* array2, int x3, double* array3){
  for (int i=0; i<x1; i++){
    array3[i] = 0;
    for (int j=0; j<y1; j++)
      array3[i] += array1[i*y1 + j]*array2[j];
  }
}
    ;

