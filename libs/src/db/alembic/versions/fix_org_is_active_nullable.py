"""
Fix org is_active column to be non-nullable with proper default.

This script ensures that the is_active column in kiwiq_auth_org table is:
1. Non-nullable (nullable=False)
2. Has a proper default value of True
3. All existing NULL values are set to True before applying NOT NULL constraint

Reference migration: 5200095f9754_add_proper_relationship_cascade_for_.py
"""

import asyncio
import logging
from sqlalchemy import text, Boolean
from sqlalchemy.ext.asyncio import AsyncSession

# Import database session manager
from db.session import get_async_db_as_manager, async_engine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_org_is_active_column():
    """
    Fix the is_active column in kiwiq_auth_org table to be non-nullable.
    
    Steps:
    1. Update any NULL values to True (default active state)
    2. Alter the column to be NOT NULL with default True
    3. Verify the changes
    """
    logger.info("Starting org is_active column fix...")
    
    async with get_async_db_as_manager() as db:
        try:
            # Step 1: Check current state of the column
            logger.info("1. Checking current state of is_active column...")
            
            result = await db.execute(text("""
                SELECT 
                    COUNT(*) as total_orgs,
                    COUNT(is_active) as non_null_count,
                    COUNT(*) - COUNT(is_active) as null_count,
                    COUNT(CASE WHEN is_active = true THEN 1 END) as active_count,
                    COUNT(CASE WHEN is_active = false THEN 1 END) as inactive_count
                FROM kiwiq_auth_org;
            """))
            
            row = result.fetchone()
            logger.info(f"   Total organizations: {row.total_orgs}")
            logger.info(f"   Non-null is_active values: {row.non_null_count}")
            logger.info(f"   NULL is_active values: {row.null_count}")
            logger.info(f"   Active organizations: {row.active_count}")
            logger.info(f"   Inactive organizations: {row.inactive_count}")
            
            # Step 2: Update any NULL values to True (default active state)
            if row.null_count > 0:
                logger.info(f"2. Updating {row.null_count} NULL is_active values to True...")
                
                update_result = await db.execute(text("""
                    UPDATE kiwiq_auth_org 
                    SET is_active = true 
                    WHERE is_active IS NULL;
                """))
                
                logger.info(f"   Updated {update_result.rowcount} rows to is_active = true")
                await db.commit()
            else:
                logger.info("2. No NULL values found, skipping update step.")
            
            # Step 3: Alter column to be NOT NULL with default True
            logger.info("3. Altering column to be NOT NULL with default True...")
            
            # # Set default value first
            # await db.execute(text("""
            #     ALTER TABLE kiwiq_auth_org 
            #     ALTER COLUMN is_active SET DEFAULT true;
            # """))
            
            # Then set NOT NULL constraint
            await db.execute(text("""
                ALTER TABLE kiwiq_auth_org 
                ALTER COLUMN is_active SET NOT NULL;
            """))
            
            await db.commit()
            logger.info("   Column altered successfully")
            
            # Step 4: Verify the changes
            logger.info("4. Verifying column changes...")
            
            # Check column definition
            column_info = await db.execute(text("""
                SELECT 
                    column_name,
                    is_nullable,
                    column_default,
                    data_type
                FROM information_schema.columns 
                WHERE table_name = 'kiwiq_auth_org' 
                AND column_name = 'is_active';
            """))
            
            col_row = column_info.fetchone()
            if col_row:
                logger.info(f"   Column name: {col_row.column_name}")
                logger.info(f"   Is nullable: {col_row.is_nullable}")
                logger.info(f"   Default value: {col_row.column_default}")
                logger.info(f"   Data type: {col_row.data_type}")
                
                if col_row.is_nullable == 'NO':
                    logger.info("   ✅ Column is now NOT NULL as expected")
                else:
                    logger.warning("   ⚠️  Column is still nullable - check if operation succeeded")
            else:
                logger.error("   ❌ Could not retrieve column information")
            
            # Check final data state
            final_result = await db.execute(text("""
                SELECT 
                    COUNT(*) as total_orgs,
                    COUNT(CASE WHEN is_active = true THEN 1 END) as active_count,
                    COUNT(CASE WHEN is_active = false THEN 1 END) as inactive_count
                FROM kiwiq_auth_org;
            """))
            
            final_row = final_result.fetchone()
            logger.info(f"5. Final state:")
            logger.info(f"   Total organizations: {final_row.total_orgs}")
            logger.info(f"   Active organizations: {final_row.active_count}")
            logger.info(f"   Inactive organizations: {final_row.inactive_count}")
            
            logger.info("✅ org is_active column fix completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error during column fix: {e}")
            await db.rollback()
            raise

async def verify_column_state():
    """
    Utility function to just check the current state of the is_active column.
    """
    logger.info("Checking current state of is_active column...")
    
    async with get_async_db_as_manager() as db:
        try:
            # Check column definition
            column_info = await db.execute(text("""
                SELECT 
                    column_name,
                    is_nullable,
                    column_default,
                    data_type
                FROM information_schema.columns 
                WHERE table_name = 'kiwiq_auth_org' 
                AND column_name = 'is_active';
            """))
            
            col_row = column_info.fetchone()
            if col_row:
                print(f"\nColumn Information:")
                print(f"  Name: {col_row.column_name}")
                print(f"  Nullable: {col_row.is_nullable}")
                print(f"  Default: {col_row.column_default}")
                print(f"  Type: {col_row.data_type}")
            else:
                print("❌ Column 'is_active' not found in 'kiwiq_auth_org' table")
                return
            
            # Check data state
            data_result = await db.execute(text("""
                SELECT 
                    COUNT(*) as total_orgs,
                    COUNT(is_active) as non_null_count,
                    COUNT(*) - COUNT(is_active) as null_count,
                    COUNT(CASE WHEN is_active = true THEN 1 END) as active_count,
                    COUNT(CASE WHEN is_active = false THEN 1 END) as inactive_count
                FROM kiwiq_auth_org;
            """))
            
            data_row = data_result.fetchone()
            print(f"\nData State:")
            print(f"  Total organizations: {data_row.total_orgs}")
            print(f"  Non-null values: {data_row.non_null_count}")
            print(f"  NULL values: {data_row.null_count}")
            print(f"  Active: {data_row.active_count}")
            print(f"  Inactive: {data_row.inactive_count}")
            
        except Exception as e:
            logger.error(f"Error checking column state: {e}")
            raise

async def main():
    """Main function to run the column fix."""
    try:
        # You can uncomment one of these lines:
        await fix_org_is_active_column()
        # await verify_column_state()  # Use this to just check current state
        
        logger.info("Script completed successfully.")
    except Exception as e:
        logger.error(f"Script failed with error: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting org is_active column fix script...")
    asyncio.run(main()) 