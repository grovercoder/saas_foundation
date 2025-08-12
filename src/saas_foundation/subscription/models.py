from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class Limit:
    id: int

    key: str
    name: str
    description: str
    default_value: Any


@dataclass
class Feature:
    id: int

    key: str
    name: str
    description: str
    permissions: List[str] = field(default_factory=list)


@dataclass
class Tier:
    id: int

    key: str
    status: str  # active:public, active:private, draft, deactivated
    name: str
    description: str
    monthly_cost: float
    yearly_cost: float
    stripe_product_id: Optional[str] = None
    monthly_price_id: Optional[str] = None
    yearly_price_id: Optional[str] = None
    features: List[Feature] = field(default_factory=list)
    limits: Dict[str, Any] = field(default_factory=dict)  # key: value
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Subscription:
    id: int

    account_id: str
    tier_id: str
    stripe_subscription_id: str
    status: str  # e.g., active, canceled, past_due
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self):
        return {
            "id": self.id,
            "account_id": self.account_id,
            "tier_id": self.tier_id,
            "stripe_subscription_id": self.stripe_subscription_id,
            "status": self.status,
            "current_period_start": (
                self.current_period_start.isoformat()
                if self.current_period_start
                else None
            ),
            "current_period_end": (
                self.current_period_end.isoformat() if self.current_period_end else None
            ),
            "cancel_at_period_end": self.cancel_at_period_end,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
