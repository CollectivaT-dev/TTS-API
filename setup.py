from setuptools import setup, find_packages

setup(
    name="tts-api",
    version="0.2",
    packages=find_packages(),
    install_requires=[
        "Flask",
        "gunicorn",
        "coqui-tts",
        "pydub",
        "nltk",
        "transformers",
        "torch",
    ],
)
