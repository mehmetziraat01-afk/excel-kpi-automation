"""Shared SQLAlchemy column type helpers."""

from sqlalchemy import Numeric


QUANTITY_TYPE = Numeric(15, 3)
PRICE_TYPE = Numeric(15, 3)
ERROR_PERCENT_TYPE = Numeric(8, 3)
