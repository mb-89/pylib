# brief
$TODO$
See [doc index](src/$PKG$/doc/000_index.md) for details.

# dependency installation
```
winget python
py -m pip install uv
```

# Powershell cmds to get started
These powershell commands run a preview directly from git without
installing anything. 
```
powershell
$url = "$TODO$"
uvx --from $url $PKG$ -x # show built-in examples and further reading
uvx --from $url $PKG$ -h # show commandline help
```

For details on how to install locally:
```
powershell
$url = "$TODO$"
uvx --from $url $PKG$ -i # show help on local installation and usage of uv
```