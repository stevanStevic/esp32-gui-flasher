#!/usr/bin/env python
"""esp32_gui_flasher setup script."""
import os

from setuptools import setup, find_packages

from esp_flasher import const

PROJECT_NAME = 'ESP32 GUI Flash Download Tool'
PROJECT_PACKAGE_NAME = 'esp32_gui_flasher'
PROJECT_LICENSE = 'MIT'
PROJECT_AUTHOR = 'Stevan Stevic'
PROJECT_COPYRIGHT = '2025, Stevan Stevic'
PROJECT_URL = 'https://github.com/stevanStevic/esp32-gui-flasher'
PROJECT_EMAIL = 'stevan.stevic@proton.me'

PROJECT_GITHUB_USERNAME = 'stevanStevic'
PROJECT_GITHUB_REPOSITORY = 'esp32-gui-flasher'

PYPI_URL = 'https://pypi.python.org/pypi/{}'.format(PROJECT_PACKAGE_NAME)
GITHUB_PATH = '{}/{}'.format(PROJECT_GITHUB_USERNAME, PROJECT_GITHUB_REPOSITORY)
GITHUB_URL = 'https://github.com/{}'.format(GITHUB_PATH)

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'requirements.txt')) as requirements_txt:
    REQUIRES = requirements_txt.read().splitlines()

with open(os.path.join(here, 'README.md')) as readme:
    LONG_DESCRIPTION = readme.read()


setup(
    name=PROJECT_PACKAGE_NAME,
    version=const.__version__,
    license=PROJECT_LICENSE,
    url=GITHUB_URL,
    author=PROJECT_AUTHOR,
    author_email=PROJECT_EMAIL,
    description="ESP32 GUI Flash Download Tool with Connection to Thermal Printer.",
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    test_suite='tests',
    python_requires='>=3.8,<4.0',
    install_requires=REQUIRES,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    keywords=['esp32', 'automation', 'flash'],
    entry_points={
        'console_scripts': [
            'esp_flasher = esp_flasher.__main__:main'
        ]
    },
    packages=find_packages(include="esprelease.*")
)
