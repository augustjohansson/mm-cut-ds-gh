%module  instant_module_13e1c5a7533e08f1b8225a1bce5cc844ec4cc4ec
//%module (directors="1") instant_module_13e1c5a7533e08f1b8225a1bce5cc844ec4cc4ec

//%feature("director");

%{
#include <iostream>

#include <numpy/arrayobject.h>



double sum (int n1, double* array1){
  double tmp = 0.0;
  for (int i=0; i<n1; i++) {
      tmp += array1[i];
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
%apply (int DIM1, double* INPLACE_ARRAY1) {(int n1, double* array1)};


double sum (int n1, double* array1){
  double tmp = 0.0;
  for (int i=0; i<n1; i++) {
      tmp += array1[i];
  }
  return tmp;
}
;

