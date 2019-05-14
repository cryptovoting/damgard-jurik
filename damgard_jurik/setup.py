import setuptools

setuptools.setup(
    name="cryptovote",
    version="0.0.1",
    author="Boucher, Govedič, Saowakon, Swanson",
    description="Secure, verifiable electronic voting using the"
                "Paillier cryptosystem",
    long_description="Enables the implementation of elections where each vote "
                     "is cryptographically secured using the Pallier "
                     "cryptosystem and the results of elections are "
                     "verifiable via a public bulletin board.",
    url="https://github.com/swansonk14/crypto-voting",
    packages=setuptools.find_packages(),
    install_requires=[
        'gmpy2',
        'tqdm'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ]
)
