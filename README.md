# X-MalChain
Our goal is to provide a platform that can explain malware, specifically, to output the malicious behavior chains (MalChain) of malware to explain how malware executes and performs malicious behavior.

![image](https://github.com/X-MalChain/x-malchain/assets/141179257/2d79635a-03b1-4285-9368-29c42a36071f)


## Our Advantages
- Detect malicious behaviors in malware as accurately as possible.
- Explain the given malware with the help of **_<font color="#10c2c1">Malicious Behavior Chains</font>_**.
- Using ChatGpt, generate a brief but clear description to explain why the application is classfied as malware with the help of malicious behavior chains.

## Development Environment

### Project Package Overview
- common: Design the model or class of database.
- createkg: Draw a knowledge graph with Neo4j.
- detect & verify: Detect malicious behaviors. Note that, this is an early version, and the latest version is in X-MalChain.py.
- exper & exper1: Implement the codes to conduct our experiments.
- manager: Design a background management system for our web service.
- mwep: The configuration package of the project itself.
- Tools: Some codes acting as tools for this project.

### OS
### Language and IDE
### Framework
# Edit Table Data
```angular2html
python manage.py makemigrations
python manage.py migrate
```
