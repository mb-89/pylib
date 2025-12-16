# brief
pylib is a library that contains reusable features and boilerplate for python projects.
See [doc index](src/pylib/doc/000_index.md) for details.

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
$url = "git+https://code.siemens.com/shs-te-mp-plm-varc/pylib"
uvx --from $url pylib -x # show built-in examples and further reading
uvx --from $url pylib -h # show commandline help
```

For details on how to install locally:
```
powershell
$url = "git+https://code.siemens.com/shs-te-mp-plm-varc/pylib"
uvx --from $url pylib -i # show help on local installation and usage of uv
```