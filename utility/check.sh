set -euxo pipefail

mypy $(fd -e py)

pytest reef/tests/test.py

time for i in $(seq 1 100); do
  python reef/main.py --seed $i --no-file
done
