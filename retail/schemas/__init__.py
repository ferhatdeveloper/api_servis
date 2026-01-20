"""
RetailOS - API Schemas
"""

from .auth import Token, TokenData, UserLogin
from .product import (
    Product,
    ProductCreate,
    ProductUpdate,
    ProductList,
    ProductBarcode
)
from .customer import (
    Customer,
    CustomerCreate,
    CustomerUpdate,
    CustomerDetail,
    CustomerList,
    CustomerLoyalty
)
from .sale import (
    Sale,
    SaleCreate,
    SaleUpdate,
    SaleDetail,
    SaleList,
    SaleItem,
    SaleItemCreate,
    PaymentCreate,
    SaleCancel,
    SaleStatistics
)

__all__ = [
    # Auth
    'Token',
    'TokenData',
    'UserLogin',
    # Product
    'Product',
    'ProductCreate',
    'ProductUpdate',
    'ProductList',
    'ProductBarcode',
    # Customer
    'Customer',
    'CustomerCreate',
    'CustomerUpdate',
    'CustomerDetail',
    'CustomerList',
    'CustomerLoyalty',
    # Sale
    'Sale',
    'SaleCreate',
    'SaleUpdate',
    'SaleDetail',
    'SaleList',
    'SaleItem',
    'SaleItemCreate',
    'PaymentCreate',
    'SaleCancel',
    'SaleStatistics',
]
