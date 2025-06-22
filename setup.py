from setuptools import setup, find_packages

setup(
    name="neurogenius",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "transformers",
        "torch",
        "PySide6",
        "llama-index",
        "speechrecognition",
        "pyttsx3",
        "requests",
        "numpy",
        "pillow",
    ],
    include_package_data=True,
    description="NeuroGenius GPT - AI-powered platform for secure chat and document analysis.",
    author="Your Name",
    author_email="your_email@example.com",
    url="https://github.com/your-repo",  # Replace with your repository URL
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)