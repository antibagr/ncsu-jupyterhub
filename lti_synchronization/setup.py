import setuptools

with open("../README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='lti_synchronization',
    version='1.0.0',
    author="Anton Bagryanov",
    author_email="antibagr@yandex.ru",
    description="lti_synchronization package developed for NCSU.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/antibagr/ncsu-jupyterhub",
    project_urls={
        "Master branch": "https://github.com/antibagr/ncsu-jupyterhub/tree/master",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Linux",
    ],
    package_dir={"": "moodle"},
    packages=setuptools.find_packages(where="moodle"),
    python_requires=">=3.8",
)
