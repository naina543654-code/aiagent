# Example Application Architecture

## Overview

This is a sample context file demonstrating the type of information AIPentester can analyze for business logic vulnerabilities.

## Application: E-Commerce Platform

### System Architecture

The platform consists of:
- **Web Frontend**: React SPA
- **API Gateway**: Node.js/Express
- **Auth Service**: OAuth 2.0 + JWT
- **Product Service**: Python/FastAPI
- **Order Service**: Python/FastAPI
- **Payment Service**: Java/Spring Boot
- **Notification Service**: Node.js

### User Roles

1. **Guest**: Can browse products
2. **Customer**: Can purchase, view orders
3. **Vendor**: Can manage their products
4. **Admin**: Full system access

### Key Workflows

#### Checkout Flow

1. Customer adds items to cart
2. Customer proceeds to checkout
3. System validates inventory availability
4. Customer enters shipping address
5. System calculates shipping cost
6. Customer selects payment method
7. System processes payment
8. System creates order
9. System sends confirmation email
10. System updates inventory

**Trust Boundaries Crossed**:
- Customer → Order Service (authz check)
- Order Service → Payment Service (internal API key)
- Payment Service → External Payment Gateway (TLS)

#### Vendor Product Management

1. Vendor logs in
2. Vendor navigates to product dashboard
3. Vendor creates new product
4. System validates vendor ownership
5. System publishes product (pending admin approval if value > $1000)

**Authorization Logic**:
```
if user.role == "vendor":
    if product.price > 1000:
        product.status = "pending_approval"
        notify_admins()
    else:
        product.status = "published"
```

### Data Model

**User**
- id (UUID)
- email (unique)
- role (enum)
- wallet_balance (decimal)

**Product**
- id (UUID)
- vendor_id (FK to User)
- name
- price
- inventory_count
- status (draft, published, pending_approval)

**Order**
- id (UUID)
- customer_id (FK to User)
- status (pending, paid, shipped, delivered, cancelled)
- total_amount
- created_at

**OrderItem**
- id (UUID)
- order_id (FK to Order)
- product_id (FK to Product)
- quantity
- price_at_purchase

### Permission Matrix

| Action | Guest | Customer | Vendor | Admin |
|--------|-------|----------|--------|-------|
| Browse products | ✓ | ✓ | ✓ | ✓ |
| Add to cart | ✓ | ✓ | ✓ | ✓ |
| Checkout | ✗ | ✓ | ✓ | ✓ |
| View own orders | ✗ | ✓ | ✗ | ✓ |
| Create product | ✗ | ✗ | ✓ | ✓ |
| Approve products | ✗ | ✗ | ✗ | ✓ |
| Manage users | ✗ | ✗ | ✗ | ✓ |

### Financial Flows

#### Purchase Flow
```
Customer Wallet (-$100)
  → Platform Escrow (+$100)
  → [Order Delivered]
  → Vendor Wallet (+$95)
  → Platform Fee (+$5)
```

#### Refund Flow
```
Vendor Wallet (-$95)
  → Platform Escrow (-$95)
  → Customer Wallet (+$95)
```

**Refund Rules**:
- Customers can request refund within 30 days
- Vendor must approve refund
- If vendor doesn't respond in 7 days, auto-approve
- Platform fee ($5) is non-refundable

### State Transitions

#### Order States
```
[Cart] → Add Item → [Cart]
[Cart] → Checkout → [Pending Payment]
[Pending Payment] → Payment Success → [Paid]
[Pending Payment] → Payment Failure → [Cancelled]
[Paid] → Ship → [Shipped]
[Shipped] → Deliver → [Delivered]
[Paid/Shipped] → Request Refund → [Refund Requested]
[Refund Requested] → Approve Refund → [Refunded]
```

### Known Trust Boundaries

1. **Anonymous → Authenticated**
   - Control: JWT token validation
   - Bypasses: Token expiry not checked in all endpoints

2. **Customer → Vendor Data**
   - Control: Ownership check via `vendor_id`
   - Bypasses: Numeric IDs susceptible to IDOR

3. **Vendor → Admin Functions**
   - Control: Role-based access control
   - Bypasses: Some admin endpoints check user.role client-side only

4. **Application → Payment Gateway**
   - Control: API key + TLS
   - Bypasses: API key rotated manually (could be stale)

### Potential Abuse Cases

1. **Price Manipulation**
   - Hypothesis: Can a customer modify price during checkout?
   - Vector: Tamper with cart item price before payment
   - Expected Control: Price fetched from database, not client

2. **IDOR on Orders**
   - Hypothesis: Can customer view other customers' orders?
   - Vector: Enumerate order IDs in GET /api/orders/:id
   - Expected Control: Authorization check `order.customer_id == current_user.id`

3. **Race Condition in Inventory**
   - Hypothesis: Can multiple customers purchase the last item?
   - Vector: Concurrent checkout requests
   - Expected Control: Database-level locking on inventory

4. **Vendor Privilege Escalation**
   - Hypothesis: Can vendor approve their own high-value products?
   - Vector: Call admin approval endpoint with vendor credentials
   - Expected Control: Role check should reject

5. **Refund Abuse**
   - Hypothesis: Can customer request multiple refunds for same order?
   - Vector: Replay refund request
   - Expected Control: Idempotency key or state check

6. **Wallet Manipulation**
   - Hypothesis: Can customer add funds without payment?
   - Vector: Direct API call to `/api/wallet/credit`
   - Expected Control: Endpoint should be internal-only or require payment proof

### API Endpoints

```
POST   /api/auth/login
POST   /api/auth/register
GET    /api/products
GET    /api/products/:id
POST   /api/products (vendor only)
PUT    /api/products/:id (vendor only, ownership check)
DELETE /api/products/:id (vendor only, ownership check)
POST   /api/cart/add
GET    /api/cart
POST   /api/checkout
GET    /api/orders (customer's own orders)
GET    /api/orders/:id (ownership check)
POST   /api/orders/:id/refund
POST   /api/admin/products/:id/approve (admin only)
GET    /api/admin/users (admin only)
```

### Security Headers

- CORS: Restricted to `app.example.com`
- CSP: `default-src 'self'`
- X-Frame-Options: DENY
- SameSite cookies: Lax

### Session Management

- JWT tokens (30 min expiry)
- Refresh tokens (7 days)
- No session invalidation on password change (vulnerability?)

## Test Priorities

1. **High**: IDOR on orders, price manipulation
2. **Medium**: Vendor privilege escalation, inventory race conditions
3. **Low**: Refund abuse, wallet manipulation
