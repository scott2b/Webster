# Starlight


Starter web application based on Starlette

```
 $ uvicorn app.starlette.main:app --reload
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


## Managing dB Sessions

A number of approaches to managing dB sessions is provided. This is partly to
provide some flexibility, and partly to try to feel out what the best approach
might be.

### General principles

  * Use a thread-local scoped session. If I understand correctly, in the context of a web application, this will mean that the session will never outlive the request/response cycle. Would appreciate a correction on this if I am wrong.
  * Regardless of session scope .. still explicitly close sessions. I am looking at the scoped_session concept primarily as a backup to prevent leakage. I still think sessions should be closed explicitly.
  * Where it makes sense, manage the session lifecycle outside of the view code, but in a way that is still obvious to developers. To this end, the decorator and dependency injection based approaches are provided.

### Approaches to getting a db session


**Create a session directly**

__containers.SessionLocal__

```
db = SessionLocal()
db.query( ... )
db.commit()
db.close()
```

Advantages:

 * Explicit control
 * Maintainable ... no magic

Disadvantages:

 * Cluttered code
 * Potential to forget to close (might not be an issue for thread-local scoped sessions)


**Use the context manager**

__orm.db.session_scope__

```
with session_scope() as db:
    # do some query with db
```

Advantages:

 * Handles rollback (for exceptions)
 * Handles commit and close

Disadvantages:

 * You might not really need a commit, e.g. for select queries
 * A bit more clutter in view code than other approaches


**Use the db_session decorator**

__orm.db.db_session__

```
@db_session
def myview(request, db:Session):
    # do view stuff here
```
Uses session_scope under the hood, so has same advantages / disadvantages

Advantages:

 * Cleans a lot of clutter from code
 * Ensures commit and closure, and rollback for errors in view

Disadvantages:

 * Commit might not really be needed for some queries
 * Requires your view to take a db parameter

**Use dependency injection**

See details in the next section.


## Dependency injection of db sessions

Two db service providers are available in the container:

 * db. Provides a SessionLocal instance
 * closed_db. Provides a SessionLocal instance that is committed and closed when the function exits. Also handles rollback for exception conditions.


### With views

Wiring with view code seems a bit finicky. At the moment, I am unable to get
the api module wired for injection. It is not clear if maybe this is because
the api application is a mounted application.

In cases where you are able to get wiring to work, you may want to use
dependency injection, although it might be easier to use the db_session
decorator. Note that the session instance provided by the decorator is itself
injected, so you can still do things like provide alternative container
services, e.g. for testing purposes.


### In the ORM layer

SQLAlchemy, more than other ORMs I have used, lends itself to usage patterns
where you tend to see session objects passed around a lot. This can be both
good and bad ... but for a lot of use cases it would be nice to get that
handling out of the way. One way to do that is via dependency injection.

An interesting pattern that I am exploring (subject to review and critique!!)
is that of the optional session parameter. You can see this usage, for example,
in orm.oauth2.token.create.

With this pattern, a Session object can be provided (via the db argument), in
which case, the caller has the responsibility of rollback, commit, close. You
would do this in the case where this is one of a series of operations for a
combined transaction scope. If a Session is not explicitly provided, one is
injected via Closing wiring so that the lifecycle (commit & close) is
automatically handled over the scope of the function.

**Important Note:** In order for this pattern to allow for returned objects to be
usable by the caller, the injected Session must be created with `expire_on_commit=False`
so that the object is available after the session is closed. Also, this should
only be used with thread-local session scope as exceptions cannot be caught by
the service provider.


## API documentation

Currently, only redoc is implemented. Swagger requires authentication, which
has not yet been sorted out.

SpecTree will let us pass a pydantic validation model to validate as the
`cookies` parameter. However, [Swagger v3 does not yet support automatically
passing cookies](https://github.com/swagger-api/swagger-ui/issues/2895). Thus,
we would need to manually submit cookies via the Swagger UI, or integrate oauth
into how we present swagger.



 * The openapi spec is available at /docs/openapi.json

 * Redoc is at /docs/api
