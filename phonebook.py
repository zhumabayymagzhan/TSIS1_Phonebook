import csv
import json
import re
from pathlib import Path

from connect import get_connection, run_sql_file

BASE_DIR = Path(__file__).resolve().parent
PHONE_TYPES = ("home", "work", "mobile")
SORT_OPTIONS = {
    "1": ("c.name ASC", "name"),
    "2": ("c.birthday ASC NULLS LAST", "birthday"),
    "3": ("c.created_at ASC", "date added"),
}


def setup():
    run_sql_file(BASE_DIR / "schema.sql")
    run_sql_file(BASE_DIR / "functions.sql")
    run_sql_file(BASE_DIR / "procedures.sql")
    print("Database is ready.")


def get_group_id(cur, group_name="Other"):
    group_name = (group_name or "Other").strip() or "Other"
    cur.execute(
        "INSERT INTO groups (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
        (group_name,),
    )
    cur.execute("SELECT id FROM groups WHERE name = %s", (group_name,))
    return cur.fetchone()[0]


def print_contact_rows(rows):
    if not rows:
        print("No contacts found.")
        return
    for row in rows:
        print(
            f"ID: {row[0]} | Name: {row[1]} | Email: {row[2] or '-'} | "
            f"Birthday: {row[3] or '-'} | Group: {row[4] or '-'} | "
            f"Phones: {row[5] or '-'}"
        )



def upsert_contact():
    """Practice 8 feature: add a contact or update its first phone number."""
    name = input("Name: ").strip()
    phone = input("Phone: ").strip()
    if not name or not re.fullmatch(r"\\+?[0-9]{10,15}", phone):
        print("Enter a name and a valid phone number (10-15 digits).")
        return
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("CALL upsert_contact(%s, %s)", (name, phone))
    print("Contact saved (inserted or updated).")


def add_contact():
    name = input("Name: ").strip()
    if not name:
        print("Name cannot be empty.")
        return
    phone = input("Phone (optional): ").strip()
    phone_type = input("Phone type (home/work/mobile) [mobile]: ").strip().lower() or "mobile"
    if phone_type not in PHONE_TYPES:
        print("Invalid phone type.")
        return
    email = input("Email (optional): ").strip() or None
    birthday = input("Birthday (YYYY-MM-DD, optional): ").strip() or None
    group_name = input("Group [Other]: ").strip() or "Other"

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                group_id = get_group_id(cur, group_name)
                cur.execute(
                    """INSERT INTO contacts (name, email, birthday, group_id)
                       VALUES (%s, %s, %s, %s) RETURNING id""",
                    (name, email, birthday, group_id),
                )
                contact_id = cur.fetchone()[0]
                if phone:
                    cur.execute(
                        "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s)",
                        (contact_id, phone, phone_type),
                    )
        print("Contact added.")
    except Exception as error:
        print("Could not add contact:", error)


def update_contact():
    name = input("Contact name: ").strip()
    print("1 - Change name")
    print("2 - Change email")
    print("3 - Change birthday")
    print("4 - Change first phone number")
    choice = input("Choose: ").strip()
    value = input("New value: ").strip()
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                if choice == "1":
                    cur.execute("UPDATE contacts SET name = %s WHERE name = %s", (value, name))
                elif choice == "2":
                    cur.execute("UPDATE contacts SET email = %s WHERE name = %s", (value or None, name))
                elif choice == "3":
                    cur.execute("UPDATE contacts SET birthday = %s WHERE name = %s", (value or None, name))
                elif choice == "4":
                    cur.execute(
                        """UPDATE phones SET phone = %s
                           WHERE id = (
                               SELECT ph.id FROM phones ph
                               JOIN contacts c ON c.id = ph.contact_id
                               WHERE c.name = %s ORDER BY ph.id LIMIT 1
                           )""",
                        (value, name),
                    )
                else:
                    print("Invalid choice.")
                    return
                print("Updated." if cur.rowcount else "Contact or phone not found.")
    except Exception as error:
        print("Could not update contact:", error)


def search_contacts():
    pattern = input("Search by name, email, or phone: ").strip()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM search_contacts(%s)", (pattern,))
            rows = cur.fetchall()
    print_contact_rows(rows)


