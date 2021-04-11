import motor.motor_asyncio
from fastapi import FastAPI, Request, status
from fastapi_users import FastAPIUsers, models
from fastapi_users.authentication import JWTAuthentication
from fastapi_users.db import MongoDBUserDatabase
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse


import requests
import httpx



DATABASE_URL = "mongodb://mongo:27017"
SECRET = "SECRET"

import uvicorn
import asyncio

loop = asyncio.get_event_loop()

#Convert the below syntax to odmantic if possible
class User(models.BaseUser):
    pass


class UserCreate(models.BaseUserCreate):
    pass


class UserUpdate(User, models.BaseUserUpdate):
    pass


class UserDB(User, models.BaseUserDB):
    pass


client = motor.motor_asyncio.AsyncIOMotorClient(
    DATABASE_URL, uuidRepresentation="standard"
)
db = client["database_name"]
collection = db["users"]
user_db = MongoDBUserDatabase(UserDB, collection)


def on_after_register(user: UserDB, request: Request):
    print(f"User {user.id} has registered.")


def on_after_forgot_password(user: UserDB, token: str, request: Request):
    print(f"User {user.id} has forgot their password. Reset token: {token}")


def after_verification_request(user: UserDB, token: str, request: Request):
    print(f"Verification requested for user {user.id}. Verification token: {token}")


jwt_authentication = JWTAuthentication(
    secret=SECRET, lifetime_seconds=3600, tokenUrl="/auth/jwt/login"
)

app = FastAPI()

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

templates = Jinja2Templates(directory="frontend/templates")


fastapi_users = FastAPIUsers(
    user_db,
    [jwt_authentication],
    User,
    UserCreate,
    UserUpdate,
    UserDB,
)
app.include_router(
    fastapi_users.get_auth_router(jwt_authentication), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(on_after_register), prefix="/auth", tags=["auth"]
)
app.include_router(
    fastapi_users.get_reset_password_router(
        SECRET, after_forgot_password=on_after_forgot_password
    ),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(
        SECRET, after_verification_request=after_verification_request
    ),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(fastapi_users.get_users_router(), prefix="/users", tags=["users"])


@app.get("/dashboard",response_class=HTMLResponse)
async def dashboard(request: Request):


    
    return templates.TemplateResponse('index.html',{"request": request})


@app.get("/registers",response_class=HTMLResponse)
async def registers(request: Request):


    # response = requests.post('http://localhost:8090/auth/register', headers=headers, data=data)
    
    return templates.TemplateResponse('register.html',{"request": request})




@app.post("/register")
async def register(request: Request):


    form = await request.form()
    print(form)

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = {
        "email":form['email'],
        "password":form['password'],
        "is_active":True,
        "is_superuser":False,
        "is_verified":False}


    print(data)
    
    async with httpx.AsyncClient() as client:
        resp = await client.post('http://0.0.0.0:8080/auth/register',json=data, headers=headers)

    print(resp)
    return RedirectResponse(url="/registers", status_code=303)


@app.post("/login")
async def login(request: Request):


    form = await request.form()
    print(form)

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
    'username': form['username'],
    'password': form['password'],
    }


    # print(data)
    #Handle invalid creds
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post('http://0.0.0.0:8080/auth/jwt/login',data=data, headers=headers)
  
        
        updated_headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {resp.json()["access_token"]}',
        }
    except Exception as exc:
        print(exc) #key error 
        return RedirectResponse(url=f"http://localhost:8080/logins", status_code=303)
    # print(resp.json())




    async with httpx.AsyncClient() as client:
        resp = await client.get('http://0.0.0.0:8080/users/me', headers=updated_headers)

    user_id=resp.json()["id"]
    if resp.status_code == 200:
        return RedirectResponse(url=f"http://localhost:8080/dashboard/{user_id}", status_code=303)
    else:
        return templates.TemplateResponse('login.html',{"request": request})


@app.get("/logins",response_class=HTMLResponse)
async def logins(request: Request):
    return templates.TemplateResponse('login.html',{"request": request})


# for when you run python3
if __name__ == '__main__':

    config = uvicorn.Config(app=app, host = "0.0.0.0", port=8080, loop=loop)
    server = uvicorn.Server(config)
    loop.run_until_complete(server.serve())
