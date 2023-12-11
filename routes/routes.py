from fastapi import FastAPI, HTTPException,Request, APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.hash import bcrypt
from models.models import *
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

DATABASE_URL = "mysql+pymysql://root:nasm@localhost:3306/fastdb"
engine = create_engine(DATABASE_URL)

app = APIRouter()

##### User Creation ########

@app.post("/user")
async def create_user(user: User):
    session = Session(engine)
    user = user_to_user_orm(user)
    session.add(user)
    session.commit()
    return {"message": "User " + str(user.username) + " created successfully."}

@app.delete("user/delete/{user_id}")
async def delete_user(user_id: int):
    session = Session(engine)
    user = session.query(UserOrm).filter(UserOrm.id == user_id).first()
    username = user.username
    session.query(UserOrm).filter(UserOrm.id == user_id).delete()
    session.commit()
    return {"message" : "User " + str(username) + " deleted successfully."}

##### Subscription Plan Management #####

@app.post("/plans")
async def create_plan(plan: Plan):
    session = Session(engine)
    plan = convert_plan_to_plan_orm(plan)
    session.add(plan)
    session.commit()
    return {"message": str(plan.name) + " plan created sucessfully."}

@app.put("/plans/modeify/{plan_id}")
async def modify_plan(plan_id: int, plan_update: Plan):
    session = Session(engine)
    plan = convert_plan_to_plan_orm(plan)
    session.query(Plan).filter(Plan.id == plan_id).update(plan_update.dict())
    session.commit()

    return {"message": "Plan updated successfully."}

@app.delete("/plans/delete/{plan_id}")
async def delete_plan(plan_id: int):
    session = Session(engine)
    plan = session.query(PlanOrm).filter(PlanOrm.id == plan_id).first()
    session.query(PlanOrm).filter(PlanOrm.id == plan_id).delete()
    session.commit()
    return {"message": str(plan.name) + "plan deleted successfully."}

##### Persmission handling #####

@app.post("/permissions")
async def add_permission(permission: Permission):
    session = Session(engine)
    permission = permission_to_permission_orm(permission)
    session.add(permission)
    session.commit()
    return {"message": "Permission added successfully."}

@app.put("/permissions/modify/{permission_id}")
async def modify_permission(permission_id: int, permission_update: Permission):
    session = Session(engine)
    permission_update = permission_to_permission_orm(permission_update)
    session.query(PermissionOrm).filter(PermissionOrm.id == permission_id).update(permission_update.dict())
    session.commit()
    return {"message": "Permission updated successfully."}

@app.delete("/permissions/delete/{permission_id}")
async def delete_permission(permission_id: int):
    session = Session(engine)
    session.query(PermissionOrm).filter(PermissionOrm.id == permission_id).delete()
    session.commit()
    return {"message": "Permission deleted successfully."}

##### User Subscription Handling #####

@app.post("/subscriptions")
async def subscribe_to_plan(subscription: Subscription):
    session = Session(engine)
    subscription = subscription_to_subscription_orm(subscription)
    session.add(subscription)
    session.commit()
    return {"message": "Subscribed to plan successfully."}

@app.get("/subscriptions/{user_id}")
async def view_subscription_details(user_id: int):
    session = Session(engine)
    user = session.query(UserOrm).filter(UserOrm.id == user_id).first()
    subscription = session.query(SubscriptionOrm).filter(SubscriptionOrm.user_id == user_id).first()
    if not subscription:
        raise HTTPException(404, "Subscription not found.")

    plan = session.query(PlanOrm).filter(PlanOrm.id == subscription.plan_id).first()

    return {"message": "Plan " + str(plan.name) + " is subscribed by " + str(user.username)}

@app.get("/subscriptions/{user_id}/usage")
async def view_usage_statistics(user_id: int):
    session = Session(engine)
    usage_data = session.query(UsageOrm).filter(UsageOrm.user_id == user_id).all()
    return usage_data

