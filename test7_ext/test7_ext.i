%module  test7_ext
//%module (directors="1") test7_ext

//%feature("director");

%{
#include <iostream>

#include <numpy/arrayobject.h>



void func(int n1, double* array1, int n2, double* array2){
    double a;
    if ( n1 == n2 ) {
        for (int i=0; i<n1; i++) {
            a = array1[i];
            array2[i] = sin(a) + cos(a) + tan(a);
        }
    } else {
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


void func(int n1, double* array1, int n2, double* array2){
    double a;
    if ( n1 == n2 ) {
        for (int i=0; i<n1; i++) {
            a = array1[i];
            array2[i] = sin(a) + cos(a) + tan(a);
        }
    } else {
        printf("The arrays should have the same size.");
    }
}
;

