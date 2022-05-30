from codecs import open
from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))


def readme():
    try:
        with open('README.md') as f:
            return f.read()
    except BaseException:
        pass


setup(
    name='ycl',
    version='1.1.0',
    description='youtube control via command line',
    long_description=readme(),
    long_description_content_type='text/markdown',
    author='Subhrajit Prusty',
    author_email='subhrajit1997@gmail.com',
    url='http://github.com/SubhrajitPrusty/ycl',
    setup_requires=['setuptools>=40.0.0'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'python-dotenv',
        'requests',
        'yt-dlp',
        'loguru',
        'windows-curses; platform_system == "Windows"',
        'python-vlc'
    ],
    entry_points={
        'console_scripts': [
            'ycl = ycl.cli:main'
        ]
    },
)
