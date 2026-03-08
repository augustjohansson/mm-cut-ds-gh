#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "$DIR/test_dijitso.sh"
bash "$DIR/test_instant.sh"
bash "$DIR/test_ufl_cut_ds.sh"
bash "$DIR/test_fiat.sh"
bash "$DIR/test_ffc_cut_ds.sh"
bash "$DIR/test_dolfin.sh"
