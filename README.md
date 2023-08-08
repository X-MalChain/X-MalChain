# X-MalChain
Our goal is to provide a platform that can explain malware, specifically, to output the malicious behavior chains (MalChain) of malware to explain how malware executes and performs malicious behavior.

![image](https://github.com/X-MalChain/x-malchain/assets/141179257/2d79635a-03b1-4285-9368-29c42a36071f)


## Our Advantages
- Detect malicious behaviors in malware as accurately as possible.
- Explain the given malware with the help of **_Malicious Behavior Chains_**.
- Using ChatGpt, generate a brief but clear description to explain why the application is classfied as malware with the help of malicious behavior chains.

## Development Environment
### Project Package Overview
- _common_: Design the model or class of database.
- _createkg_: Draw a knowledge graph with Neo4j.
- _detect & verify_: Detect malicious behaviors. Note that, this is an early version, and the latest version is in X-MalChain.py.
- _exper & exper1_: Implement the codes to conduct our experiments.
- _manager_: Design a background management system for our web service.
- _mwep_: The configuration package of the project itself.
- _tools_: Some codes acting as tools for this project.
- _sb.sqlite3_: database.
- _manage.py_: manage codes.
  
### Operate System
This project is developed on Ubuntu 20.04.
### Language & IDE & Framework
Using python 3.8, we choose Pycharm to implement our Django project.
### Installation of important packages
- Androguard
```angular2html
sudo apt-get install sqlite sqlite3
sudo apt-get install libsqlite3-dev
sqlite3 version
```
- Django
```angular2html
python -m pip install Django
#  Edit Table Data
python manage.py makemigrations
python manage.py migrate
```

## Web
Note that,our project for web is also an open source at [Our Web Project](https://github.com/X-MalChain/projects).
