# -*- coding: utf-8 -*-

import importlib.metadata as imp_meta
import os.path as os_path
import re

import packaging.requirements as pkg_req

req_file = os_path.join('conda', 'requirements.txt')
spec_re = re.compile(r'\s*(===|!=|~=|==|<=|>=|<|>)\s*')


def normalise_requirement(line):
    req = line.strip()
    if not req or req.startswith('#'):
        return None

    if ';' in req:
        spec, marker = req.split(';', 1)
        return f'{spec_re.sub(r"\1", spec.strip())}; {marker.strip()}'
    return spec_re.sub(r'\1', req)


def pinned_requirement(req, version):
    spec = f'{req.name}=={version}'
    if req.marker is None:
        return spec
    return f'{spec}; {req.marker}'

data = {}  # dict[str, str]
with open(req_file) as file:
    for line in file:
        line = normalise_requirement(line)
        if line is None:
            continue
        req = pkg_req.Requirement(line)

        try:
            ver = imp_meta.version(req.name)
            data[req.name] = pinned_requirement(req, ver)
        except imp_meta.PackageNotFoundError:
            if req.marker is None:
                raise
            data[req.name] = f'{req.name} ; {req.marker}'

with open(req_file, 'w') as file:
    for key, line in sorted(data.items()):
        print(line, file=file)
