#Planar Backend

1. Set env:\
SECRET_KEY=*secret*\
CLIENT_ID=*secret*
DATABASE_URL=`postgresql://`*userid*`:`*pass*`@`*ip:port*`/`*name*

2. Init database with flask-migrate\
`manage.py init`\
`manage.py migrate`\
`manage.py upgrade`\
Might have to delete `/migrations` folder!

3. Run app.py
4. ???
5. Profit!
