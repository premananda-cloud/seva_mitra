# admin/merchant_routes.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import logging

router = APIRouter(prefix="/admin/merchants", tags=["admin-merchants"])
logger = logging.getLogger(__name__)

# Pydantic models
class MerchantCreate(BaseModel):
    department: str
    merchant_name: str
    gateway_type: str
    api_key: str
    api_secret: str
    merchant_id_ref: Optional[str] = None
    webhook_secret: Optional[str] = None
    environment: str = "sandbox"
    gateway_config: dict = {}
    is_default: bool = False

class MerchantUpdate(BaseModel):
    merchant_name: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    merchant_id_ref: Optional[str] = None
    webhook_secret: Optional[str] = None
    environment: Optional[str] = None
    gateway_config: Optional[dict] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

class PaymentMethodConfig(BaseModel):
    payment_method: str
    is_enabled: bool = True
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    sort_order: int = 0
    additional_config: dict = {}

# API Endpoints
@router.post("/")
async def create_merchant(config: MerchantCreate, admin_id: str = Depends(get_current_admin)):
    """Create a new merchant configuration"""
    try:
        # Encrypt sensitive data
        encrypted_api_key = encrypt_value(config.api_key)
        encrypted_api_secret = encrypt_value(config.api_secret)
        encrypted_webhook = encrypt_value(config.webhook_secret) if config.webhook_secret else None
        
        # Insert into database
        query = """
            INSERT INTO payment_merchants 
            (department, merchant_name, gateway_type, api_key, api_secret, 
             merchant_id_ref, webhook_secret, environment, gateway_config, 
             is_default, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING merchant_id, created_at
        """
        
        result = await db.execute(
            query,
            (
                config.department,
                config.merchant_name,
                config.gateway_type,
                encrypted_api_key,
                encrypted_api_secret,
                config.merchant_id_ref,
                encrypted_webhook,
                config.environment,
                json.dumps(config.gateway_config),
                config.is_default,
                admin_id
            )
        )
        
        # Log the action
        await log_merchant_action(
            merchant_id=result['merchant_id'],
            action='CREATE',
            changed_by=admin_id,
            new_values=config.dict()
        )
        
        return {
            "success": True,
            "merchant_id": result['merchant_id'],
            "message": f"Merchant {config.merchant_name} created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating merchant: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
async def list_merchants(
    department: Optional[str] = None,
    gateway_type: Optional[str] = None,
    environment: Optional[str] = None,
    active_only: bool = True,
    admin_id: str = Depends(get_current_admin)
):
    """List all merchants with optional filters"""
    
    query = """
        SELECT 
            merchant_id, department, merchant_name, gateway_type,
            environment, is_active, is_default, created_at,
            -- Mask sensitive data
            CASE WHEN api_key IS NOT NULL THEN '••••••••' ELSE NULL END as api_key_masked,
            CASE WHEN api_secret IS NOT NULL THEN '••••••••' ELSE NULL END as api_secret_masked
        FROM payment_merchants
        WHERE 1=1
    """
    params = []
    
    if department:
        query += " AND department = %s"
        params.append(department)
    if gateway_type:
        query += " AND gateway_type = %s"
        params.append(gateway_type)
    if environment:
        query += " AND environment = %s"
        params.append(environment)
    if active_only:
        query += " AND is_active = true"
    
    query += " ORDER BY department, is_default DESC, merchant_name"
    
    results = await db.fetch_all(query, params)
    return {"success": True, "merchants": results}

@router.get("/{merchant_id}")
async def get_merchant(merchant_id: str, admin_id: str = Depends(get_current_admin)):
    """Get merchant details (with masked sensitive data)"""
    
    query = """
        SELECT 
            merchant_id, department, merchant_name, gateway_type,
            environment, is_active, is_default, gateway_config,
            -- Return masked values for display
            CASE WHEN api_key IS NOT NULL THEN '••••••••' ELSE NULL END as api_key_masked,
            CASE WHEN api_secret IS NOT NULL THEN '••••••••' ELSE NULL END as api_secret_masked,
            merchant_id_ref,
            created_at, updated_at, created_by
        FROM payment_merchants
        WHERE merchant_id = %s
    """
    
    result = await db.fetch_one(query, (merchant_id,))
    if not result:
        raise HTTPException(status_code=404, detail="Merchant not found")
    
    # Get payment methods
    methods_query = """
        SELECT payment_method, is_enabled, min_amount, max_amount, sort_order
        FROM payment_method_config
        WHERE merchant_id = %s
        ORDER BY sort_order
    """
    methods = await db.fetch_all(methods_query, (merchant_id,))
    
    return {
        "success": True,
        "merchant": result,
        "payment_methods": methods
    }

@router.put("/{merchant_id}")
async def update_merchant(
    merchant_id: str, 
    updates: MerchantUpdate, 
    admin_id: str = Depends(get_current_admin)
):
    """Update merchant configuration"""
    
    # Get current values for audit
    current = await get_current_merchant(merchant_id)
    
    # Build update query dynamically
    update_fields = []
    params = []
    changed_values = {}
    
    if updates.merchant_name is not None:
        update_fields.append("merchant_name = %s")
        params.append(updates.merchant_name)
        changed_values['merchant_name'] = updates.merchant_name
    
    if updates.api_key is not None:
        encrypted = encrypt_value(updates.api_key)
        update_fields.append("api_key = %s")
        params.append(encrypted)
        changed_values['api_key'] = '***UPDATED***'
    
    if updates.api_secret is not None:
        encrypted = encrypt_value(updates.api_secret)
        update_fields.append("api_secret = %s")
        params.append(encrypted)
        changed_values['api_secret'] = '***UPDATED***'
    
    if updates.merchant_id_ref is not None:
        update_fields.append("merchant_id_ref = %s")
        params.append(updates.merchant_id_ref)
        changed_values['merchant_id_ref'] = updates.merchant_id_ref
    
    if updates.environment is not None:
        update_fields.append("environment = %s")
        params.append(updates.environment)
        changed_values['environment'] = updates.environment
    
    if updates.is_active is not None:
        update_fields.append("is_active = %s")
        params.append(updates.is_active)
        changed_values['is_active'] = updates.is_active
    
    if updates.is_default is not None:
        # If setting as default, unset other defaults for this department
        if updates.is_default:
            await unset_default_merchant(current['department'], merchant_id)
        update_fields.append("is_default = %s")
        params.append(updates.is_default)
        changed_values['is_default'] = updates.is_default
    
    if updates.gateway_config is not None:
        update_fields.append("gateway_config = %s")
        params.append(json.dumps(updates.gateway_config))
        changed_values['gateway_config'] = updates.gateway_config
    
    if update_fields:
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        update_fields.append("updated_by = %s")
        params.append(admin_id)
        
        query = f"""
            UPDATE payment_merchants 
            SET {', '.join(update_fields)}
            WHERE merchant_id = %s
            RETURNING merchant_id
        """
        params.append(merchant_id)
        
        await db.execute(query, params)
        
        # Log the update
        await log_merchant_action(
            merchant_id=merchant_id,
            action='UPDATE',
            changed_by=admin_id,
            old_values=current,
            new_values=changed_values
        )
    
    return {"success": True, "message": "Merchant updated successfully"}

@router.post("/{merchant_id}/payment-methods")
async def configure_payment_methods(
    merchant_id: str,
    methods: List[PaymentMethodConfig],
    admin_id: str = Depends(get_current_admin)
):
    """Configure payment methods for a merchant"""
    
    # Delete existing configurations
    await db.execute(
        "DELETE FROM payment_method_config WHERE merchant_id = %s",
        (merchant_id,)
    )
    
    # Insert new configurations
    for method in methods:
        await db.execute("""
            INSERT INTO payment_method_config 
            (merchant_id, payment_method, is_enabled, min_amount, max_amount, sort_order, additional_config)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            merchant_id,
            method.payment_method,
            method.is_enabled,
            method.min_amount,
            method.max_amount,
            method.sort_order,
            json.dumps(method.additional_config)
        ))
    
    return {"success": True, "message": "Payment methods configured successfully"}

@router.post("/{merchant_id}/test")
async def test_merchant_connection(
    merchant_id: str,
    admin_id: str = Depends(get_current_admin)
):
    """Test merchant connection by making a test API call"""
    
    merchant = await get_merchant_with_credentials(merchant_id)
    
    try:
        # Initialize gateway client based on type
        if merchant['gateway_type'] == 'razorpay':
            import razorpay
            client = razorpay.Client(
                auth=(decrypt_value(merchant['api_key']), 
                      decrypt_value(merchant['api_secret']))
            )
            # Test API call - get balance
            response = client.payment.all({'count': 1})
            
        elif merchant['gateway_type'] == 'payu':
            # PayU test logic
            pass
            
        # Log test attempt
        await db.execute("""
            INSERT INTO payment_gateway_logs 
            (merchant_id, request_type, success, created_at)
            VALUES (%s, 'TEST_CONNECTION', true, %s)
        """, (merchant_id, datetime.utcnow()))
        
        return {"success": True, "message": "Connection successful"}
        
    except Exception as e:
        logger.error(f"Merchant test failed: {str(e)}")
        
        # Log failure
        await db.execute("""
            INSERT INTO payment_gateway_logs 
            (merchant_id, request_type, success, error_message, created_at)
            VALUES (%s, 'TEST_CONNECTION', false, %s, %s)
        """, (merchant_id, str(e), datetime.utcnow()))
        
        return {
            "success": False, 
            "message": f"Connection failed: {str(e)}"
        }

# Helper functions
async def get_current_merchant(merchant_id: str) -> dict:
    query = "SELECT * FROM payment_merchants WHERE merchant_id = %s"
    result = await db.fetch_one(query, (merchant_id,))
    if not result:
        raise HTTPException(status_code=404, detail="Merchant not found")
    return result

async def unset_default_merchant(department: str, exclude_id: str):
    await db.execute("""
        UPDATE payment_merchants 
        SET is_default = false 
        WHERE department = %s AND merchant_id != %s
    """, (department, exclude_id))

async def log_merchant_action(merchant_id: str, action: str, changed_by: str, 
                              old_values: dict = None, new_values: dict = None):
    await db.execute("""
        INSERT INTO payment_merchant_audit 
        (merchant_id, action, changed_by, old_values, new_values)
        VALUES (%s, %s, %s, %s, %s)
    """, (merchant_id, action, changed_by, 
          json.dumps(old_values) if old_values else None,
          json.dumps(new_values) if new_values else None))
