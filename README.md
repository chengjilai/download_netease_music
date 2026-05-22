# download_netease_music
Download music from NetEase Cloud Music

## Setup

```shell
# 1. Clone and enter
git clone git@github.com:chengjilai/download_netease_music && cd download_netease_music
# 2. Get native libs (one-time)
mkdir -p lib
curl -sL "$(curl -s https://api.github.com/repos/2061360308/MusicLibrary/releases/latest \
  | python3 -c 'import json,sys; [print(a["browser_download_url"]) for a in json.load(sys.stdin)["assets"] if "linux-x64" in a["name"]]')" \
  -o /tmp/ncm.zip && unzip -j /tmp/ncm.zip 'lib/*.so' -d lib/ && rm /tmp/ncm.zip
```

## Usage

```shell
python3 netease_dl.py
```

First run prompts for phone → SMS code → login. Session saved.
Subsequent runs: just type a keyword, pick a number.

## Credits

| Component | Source | License |
|-----------|--------|---------|
| `lib/*.so` | [2061360308/MusicLibrary](https://github.com/2061360308/MusicLibrary) | MIT |
| `core.py`, `common.py` | [2061360308/NeteaseCloudMusic_PythonSDK](https://github.com/2061360308/NeteaseCloudMusic_PythonSDK) | MIT |
