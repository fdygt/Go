# Project Requirements & Specifications
Current Date: 2025-05-29 07:10:37
Author: fdygg

## 1. Multi-Platform Integration
### Bot Discord + Web API
- Bot Discord untuk game Growtopia
- API untuk berbagai layanan (PPOB, dll)
- Satu database untuk semua platform
- Konsistensi data antar platform

## 2. Sistem Balance Dual Currency
### Discord Users (Growtopia Players)
- Balance WL (World Lock)
- Balance DL (Diamond Lock)
- Balance BGL (Blue Gem Lock)
- Balance Rupiah
- **Fitur Khusus**: Bisa convert WL/DL/BGL ke Rupiah

### Web/App Users (Non-Discord)
- Balance Rupiah saja
- Tidak ada akses ke currency Growtopia
- Tidak ada fitur convert

## 3. Sistem Konversi (Discord Users Only)
### Rate Konversi (Configurable di Dashboard)
```sql
CREATE TABLE conversion_rates (
    id INTEGER PRIMARY KEY,
    currency TEXT,
    amount INTEGER,
    rate_rupiah INTEGER,
    updated_at TIMESTAMP,
    updated_by TEXT
)

# Models Documentation

## Core Features & Dependencies

1. **Multi-Platform Support**
   - Discord Integration
   - Web Platform
   - Platform-specific validations
   - Shared core functionality

2. **Currency System**
   - World Lock (WL)
   - Diamond Lock (DL)
   - Blue Gem Lock (BGL)
   - Indonesian Rupiah (IDR)
   - Conversion system (Discord-only)

3. **User Management**
   - Discord users (with Growtopia ID)
   - Web users
   - Role-based access
   - Admin hierarchy

4. **Security**
   - Blacklist system
   - Fraud detection
   - Platform-specific restrictions
   - Admin activity logging

## Key Models & Their Relationships

1. **User-Related**
   - `user.py`: Base user management
   - `auth.py`: Authentication & authorization
   - `admin.py`: Administrative controls
   - `blacklist.py`: User restrictions

2. **Transaction-Related**
   - `balance.py`: Currency balances
   - `transaction.py`: Transaction records
   - `conversion.py`: Currency conversion

3. **Product-Related**
   - `product.py`: Product definitions
   - `stock.py`: Inventory tracking
   
4. **System-Related**
   - `settings.py`: System configuration
   - `__init__.py`: Base models & exports

## Common Patterns

1. **Base Models**
   - `BaseTimestampModel`: Created/updated tracking
   - `BaseStatusModel`: Status management
   - `BaseResponse`: Standard response format
   - `BaseDateRangeFilter`: Date filtering
   - `BasePaginationParams`: List pagination

2. **Standard Fields**
   - `created_at`/`updated_at`: Timestamps
   - `created_by`/`updated_by`: User tracking
   - `metadata`: Flexible extra data
   - `is_active`: Status tracking

3. **Validation Rules**
   - Platform-specific restrictions
   - Currency access controls
   - Role-based permissions
   - Data integrity checks

## Best Practices

1. **Model Creation**
   - Always inherit from appropriate base models
   - Include Config class with examples
   - Add proper field validations
   - Document complex validations

2. **Platform Integration**
   - Check user_type for platform-specific logic
   - Validate Growtopia ID for Discord users
   - Restrict currency access appropriately
   - Use platform-specific metadata

3. **Currency Handling**
   - Always use CurrencyType enum
   - Implement proper conversion logic
   - Validate currency access rights
   - Track all currency changes

4. **Security Considerations**
   - Log all admin actions
   - Implement fraud detection
   - Maintain audit trails
   - Use proper permission checks

## Versioning & Updates

1. **Version Control**
   - Current Version: 1.0.0
   - API Version: v1
   - Last Updated: 2025-05-29 15:55:50
   - Updated By: fdygg

2. **Update Process**
   - Update timestamps
   - Increment version numbers
   - Update documentation
   - Test all integrations

## Notes for Future Development

1. **New Features**
   - Follow existing patterns
   - Update __init__.py exports
   - Add appropriate documentation
   - Include example configurations

2. **Modifications**
   - Maintain backward compatibility
   - Update all affected models
   - Follow naming conventions
   - Keep documentation current
## Folder Structure
models/
        ├── init.py # Model exports and base 
        ├── admin.py # Admin panel 
        ├── auth.py # Authentication 
        ├── balance.py # Balance & currency 
        ├── blacklist.py # Blacklist & fraud detection 
        ├── conversion.py # Currency conversion 
        ├── product.py # Product catalog 
        ├── settings.py # System settings 
        ├── stock.py # Inventory management 
        ├── transaction.py # Transaction handling 
        ├──  notifications.py 
        └── user.py # User management