# TSIS 1 - PhoneBook

## Files
- `phonebook.py` - console application
- `config.py` - PostgreSQL settings
- `connect.py` - database connection
- `schema.sql` - new tables and migration from the old phonebook table
- `functions.sql` - search and pagination functions
- `procedures.sql` - Practice 8 procedures adapted to the new schema and new TSIS 1 procedures
- `contacts.csv` - example CSV file

## 1. Install dependency

```bash
python3 -m pip install psycopg2-binary
```

## 2. Configure PostgreSQL

The default database name is `phonebook_db`, and the default user is `zhumabaymagzhan`.
If your PostgreSQL password is not empty, set it in Terminal:

```bash
export PGPASSWORD='your_postgresql_password'
```

You can change the settings in `config.py` or use environment variables:
`PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`.

Make sure the database already exists. If needed, create it in PostgreSQL:

```sql
CREATE DATABASE phonebook_db;
```

## 3. Run

```bash
python3 phonebook.py
```

The program creates the new tables and installs the SQL functions and procedures.

## 4. Features

- Multiple phone numbers per contact (`phones`)
- Email and birthday
- Groups (`groups`)
- Filter by group and partial email search
- Sort by name, birthday, and date added
- Page navigation: `next`, `prev`, `quit`
- JSON export and import with skip/overwrite for duplicate names
- Extended CSV import, supporting both `name` and old `first_name` headers
- Practice 8 upsert, bulk-insert validation, delete, and pagination workflows retained
- `add_phone`, `move_to_group`, and `search_contacts`

## Old Practice 7/8 data

The schema script checks for an old `phonebook` table and copies contacts and phone numbers into the new tables. Practice 7 used `name`; Practice 8 used `first_name`.

The old pagination function name `get_contacts_page` is retained, but adapted to the new tables.
