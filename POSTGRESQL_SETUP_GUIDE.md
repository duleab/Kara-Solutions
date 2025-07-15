# PostgreSQL Migration Guide for Telegram Analytics

This guide will help you migrate your dbt project from SQLite to PostgreSQL for better performance and advanced analytics capabilities.

## Prerequisites

1. **Install PostgreSQL**
   - Download from: https://www.postgresql.org/download/
   - Install with default settings
   - Remember your postgres user password

2. **Install Python Dependencies**
   ```bash
   pip install psycopg2-binary
   ```

## Step 1: Database Setup

1. **Create Database**
   ```sql
   -- Connect to PostgreSQL as superuser
   CREATE DATABASE telegram_warehouse;
   ```

2. **Run Setup Script**
   ```bash
   psql -U postgres -d telegram_warehouse -f setup_postgresql.sql
   ```

## Step 2: Update Environment Variables

Update your `.env` file with PostgreSQL credentials:

```env
# Database Configuration (PostgreSQL)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=telegram_warehouse
DB_USER=postgres
DB_PASSWORD=your_actual_password_here
```

## Step 3: Data Migration

1. **Run Migration Script**
   ```bash
   python migrate_to_postgresql.py
   ```

2. **Verify Migration**
   ```sql
   -- Connect to PostgreSQL and check data
   SELECT COUNT(*) FROM telegram_messages;
   SELECT COUNT(*) FROM telegram_channels;
   ```

## Step 4: Test dbt Connection

1. **Test Connection**
   ```bash
   cd dbt_project
   dbt debug
   ```

2. **Run Models**
   ```bash
   dbt run
   ```

## Benefits of PostgreSQL Migration

### Performance Improvements
- **Faster Queries**: PostgreSQL's query optimizer is much more advanced
- **Parallel Processing**: Better handling of large datasets
- **Indexing**: Advanced indexing strategies for better performance
- **Memory Management**: Better memory utilization for analytics workloads

### Advanced Features
- **Window Functions**: Full support for advanced analytics functions
- **JSON/JSONB**: Native JSON support for raw_data fields
- **Date/Time Functions**: Rich set of temporal functions
- **Regular Expressions**: Advanced pattern matching capabilities
- **Full-Text Search**: Built-in search capabilities

### Scalability
- **Concurrent Users**: Better support for multiple users
- **Large Datasets**: Handles millions of rows efficiently
- **Partitioning**: Table partitioning for time-series data
- **Replication**: Built-in replication for high availability

### dbt Enhancements
- **Incremental Models**: Better support for incremental processing
- **Materializations**: More materialization options (views, tables, incremental)
- **Tests**: More comprehensive data quality testing
- **Macros**: Access to PostgreSQL-specific dbt macros

## Updated Model Features

### Enhanced Date/Time Processing
```sql
-- PostgreSQL native functions now available
extract(hour from message_date) as message_hour
date_trunc('week', message_date) as week_start
to_char(activity_date, 'Day') as day_name
```

### Better Type Casting
```sql
-- PostgreSQL casting syntax
messages_with_media::float / total_messages
message_date::date
```

### Advanced Analytics
```sql
-- Window functions with better performance
avg(daily_messages) over (
    partition by channel_id
    order by activity_date
    rows between 6 preceding and current row
) as messages_7day_avg
```

## Troubleshooting

### Connection Issues
1. Verify PostgreSQL is running: `pg_ctl status`
2. Check firewall settings
3. Verify credentials in `.env` file

### Migration Issues
1. Check SQLite database exists
2. Verify PostgreSQL tables are created
3. Check data types compatibility

### dbt Issues
1. Run `dbt clean` and `dbt deps`
2. Check profiles.yml configuration
3. Verify source table references

## Next Steps

1. **Optimize Performance**
   - Add appropriate indexes
   - Consider table partitioning for large datasets
   - Implement incremental models

2. **Enhance Analytics**
   - Add more sophisticated business metrics
   - Implement real-time dashboards
   - Create data quality monitoring

3. **Scale Infrastructure**
   - Set up automated backups
   - Configure monitoring and alerting
   - Implement CI/CD for dbt models

## Support

If you encounter issues:
1. Check PostgreSQL logs: `tail -f /var/log/postgresql/postgresql-*.log`
2. Review dbt logs: `dbt --log-level debug run`
3. Verify environment variables are loaded correctly

Your dbt project is now ready for production-scale analytics with PostgreSQL!