def filter_by_group():
    group_name = input("Group name: ").strip()
    query = """
        SELECT c.id, c.name, c.email, c.birthday, g.name,
               COALESCE(STRING_AGG(ph.phone || ' (' || ph.type || ')', ', ' ORDER BY ph.id), '')
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        LEFT JOIN phones ph ON ph.contact_id = c.id
        WHERE g.name ILIKE %s
        GROUP BY c.id, c.name, c.email, c.birthday, g.name
        ORDER BY c.name
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (group_name,))
            rows = cur.fetchall()
    print_contact_rows(rows)


def search_by_email():
    part = input("Part of email (example: gmail): ").strip()
    query = """
        SELECT c.id, c.name, c.email, c.birthday, g.name,
               COALESCE(STRING_AGG(ph.phone || ' (' || ph.type || ')', ', ' ORDER BY ph.id), '')
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        LEFT JOIN phones ph ON ph.contact_id = c.id
        WHERE c.email ILIKE %s
        GROUP BY c.id, c.name, c.email, c.birthday, g.name
        ORDER BY c.name
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, ("%" + part + "%",))
            rows = cur.fetchall()
    print_contact_rows(rows)


def sort_contacts():
    print("1 - By name")
    print("2 - By birthday")
    print("3 - By date added")
    selected = SORT_OPTIONS.get(input("Sort by: ").strip())
    if not selected:
        print("Invalid choice.")
        return
    order_by, label = selected
    # order_by comes only from the fixed whitelist above.
    query = f"""
        SELECT c.id, c.name, c.email, c.birthday, g.name,
               COALESCE(STRING_AGG(ph.phone || ' (' || ph.type || ')', ', ' ORDER BY ph.id), '')
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        LEFT JOIN phones ph ON ph.contact_id = c.id
        GROUP BY c.id, c.name, c.email, c.birthday, g.name, c.created_at
        ORDER BY {order_by}
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
    print("Sorted by", label)
    print_contact_rows(rows)


def show_pages():
    try:
        page_size = int(input("Contacts per page [5]: ").strip() or "5")
        if page_size < 1:
            raise ValueError
    except ValueError:
        print("Enter a positive number.")
        return

    page = 1
    while True:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM get_contacts_page(%s, %s)",
                    (page_size, (page - 1) * page_size),
                )
                rows = cur.fetchall()
        print(f"\\n--- Page {page} ---")
        if rows:
            for row in rows:
                print(f"ID: {row[0]} | Name: {row[1]} | First phone: {row[2]}")
        else:
            print("No contacts on this page.")
        command = input("next / prev / quit: ").strip().lower()
        if command == "next":
            if rows:
                page += 1
            else:
                print("There are no more pages.")
        elif command == "prev":
            if page > 1:
                page -= 1
            else:
                print("This is the first page.")
        elif command == "quit":
            break
        else:
            print("Use next, prev, or quit.")


def delete_contact():
    value = input("Contact name or phone number to delete: ").strip()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("CALL delete_contact(%s)", (value,))
    print("Delete command completed.")


def add_extra_phone():
    name = input("Contact name: ").strip()
    phone = input("New phone number: ").strip()
    phone_type = input("Type (home/work/mobile): ").strip().lower()
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("CALL add_phone(%s, %s, %s)", (name, phone, phone_type))
        print("Phone number added.")
    except Exception as error:
        print("Could not add phone:", error)


def move_contact_to_group():
    name = input("Contact name: ").strip()
    group_name = input("New group name: ").strip()
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("CALL move_to_group(%s, %s)", (name, group_name))
        print("Contact moved to group.")
    except Exception as error:
        print("Could not move contact:", error)


def export_json():
    path = input("JSON file name [contacts.json]: ").strip() or "contacts.json"
    result = []
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT c.id, c.name, c.email, c.birthday, g.name, c.created_at
                   FROM contacts c LEFT JOIN groups g ON g.id = c.group_id
                   ORDER BY c.name"""
            )
            contacts = cur.fetchall()
            for contact in contacts:
                cur.execute(
                    "SELECT phone, type FROM phones WHERE contact_id = %s ORDER BY id",
                    (contact[0],),
                )
                phones = [{"phone": p[0], "type": p[1]} for p in cur.fetchall()]
                result.append({
                    "name": contact[1],
                    "email": contact[2],
                    "birthday": contact[3].isoformat() if contact[3] else None,
                    "group": contact[4] or "Other",
                    "phones": phones,
                    "date_added": contact[5].isoformat() if contact[5] else None,
                })
    with open(path, "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=4, default=str)
    print(f"Exported {len(result)} contacts to {path}.")


def import_json():
    path = input("JSON file path: ").strip()
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, list):
            raise ValueError("JSON root must be a list of contacts.")

        with get_connection() as conn:
            with conn.cursor() as cur:
                for item in data:
                    name = (item.get("name") or "").strip()
                    if not name:
                        print("Skipped a record without a name.")
                        continue
                    cur.execute("SELECT id FROM contacts WHERE name = %s", (name,))
                    existing = cur.fetchone()
                    group_id = get_group_id(cur, item.get("group", "Other"))

                    if existing:
                        decision = input(f"{name} already exists. skip / overwrite? ").strip().lower()
                        if decision != "overwrite":
                            continue
                        contact_id = existing[0]
                        cur.execute(
                            """UPDATE contacts SET email = %s, birthday = %s, group_id = %s
                               WHERE id = %s""",
                            (item.get("email"), item.get("birthday"), group_id, contact_id),
                        )
                        cur.execute("DELETE FROM phones WHERE contact_id = %s", (contact_id,))
                    else:
                        cur.execute(
                            """INSERT INTO contacts (name, email, birthday, group_id)
                               VALUES (%s, %s, %s, %s) RETURNING id""",
                            (name, item.get("email"), item.get("birthday"), group_id),
                        )
                        contact_id = cur.fetchone()[0]

                    for phone_item in item.get("phones", []):
                        phone = (phone_item.get("phone") or "").strip()
                        phone_type = (phone_item.get("type") or "mobile").lower()
                        if phone and phone_type in PHONE_TYPES:
                            cur.execute(
                                "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s)",
                                (contact_id, phone, phone_type),
                            )
        print("JSON import completed.")
    except Exception as error:
        print("Could not import JSON:", error)


