set -euxo pipefail

mypy *py

pytest test.py

time for i in $(seq 1 100); do
  python main.py --seed $i > /dev/null
done
