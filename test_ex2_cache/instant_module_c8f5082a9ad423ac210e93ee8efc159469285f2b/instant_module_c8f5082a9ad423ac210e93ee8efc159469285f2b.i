%module  instant_module_c8f5082a9ad423ac210e93ee8efc159469285f2b
//%module (directors="1") instant_module_c8f5082a9ad423ac210e93ee8efc159469285f2b

//%feature("director");

%{
#include <iostream>

#include <numpy/arrayobject.h>



double sum (int x1, int y1, double* array1, int x2, int y2, double* array2){
  double tmp = 0.0;
  for (int i=0; i<x1; i++)
    for (int j=0; j<y1; j++){
      tmp = array1[i*y1 + j];
      array1[i*y1 + j] = array2[i*y1 + j];
      array2[i*y1 + j] = tmp;
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
%apply (int DIM1, int DIM2, double* INPLACE_ARRAY2) {(int x1, int y1, double* array1)};

%apply (int DIM1, int DIM2, double* INPLACE_ARRAY2) {(int x2, int y2, double* array2)};


double sum (int x1, int y1, double* array1, int x2, int y2, double* array2){
  double tmp = 0.0;
  for (int i=0; i<x1; i++)
    for (int j=0; j<y1; j++){
      tmp = array1[i*y1 + j];
      array1[i*y1 + j] = array2[i*y1 + j];
      array2[i*y1 + j] = tmp;
    }
  return tmp;
}
    ;

