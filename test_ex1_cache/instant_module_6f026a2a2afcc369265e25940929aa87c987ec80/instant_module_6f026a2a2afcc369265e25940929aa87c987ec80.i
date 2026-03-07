%module  instant_module_6f026a2a2afcc369265e25940929aa87c987ec80
//%module (directors="1") instant_module_6f026a2a2afcc369265e25940929aa87c987ec80

//%feature("director");

%{
#include <iostream>

#include <numpy/arrayobject.h>



double sum (int x1, int y1, int z1, double* array1, int x2, double* array2){
  double tmp = 0.0;
  for (int i=0; i<x1; i++)
    for (int j=0; j<y1; j++)
      for (int k=0; k<z1; k++){
        tmp += array1[i*y1*z1 + j*z1 + k];
        array2[1] = 2;
    }
  return tmp;
}
    
%}

//%feature("autodoc", "1");
%include "numpy.i"

%init%{

import_array();

%}




//
%apply (int DIM1, int DIM2, int DIM3, double* INPLACE_ARRAY3) {(int x1, int y1, int z1, double* array1)};

%apply (int DIM1, double* IN_ARRAY1) {(int x2, double* array2)};


double sum (int x1, int y1, int z1, double* array1, int x2, double* array2){
  double tmp = 0.0;
  for (int i=0; i<x1; i++)
    for (int j=0; j<y1; j++)
      for (int k=0; k<z1; k++){
        tmp += array1[i*y1*z1 + j*z1 + k];
        array2[1] = 2;
    }
  return tmp;
}
    ;