@app.put("/subscriptions/modify/{user_id}")
async def assign_modify_user_plan(user_id: int, plan_update: Subscription):
    session = Session(engine)
    plan_update = subscription_to_subscription_orm(plan_update)
    session.query(SubscriptionOrm).filter(SubscriptionOrm.user_id == user_id).update(plan_update.dict())
    session.commit()
    return {"message": "Subscription updated successfully."}

##### Access Control #####

@app.get("/access/{user_id}/{api_request}")
async def check_access_permission(user_id: int, api_request: str):
    session = Session(engine)
    # 1. Retrieve user's subscription
    subscription = session.query(SubscriptionOrm).filter(SubscriptionOrm.user_id == user_id).first()
    if not subscription:
        raise HTTPException(404, "Subscription not found.")

    # 2. Get allowed API permissions for the user's plan
    plan_permissions = session.query(PlanPermissionOrm).filter(PlanPermissionOrm.plan_id == subscription.plan_id).all()
    allowed_permissions = [p.permission_id for p in plan_permissions]

    # 3. Check if requested API permission is allowed
    api_permission = session.query(PermissionOrm).filter(PermissionOrm.name == api_request).first()
    if not api_permission:
        raise HTTPException(404, "API permission not found.")

    if api_permission.id not in allowed_permissions:
        raise HTTPException(403, "Access denied for this API.")

    # 4. Check and enforce API usage limit
    usage = session.query(UsageOrm).filter(UsageOrm.user_id == user_id, UsageOrm.permission_id == api_permission.id).first()
    plan = session.query(PlanOrm).filter(PlanOrm.id == subscription.plan_id).first()

    if usage and usage.count >= plan.api_limit:
        raise HTTPException(429, "API usage limit exceeded.")

    # Update usage count
    if usage:
        usage.count += 1
    else:
        new_usage = UsageOrm(user_id=user_id, permission_id=api_permission.id, count=1)
        session.add(new_usage)

    session.commit()

    return {"permission_granted": True}

#### Usage Tracking & Limit Enforcement #####

@app.post("/usage/{user_id}")
async def track_api_request(user_id: int, api_request: str):
    session = Session(engine)
    # 1. Get API permission
    api_permission = session.query(PermissionOrm).filter(PermissionOrm.name == api_request).first()
    if not api_permission:
        raise HTTPException(404, "API permission not found.")

    # 2. Check and update user's usage
    usage = session.query(UsageOrm).filter(UsageOrm.user_id == user_id, UsageOrm.permission_id == api_permission.id).first()
    if usage:
        usage.count += 1
    else:
        new_usage = UsageOrm(user_id=user_id, permission_id=api_permission.id, count=1)
        session.add(new_usage)
    session.commit()

    return {"message": "API usage tracked successfully."}

@app.get("/usage/{user_id}/limit")
async def check_limit_status(user_id: int, api_request: str):
    session = Session(engine)
    # 1. Get user's subscription and API permission
    subscription = session.query(SubscriptionOrm).filter(SubscriptionOrm.user_id == user_id).first()
    if not subscription:
        raise HTTPException(404, "Subscription not found.")

    api_permission = session.query(PermissionOrm).filter(PermissionOrm.name == api_request).first()
    if not api_permission:
        raise HTTPException(404, "API permission not found.")

    # 2. Check user's usage and plan limit
    usage = session.query(UsageOrm).filter(UsageOrm.user_id == user_id, UsageOrm.permission_id == api_permission.id).first()
    plan = session.query(PlanOrm).filter(PlanOrm.id == subscription.plan_id).first()

    if not usage or usage.count < plan.api_limit:
        is_limit_exceeded = False
    else:
        is_limit_exceeded = True

    return {"limit_exceeded": is_limit_exceeded}

@app.get("/")
async def root():
    return {"message": "My First FastAPI project"}
