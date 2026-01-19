# brief
$TODO$

# dependency installation
```
winget python
py -m pip install uv
```

# Powershell cmds to get started
To run this package from local code:
```
powershell
cd <repo_dir> # repo_dir is the directory that this file is in
uv run $PKG$ # opens the docu browser with more details
```

To run this package directly from git without installing anything:
```
powershell
$url = "git+https://<repo_url>" #repo_url is the url where the git remote is hosted
uvx --from $url $PKG$ opens the docu browser with more details
```