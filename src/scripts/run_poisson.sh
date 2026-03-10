#!/bin/bash

python3 -u poisson_convergence.py --geometry unitsquare 2>&1 | tee log-unitsquare.txt

python3 -u poisson_convergence.py --geometry unitcube 2>&1 | tee log-unitcube.txt
