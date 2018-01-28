#-*- coding:utf-8 -*-
__author__ = 'liucaiyun'


from rolepermissions.roles import AbstractUserRole


class SystemAdmin(AbstractUserRole):

    available_permissions = {
        'create_user': True,
    }


class PurchasingAgent(AbstractUserRole):
    # 采购员
    available_permissions = {
        'create_purchasing_order': True,
        'edit_purchasing_order': True
    }


class Finance(AbstractUserRole):
    # 财务
    available_permissions = {
        'edit_purchasing_order': True,
        'approve_purchasing_order': True
    }


class GodownManager(AbstractUserRole):
    # 仓库管理员
    available_permissions = {
        'edit_patient_file': True,
    }


class Operator(AbstractUserRole):
    # 运营人员
    available_permissions = {
        'edit_oversea_shipment': True,      # 允许移库
    }