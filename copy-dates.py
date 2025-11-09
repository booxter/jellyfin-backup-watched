# Copy DateCreated / DateModified / DateLastMediaAdded values from the BaseItems tables from
# one Jellyfin Database to another, matching the ItemIDs based on the Name/Type/Media Path of
# each media item.
# 
# This is for when you're standing up a new Jellyfin instance with a new jellyfin.db, but the
# libraries are the same as before and you want # that is using the same libraries as before
# and want to preserve the 'Date Added' order of shows
#
# Tested only on Jellyfin 10.11.1 (after the major database overhaul to EF Core)
#

import sqlite3

def update_date_created(source_db_path, target_db_path):
    # Connect to the source SQLite database (BaseItems - database for matching records)
    source_conn = sqlite3.connect(source_db_path)
    source_cursor = source_conn.cursor()

    # Connect to the target SQLite database (BaseItems - database to be updated)
    target_conn = sqlite3.connect(target_db_path)
    target_cursor = target_conn.cursor()

    target_update_cursor = target_conn.cursor()

    try:
        # Query to get the relevant columns from the BaseItems table in the target database
        target_cursor.execute("SELECT id, Name, Type, Path, DateCreated, DateModified, DateLastMediaAdded FROM BaseItems")
        
        # Iterate through each record in the target (database to be updated)
        for row in target_cursor:
            target_db_id, target_db_name, target_db_type, target_db_path, target_db_datecreated, target_db_datemodified, target_db_datelastmediaadded = row

            # Query the source database to find a matching record based on Name, Type, and Path
            source_cursor.execute("""
                SELECT DateCreated, DateModified, DateLastMediaAdded
                FROM BaseItems
                WHERE Name = ? AND Type = ? AND Path = ?
            """, (target_db_name, target_db_type, target_db_path))

            # Check if a matching record exists in the source database
            match = source_cursor.fetchall()

            if len(match) == 0:
                print(f"No matches for {target_db_id}")

            if len(match) > 1:
                print(f"Duplicate for {target_db_id}")

            if len(match) == 1:
                source_db_datecreated, source_db_datemodified, source_db_datelastmediaadded  = match[0]
                # Update the DateCreated field in the target database using the target_db_id
                target_update_cursor.execute("""
                    UPDATE BaseItems
                    SET DateCreated = ?,
                        DateModified = ?,
                        DateLastMediaAdded = ?
                    WHERE id = ?
                    
                """, (source_db_datecreated, source_db_datemodified, source_db_datelastmediaadded, target_db_id))

                print(f"Updated {target_db_id} {target_db_type} {target_db_name}: {source_db_datecreated} {source_db_datemodified} {source_db_datelastmediaadded}")

        # Commit the changes to the target (database to be updated)
        target_conn.commit()
        print("Database update completed successfully.")

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")

    finally:
        # Close database connections
        target_cursor.close()
        target_conn.close()
        source_cursor.close()
        source_conn.close()

# Specify the paths to the SQLite databases
source_db_path = '/config/jellyfin/data/data/jellyfin.db'  # Source database (where the matching records come from)
target_db_path = '/config/jellyfin2/data/data/jellyfin.db'  # Target database (where the DateCreated field is updated)

# Call the function to update the records
update_date_created(source_db_path, target_db_path)
