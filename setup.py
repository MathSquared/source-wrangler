from setuptools import setup

setup(
    name="source-wrangler",
    version="0.1",
    author="MathSquared",
    description="A source manager for research projects (not source code)",
    license="MIT",
    packages=["sourcewrangler"],
    entry_points={
        "console_scripts": [
            "sw = sourcewrangler:main",
        ],
    },
    test_suite="tests",
)
