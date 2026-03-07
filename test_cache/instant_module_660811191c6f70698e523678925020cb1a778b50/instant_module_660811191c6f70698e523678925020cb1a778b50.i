%module  instant_module_660811191c6f70698e523678925020cb1a778b50
//%module (directors="1") instant_module_660811191c6f70698e523678925020cb1a778b50

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
double max(int n1, double* array1){
  double tmp = 0.0;
  for (int i=0; i<n1; i++) {
      if (array1[i] > tmp) {
          tmp = array1[i];
      }
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
double max(int n1, double* array1){
  double tmp = 0.0;
  for (int i=0; i<n1; i++) {
      if (array1[i] > tmp) {
          tmp = array1[i];
      }
  }
  return tmp;
}

;

