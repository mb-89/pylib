# brief
pylib is a library that contains reusable features and boilerplate for python projects.

# dependency installation
```
winget python
py -m pip install uv
```

# Powershell cmds to get started

To run this package directly from git without installing anything:
```
powershell
$url = "git+https://<repo_url>"     #   repo_url is the url where the git remote is hosted
uvx --from $url pylib               #   opens the docu browser with more details
```

To run this package from local code:
```
powershell
cd <repo_dir>                       #   repo_dir is the directory that this file is in
uv run pylib                        #   opens the docu browser with more details
```

To install this package as system-wide tool
```
powershell
$url = "git+https://<repo_url>"     #   repo_url is the url where the git remote is hosted
uv tool install --from $url pylib   #   install the tool
uv tool upgrader pylib              #   Fetch the latest version. Not needed directly after install.
```