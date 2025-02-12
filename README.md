```bash
mkdir -p packages  # 패키지를 저장할 디렉토리 생성
pip download --platform manylinux2014_x86_64 --only-binary=:all: -d packages -r requirements.txt
```

- 압축해서 리눅스환경으로 옮기기기

```bash
tar -czvf python_env.tar.gz packages requirements.txt
필요시 logging_config.py main.py middleware.py schemas.py utils.py README.md
```

- 압축해제 하기기

```bash
tar -xzvf python_env.tar.gz
```

## 리눅스에서 사용할 파이썬 3.10.5 다운로드드

```bash
curl -O https://www.python.org/ftp/python/3.10.5/Python-3.10.5-linux-x86_64.tar.xz
```

```bash
mv /path/to/USB/Python-3.10.5-linux-x86_64.tar.xz ~/
tar -xzvf Python-3.10.5-linux-x86_64.tar.xz
cd Python-3.10.5
./bin/python3.10 --version

```

```bash
./bin/python3.10 -m venv .venv
source .venv/bin/activate
```

### 리눅스에서 pip 오프라인설치

```bash
pip install --no-index --find-links=packages -r requirements.txt
```
