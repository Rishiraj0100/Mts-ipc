from setuptools import setup, find_packages
import re

with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

version = ''
with open('mts_ipc/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('version is not set')

if version.endswith(('a', 'b', 'rc')):
    # append version identifier based on commit count
    try:
        import subprocess
        p = subprocess.Popen(['git', 'rev-list', '--count', 'HEAD'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            version += out.decode('utf-8').strip()
        p = subprocess.Popen(['git', 'rev-parse', '--short', 'HEAD'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if out:
            version += '+g' + out.decode('utf-8').strip()
    except Exception:
        pass

setup(
    name="mts-ipc",
    version=version,
    description="An IPC for discord.py. Making Discord bot websites development easier. ",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/Rishiraj0100/Mts-Ipc",
    author="Rishi dev",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
    ],
    python_requires=">=3.8",
    keywords="discord.py ipc",
    packages=find_packages(exclude=["tests","docs","requirements",".readthedocs"]),
)
