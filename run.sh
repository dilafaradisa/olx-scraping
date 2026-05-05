#!/bin/bash

echo "========== Start Orchestration Process =========="

# export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

VENV_PATH="/Users/dilafaradisa/Documents/disa/05_pacmann/03_into_to_devops/pandas/mentoring/venv/bin/activate"

PYTHON_SCRIPT="/Users/dilafaradisa/Documents/disa/05_pacmann/03_into_to_devops/pandas/mentoring/main_etl.py"

source "$VENV_PATH"

python3 "$PYTHON_SCRIPT"
Why is she so perfectI will study with you
echo "========== End of Orchestration Process =========="