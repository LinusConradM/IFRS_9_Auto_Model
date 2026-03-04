"""Parameter lookup service for PD, LGD, EAD"""
from typing import Optional
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from src.db.models import ParameterSet, ParameterType, CustomerType
from src.utils.logging_config import get_logger
from src.utils.cache import get_cache, set_cache

logger = get_logger(__name__)


class ParameterService:
    """Service for looking up risk parameters (PD, LGD, EAD)"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache_ttl = 3600  # 1 hour cache
    
    def get_pd(self, customer_type: CustomerType, product_type: str, 
               credit_rating: Optional[str], time_horizon_months: int,
               effective_date: date) -> Decimal:
        """
        Get Probability of Default parameter.
        
        Supports segmentation by:
        - Customer type (RETAIL, SME, CORPORATE, etc.)
        - Product type (LOAN, BOND, etc.)
        - Credit rating
        - Time horizon (12 months for Stage 1, lifetime for Stage 2/3)
        
        Args:
            customer_type: Customer type
            product_type: Product/instrument type
            credit_rating: Credit rating (optional)
            time_horizon_months: Time horizon in months
            effective_date: Effective date for parameter lookup
            
        Returns:
            PD value
        """
        # Build cache key
        cache_key = f"pd:{customer_type.value}:{product_type}:{credit_rating}:{time_horizon_months}:{effective_date}"
        
        # Check cache
        cached_value = get_cache(cache_key)
        if cached_value is not None:
            logger.debug(f"PD cache hit: {cache_key}")
            return Decimal(str(cached_value))
        
        # Query database
        query = self.db.query(ParameterSet).filter(
            ParameterSet.parameter_type == ParameterType.PD,
            ParameterSet.is_active == True,
            ParameterSet.effective_date <= effective_date
        )
        
        # Apply segmentation filters
        if customer_type:
            query = query.filter(ParameterSet.customer_type == customer_type)
        if product_type:
            query = query.filter(ParameterSet.product_type == product_type)
        if credit_rating:
            query = query.filter(ParameterSet.credit_rating == credit_rating)
        if time_horizon_months:
            query = query.filter(ParameterSet.time_horizon_months == time_horizon_months)
        
        # Order by effective_date descending to get most recent
        query = query.order_by(ParameterSet.effective_date.desc())
        
        parameter = query.first()
        
        if parameter:
            pd_value = parameter.value
            logger.info(f"PD found: {pd_value} for {customer_type.value}/{product_type}")
        else:
            # Fallback to default
            pd_value = Decimal("0.02")  # 2% default
            logger.warning(f"No PD found for {customer_type.value}/{product_type}, using default {pd_value}")
        
        # Cache result
        set_cache(cache_key, float(pd_value), expire=self.cache_ttl)
        
        return pd_value
    
    def get_lgd(self, customer_type: CustomerType, product_type: str,
                credit_rating: Optional[str], effective_date: date) -> Decimal:
        """
        Get Loss Given Default parameter.
        
        Args:
            customer_type: Customer type
            product_type: Product/instrument type
            credit_rating: Credit rating (optional)
            effective_date: Effective date for parameter lookup
            
        Returns:
            LGD value
        """
        # Build cache key
        cache_key = f"lgd:{customer_type.value}:{product_type}:{credit_rating}:{effective_date}"
        
        # Check cache
        cached_value = get_cache(cache_key)
        if cached_value is not None:
            logger.debug(f"LGD cache hit: {cache_key}")
            return Decimal(str(cached_value))
        
        # Query database
        query = self.db.query(ParameterSet).filter(
            ParameterSet.parameter_type == ParameterType.LGD,
            ParameterSet.is_active == True,
            ParameterSet.effective_date <= effective_date
        )
        
        # Apply segmentation filters
        if customer_type:
            query = query.filter(ParameterSet.customer_type == customer_type)
        if product_type:
            query = query.filter(ParameterSet.product_type == product_type)
        if credit_rating:
            query = query.filter(ParameterSet.credit_rating == credit_rating)
        
        # Order by effective_date descending
        query = query.order_by(ParameterSet.effective_date.desc())
        
        parameter = query.first()
        
        if parameter:
            lgd_value = parameter.value
            logger.info(f"LGD found: {lgd_value} for {customer_type.value}/{product_type}")
        else:
            # Fallback to default
            lgd_value = Decimal("0.45")  # 45% default
            logger.warning(f"No LGD found for {customer_type.value}/{product_type}, using default {lgd_value}")
        
        # Cache result
        set_cache(cache_key, float(lgd_value), expire=self.cache_ttl)
        
        return lgd_value
    
    def get_ead(self, customer_type: CustomerType, product_type: str,
                outstanding_balance: Decimal, effective_date: date) -> Decimal:
        """
        Get Exposure at Default parameter.
        
        For most instruments, EAD = outstanding balance.
        For revolving facilities, EAD includes credit conversion factor for undrawn amounts.
        
        Args:
            customer_type: Customer type
            product_type: Product/instrument type
            outstanding_balance: Current outstanding balance
            effective_date: Effective date for parameter lookup
            
        Returns:
            EAD value
        """
        # Build cache key
        cache_key = f"ead:{customer_type.value}:{product_type}:{effective_date}"
        
        # Check cache for credit conversion factor
        cached_ccf = get_cache(cache_key)
        
        if cached_ccf is None:
            # Query database for credit conversion factor
            query = self.db.query(ParameterSet).filter(
                ParameterSet.parameter_type == ParameterType.EAD,
                ParameterSet.is_active == True,
                ParameterSet.effective_date <= effective_date
            )
            
            if customer_type:
                query = query.filter(ParameterSet.customer_type == customer_type)
            if product_type:
                query = query.filter(ParameterSet.product_type == product_type)
            
            query = query.order_by(ParameterSet.effective_date.desc())
            parameter = query.first()
            
            if parameter:
                cached_ccf = float(parameter.value)
                logger.info(f"EAD CCF found: {cached_ccf} for {customer_type.value}/{product_type}")
            else:
                cached_ccf = 1.0  # Default: EAD = outstanding balance
                logger.debug(f"No EAD CCF found, using default 1.0")
            
            # Cache result
            set_cache(cache_key, cached_ccf, expire=self.cache_ttl)
        
        # For MVP, EAD = outstanding balance × credit conversion factor
        ead_value = outstanding_balance * Decimal(str(cached_ccf))
        
        return ead_value
    
    def get_discount_rate(self, product_type: str, effective_date: date) -> Decimal:
        """
        Get discount rate for present value calculations.
        
        Args:
            product_type: Product/instrument type
            effective_date: Effective date for parameter lookup
            
        Returns:
            Discount rate
        """
        # Build cache key
        cache_key = f"discount_rate:{product_type}:{effective_date}"
        
        # Check cache
        cached_value = get_cache(cache_key)
        if cached_value is not None:
            return Decimal(str(cached_value))
        
        # Query database
        query = self.db.query(ParameterSet).filter(
            ParameterSet.parameter_type == ParameterType.DISCOUNT_RATE,
            ParameterSet.is_active == True,
            ParameterSet.effective_date <= effective_date
        )
        
        if product_type:
            query = query.filter(ParameterSet.product_type == product_type)
        
        query = query.order_by(ParameterSet.effective_date.desc())
        parameter = query.first()
        
        if parameter:
            rate = parameter.value
            logger.info(f"Discount rate found: {rate} for {product_type}")
        else:
            rate = Decimal("0.12")  # 12% default
            logger.warning(f"No discount rate found for {product_type}, using default {rate}")
        
        # Cache result
        set_cache(cache_key, float(rate), expire=self.cache_ttl)
        
        return rate
    
    def get_sicr_threshold(self, threshold_type: str, effective_date: date) -> Decimal:
        """
        Get SICR threshold parameter.
        
        Args:
            threshold_type: Type of threshold (e.g., 'pd_increase_ratio', 'absolute_pd')
            effective_date: Effective date for parameter lookup
            
        Returns:
            Threshold value
        """
        # Build cache key
        cache_key = f"sicr_threshold:{threshold_type}:{effective_date}"
        
        # Check cache
        cached_value = get_cache(cache_key)
        if cached_value is not None:
            return Decimal(str(cached_value))
        
        # Query database
        query = self.db.query(ParameterSet).filter(
            ParameterSet.parameter_type == ParameterType.SICR_THRESHOLD,
            ParameterSet.segment == threshold_type,
            ParameterSet.is_active == True,
            ParameterSet.effective_date <= effective_date
        )
        
        query = query.order_by(ParameterSet.effective_date.desc())
        parameter = query.first()
        
        if parameter:
            threshold = parameter.value
            logger.info(f"SICR threshold found: {threshold} for {threshold_type}")
        else:
            # Default thresholds
            defaults = {
                'pd_increase_ratio': Decimal("2.0"),  # 100% increase (2x)
                'absolute_pd': Decimal("0.20")  # 20%
            }
            threshold = defaults.get(threshold_type, Decimal("2.0"))
            logger.warning(f"No SICR threshold found for {threshold_type}, using default {threshold}")
        
        # Cache result
        set_cache(cache_key, float(threshold), expire=self.cache_ttl)
        
        return threshold
    
    def invalidate_cache(self, parameter_type: Optional[ParameterType] = None):
        """
        Invalidate parameter cache.
        
        Called when parameters are updated to force fresh lookups.
        
        Args:
            parameter_type: Specific parameter type to invalidate, or None for all
        """
        # In production, would use Redis pattern matching to delete keys
        # For MVP, cache will expire naturally after TTL
        logger.info(f"Parameter cache invalidation requested for {parameter_type}")
