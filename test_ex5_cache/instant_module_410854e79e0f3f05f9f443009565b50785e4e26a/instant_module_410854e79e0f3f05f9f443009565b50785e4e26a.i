%module  instant_module_410854e79e0f3f05f9f443009565b50785e4e26a
//%module (directors="1") instant_module_410854e79e0f3f05f9f443009565b50785e4e26a

//%feature("director");

%{
#include <iostream>

#include <numpy/arrayobject.h>



void sum (int m, int* mp, double* array1, int n, int* np, double* array2){
  int w = mp[0], x = mp[1], y = mp[2], z = mp[3];
  for (int i=0; i<w; i++)
    for (int j=0; j<x; j++)
      for (int k=0; k<y; k++)
        for (int l=0; l<z; l++){
          *array2 = *array1*2;
          array1++;
          array2++;
        }
}
    
%}

//%feature("autodoc", "1");
%include "numpy.i"

%init%{

import_array();

%}




//
%typemap(in) (int m,int* mp,double* array1){
  if (!PyArray_Check($input)) {
    PyErr_SetString(PyExc_TypeError, "Not a NumPy array");
    return NULL; ;
  }
  PyArrayObject* pyarray;
  pyarray = (PyArrayObject*)$input;
  $1 = int(pyarray->nd);
  int* dims = new int[$1];
  for (int d=0; d<$1; d++) {
     dims[d] = int(pyarray->dimensions[d]);
  }

  $2 = dims;
  $3 = (double*)pyarray->data;
}
%typemap(freearg) (int m,int* mp,double* array1){
    // deleting dims
    delete $2;
}

%typemap(in) (int n,int* np,double* array2){
  if (!PyArray_Check($input)) {
    PyErr_SetString(PyExc_TypeError, "Not a NumPy array");
    return NULL; ;
  }
  PyArrayObject* pyarray;
  pyarray = (PyArrayObject*)$input;
  $1 = int(pyarray->nd);
  int* dims = new int[$1];
  for (int d=0; d<$1; d++) {
     dims[d] = int(pyarray->dimensions[d]);
  }

  $2 = dims;
  $3 = (double*)pyarray->data;
}
%typemap(freearg) (int n,int* np,double* array2){
    // deleting dims
    delete $2;
}


void sum (int m, int* mp, double* array1, int n, int* np, double* array2){
  int w = mp[0], x = mp[1], y = mp[2], z = mp[3];
  for (int i=0; i<w; i++)
    for (int j=0; j<x; j++)
      for (int k=0; k<y; k++)
        for (int l=0; l<z; l++){
          *array2 = *array1*2;
          array1++;
          array2++;
        }
}
    ;

