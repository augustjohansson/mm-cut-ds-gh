%module  test6_ext
//%module (directors="1") test6_ext

//%feature("director");

%{
#include <iostream>

#include <numpy/arrayobject.h>



/* add function for matrices with all safety checks removed ..*/
void add(int x1, int y1, double* array1,
         int x2, int y2, double* array2,
         int x3, int y3, double* array3){

  for (int i=0; i<x1; i++) {
    for (int j=0; j<y1; j++) {
      *array3 = *array1 + *array2;
      array3++;
      array2++;
      array1++;
    }
  }
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

%apply (int DIM1, int DIM2, double* INPLACE_ARRAY2) {(int x3, int y3, double* array3)};


/* add function for matrices with all safety checks removed ..*/
void add(int x1, int y1, double* array1,
         int x2, int y2, double* array2,
         int x3, int y3, double* array3){

  for (int i=0; i<x1; i++) {
    for (int j=0; j<y1; j++) {
      *array3 = *array1 + *array2;
      array3++;
      array2++;
      array1++;
    }
  }
}
;