def import_csv():
    path = input("CSV file path [contacts.csv]: ").strip() or "contacts.csv"
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))
        imported = skipped = 0
        with get_connection() as conn:
            with conn.cursor() as cur:
                for row in rows:
                    name = (row.get("name") or row.get("first_name") or "").strip()
                    phone = (row.get("phone") or "").strip()
                    if not name:
                        skipped += 1
                        continue
                    if phone and not re.fullmatch(r"\\+?[0-9]{10,15}", phone):
                        print(f"Skipped invalid phone number for {name}: {phone}")
                        skipped += 1
                        continue
                    group_id = get_group_id(cur, row.get("group") or "Other")
                    birthday = (row.get("birthday") or "").strip() or None
                    email = (row.get("email") or "").strip() or None
                    phone_type = (row.get("phone_type") or "mobile").strip().lower()
                    if phone_type not in PHONE_TYPES:
                        phone_type = "mobile"

                    cur.execute("SELECT id FROM contacts WHERE name = %s", (name,))
                    found = cur.fetchone()
                    if found:
                        contact_id = found[0]
                        cur.execute(
                            """UPDATE contacts
                               SET email = COALESCE(%s, email),
                                   birthday = COALESCE(%s, birthday), group_id = %s
                               WHERE id = %s""",
                            (email, birthday, group_id, contact_id),
                        )
                    else:
                        cur.execute(
                            """INSERT INTO contacts (name, email, birthday, group_id)
                               VALUES (%s, %s, %s, %s) RETURNING id""",
                            (name, email, birthday, group_id),
                        )
                        contact_id = cur.fetchone()[0]
                    if phone:
                        cur.execute(
                            "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s)",
                            (contact_id, phone, phone_type),
                        )
                    imported += 1
        print(f"CSV import finished. Processed: {imported}; skipped: {skipped}.")
    except Exception as error:
        print("Could not import CSV:", error)


def main():
    try:
        setup()
    except Exception as error:
        print("Database setup failed:", error)
        print("Check PostgreSQL, database existence, and config.py.")
        return

    actions = {
        "1": add_contact,
        "2": update_contact,
        "3": search_contacts,
        "4": filter_by_group,
        "5": search_by_email,
        "6": sort_contacts,
        "7": show_pages,
        "8": import_csv,
        "9": export_json,
        "10": import_json,
        "11": add_extra_phone,
        "12": move_contact_to_group,
        "13": delete_contact,
        "14": upsert_contact,
    }

    while True:
        print("""
========== PHONEBOOK ==========
1. Add contact
2. Update contact
3. Search by name / email / phone
4. Filter by group
5. Search by email
6. Sort contacts
7. Show pages (next / prev / quit)
8. Import CSV
9. Export JSON
10. Import JSON
11. Add another phone
12. Move contact to group
13. Delete contact
14. Add/update contact (Practice 8 upsert)
0. Exit
""")
        choice = input("Choose: ").strip()
        if choice == "0":
            print("Goodbye!")
            break
        action = actions.get(choice)
        if action:
            action()
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
