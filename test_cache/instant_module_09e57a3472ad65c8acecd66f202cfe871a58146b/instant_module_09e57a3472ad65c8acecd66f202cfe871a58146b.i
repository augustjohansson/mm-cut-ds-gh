%module  instant_module_09e57a3472ad65c8acecd66f202cfe871a58146b
//%module (directors="1") instant_module_09e57a3472ad65c8acecd66f202cfe871a58146b

//%feature("director");

%{
#include <iostream>

#include <numpy/arrayobject.h>



void time_loop(int n, double* p,
             int m, double* Q,
             double A, double B,
             double dt, int N, double p0)
{
    if ( n != m ) {
        printf("n and m should be equal");
        return;
    }
    if ( n != N ) {
        printf("n and N should be equal");
        return;
    }

    p[0] = p0;
    for (int i=1; i<n; i++) {
        p[i] = p[i-1] + dt*(B*Q[i] - A*p[i-1]);
    }
}

%}

//%feature("autodoc", "1");
%include "numpy.i"

%init%{

import_array();

%}




//
%apply (int DIM1, double* INPLACE_ARRAY1) {(int n, double* p)};

%apply (int DIM1, double* INPLACE_ARRAY1) {(int m, double* Q)};


void time_loop(int n, double* p,
             int m, double* Q,
             double A, double B,
             double dt, int N, double p0)
{
    if ( n != m ) {
        printf("n and m should be equal");
        return;
    }
    if ( n != N ) {
        printf("n and N should be equal");
        return;
    }

    p[0] = p0;
    for (int i=1; i<n; i++) {
        p[i] = p[i-1] + dt*(B*Q[i] - A*p[i-1]);
    }
}
;

