%module  test5_ext
//%module (directors="1") test5_ext

//%feature("director");

%{
#include <iostream>

#include <numpy/arrayobject.h>



/* add function for vectors with all safety checks removed ..*/
void add(int n1, double* array1, int n2, double* array2, int n3, double* array3){
  if ( n1 == n2 && n1 == n3 ) {
     for (int i=0; i<n1; i++) {
        array3[i] = array1[i] + array2[i];
     }
  }
  else {
    printf("The arrays should have the same size.");
  }

}

%}

//%feature("autodoc", "1");
%include "numpy.i"

%init%{
import_array();
%}




//
%apply (int DIM1, double* INPLACE_ARRAY1) {(int n1, double* array1)};

%apply (int DIM1, double* INPLACE_ARRAY1) {(int n2, double* array2)};

%apply (int DIM1, double* INPLACE_ARRAY1) {(int n3, double* array3)};


/* add function for vectors with all safety checks removed ..*/
void add(int n1, double* array1, int n2, double* array2, int n3, double* array3){
  if ( n1 == n2 && n1 == n3 ) {
     for (int i=0; i<n1; i++) {
        array3[i] = array1[i] + array2[i];
     }
  }
  else {
    printf("The arrays should have the same size.");
  }

}
;

