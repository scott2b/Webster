# Starlight
Starter web application based on Starlette


```
 $ uvicorn app.main:app --reload
```


## Adding models

 * Add module to app.orm.models
 * import and inherit from Base
 * import the model into the app.orm __init__
 * run `alembic revision --autogenerate -m "Added .. "`
 * check the generated migration under _alembic/versions_
 * run `alembic upgrade head`

More info:

 * Alembic docs: [Auto-generating Migrations](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
