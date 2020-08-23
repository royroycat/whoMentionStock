# whoMentionStock

### docker-compose.yml
- change the root password and user password of mysql

### create instance/config.py
- instance config is [FLASK stuff](https://flask.palletsprojects.com/en/1.1.x/config/)
- mkdir instance in app folder
- you should copy the config.py from root 
- change the sql password, twitter token and telegram bot token 

### start your engine!
`docker-compose -f docker-compose.xml up`

### ADMINER
- installed adminer for manage the program
- ip:8080 to access your db by [ADMINER](https://www.adminer.org/)
