from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, StringConstraints
from typing_extensions import Annotated

Base = declarative_base()

class UserOrm(Base):
    __tablename__ = "users"

    id = Column('id', Integer, primary_key=True)
    username = Column(String(25), unique=True, nullable = False)
    password = Column(String(50))

class User(BaseModel):
    model_config = ConfigDict(from_attributes = True)

    id: int
    username: Annotated[str, StringConstraints(max_length = 25)]
    password: Annotated[str, StringConstraints(max_length = 50)]

def user_to_user_orm(user: User) -> UserOrm:
    userOrm = UserOrm(
        id = user.id,
        username = user.username,
        password = user.password,
    )

    return userOrm

class PlanOrm(Base):
    __tablename__ = "plans"

    id = Column('id', Integer, primary_key=True)
    name = Column(String(50))
    description = Column(String(500))
    api_limit = Column(Integer)

class Plan(BaseModel):
    model_config = ConfigDict(from_attributes = True)

    id: int
    name: Annotated[str, StringConstraints(max_length = 50)]
    description: Annotated[str, StringConstraints(max_length = 500)]
    api_limit: int

def convert_plan_to_plan_orm(plan: Plan) -> PlanOrm:
    plan_orm = PlanOrm(
        name=plan.name,
        description=plan.description,
        api_limit=plan.api_limit,
    )
    return plan_orm

class SubscriptionOrm(Base):
    __tablename__ = "subscriptions"

    id = Column('id', Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_id = Column(Integer, ForeignKey("plans.id"))

    def dict(self):
        return {
          "id": self.id,
          "user_id": self.user_id,
          "plan_id": self.plan_id,
        }

class Subscription(BaseModel):
    model_config = ConfigDict(from_attributes = True)

    id: int
    user_id: User
    plan_id: Plan

def subscription_to_subscription_orm(subs: Subscription) -> SubscriptionOrm:
    subs_orm = SubscriptionOrm(
        id = subs.id,
        user_id = subs.user_id.id,
        plan_id = subs.plan_id.id,
    )

    return subs_orm

class PermissionOrm(Base):
    __tablename__ = "permissions"

    id = Column('id', Integer, primary_key=True)
    name = Column(String(50))
    description = Column(String(500))

    def dict(self):
        return {
          "name": self.name,
          "description": self.description,
        }

class Permission(BaseModel):
    model_config = ConfigDict(from_attributes = True)

    id: int
    name: Annotated[str, StringConstraints(max_length = 50)]
    description: Annotated[str, StringConstraints(max_length = 500)]

def permission_to_permission_orm(permission: Permission) -> PermissionOrm:
    permission_orm = PermissionOrm(
        name = permission.name,
        description = permission.description,
    )

    return permission_orm

class PlanPermissionOrm(Base):
    __tablename__ = "plan_permissions"

    id = Column('id', Integer, primary_key=True)
    plan_id = Column(Integer, ForeignKey("plans.id"))
    permission_id = Column(Integer, ForeignKey("permissions.id"))

class PlanPermission(BaseModel):
    model_config = ConfigDict(from_attributes = True)

    id: int
    plan_id: Plan
    permission_id: Permission

def planpermission_to_planpermission_orm(planPermission: PlanPermission) -> PlanPermissionOrm:
    planPermissionOrm = PlanPermissionOrm(
        plan_id = planPermission.plan_id,
        permission_id = planPermission.permission.id,
    )

    return planPermissionOrm

class UsageOrm(Base):
    __tablename__ = "usage"

    id = Column('id', Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    permission_id = Column(Integer, ForeignKey("permissions.id"))
    count = Column(Integer)

class Usage(BaseModel):
    model_config = ConfigDict(from_attributes = True)

    id: int
    user_id: User
    permission_id: Permission
    count: int

def usage_to_usage_orm(usage: Usage) -> UsageOrm:
    usageOrm = UsageOrm(
        user_id = usage.user_id,
        permission_id = usage.permission_id,
        count = usage.count,
    )

    return usageOrm
