# Copy the Watch History / Favourites from the UserData table from one Jellyfin
# Database to another, matching the ItemIDs based on the Name/Type/Path
# each media item, and matching the UserID based on the UserName.
# 
# This is for when you're standing up a new Jellyfin instance with a new jellyfin.db, but with
# the same users, and want the users to retain their watch history, played shows, favourited shows etc.
#
# Tested only on Jellyfin 10.11.1 (after the major database overhaul to EF Core)
#

import sqlite3
import sys

# --- CONFIGURATION ---
SOURCE_DB_PATH = '/config/jellyfin/data/data/jellyfin.db'  # Source database (where the matching records come from)
TARGET_DB_PATH = '/config/jellyfin2/data/data/jellyfin.db'  # Target database (where the DateCreated field is updated)

def main():
    try:
        # Connect to both databases
        source_conn = sqlite3.connect(SOURCE_DB_PATH)
        target_conn = sqlite3.connect(TARGET_DB_PATH)

        # Create separate cursors
        source_cur = source_conn.cursor()
        target_search_cur = target_conn.cursor()  # For lookup queries
        target_insert_cur = target_conn.cursor()  # For inserts

        # Fetch all records from source UserData
        source_cur.execute("SELECT * FROM UserData")
        columns = [desc[0] for desc in source_cur.description]

        for row in source_cur.fetchall():
            record = dict(zip(columns, row))

            # --- Step 1: Find matching UserID in target ---
            src_user_id = record["UserId"]
            try:
                source_cur.execute("SELECT Username FROM Users WHERE Id = ?", (src_user_id,))
                src_user = source_cur.fetchone()
                if not src_user:
                    print(f"[WARN] Source UserId {src_user_id} not found in source Users table.")
                    continue
                username = src_user[0]

                target_search_cur.execute("SELECT Id FROM Users WHERE Username = ?", (username,))
                target_users = target_search_cur.fetchall()

                if len(target_users) != 1:
                    print(f"[WARN] Found {len(target_users)} target users matching username '{username}'")
                    continue

                target_user_id = target_users[0][0]
            except Exception as e:
                print(f"[ERROR] Looking up user for {src_user_id}: {e}")
                continue

            # --- Step 2: Find matching ItemId in target ---
            src_item_id = record["ItemId"]
            try:
                # Get identifying fields from the source BaseItems table
                source_cur.execute("SELECT Name, Path, Type FROM BaseItems WHERE Id = ?", (src_item_id,))
                src_item = source_cur.fetchone()
                if not src_item:
                    print(f"[WARN] Source ItemId {src_item_id} not found in BaseItems.")
                    continue
                name, path, type_ = src_item

                target_search_cur.execute(
                    "SELECT Id FROM BaseItems WHERE Name = ? AND Path = ? AND Type = ?",
                    (name, path, type_)
                )
                target_items = target_search_cur.fetchall()

                if len(target_items) != 1:
                    print(f"[WARN] Found {len(target_items)} target items matching {name}/{path}/{type_}")
                    continue

                target_item_id = target_items[0][0]
            except Exception as e:
                print(f"[ERROR] Looking up item for {src_item_id}: {e}")
                continue

            # --- Step 3: Insert into target UserData ---
            try:
                insert_data = (
                    target_item_id,
                    target_user_id,
                    record["CustomDataKey"],
                    record["AudioStreamIndex"],
                    record["IsFavorite"],
                    record["LastPlayedDate"],
                    record["Likes"],
                    record["PlayCount"],
                    record["PlaybackPositionTicks"],
                    record["Played"],
                    record["Rating"],
                    record["SubtitleStreamIndex"],
                    record["RetentionDate"]
                )

                target_insert_cur.execute("""
                    INSERT INTO UserData (
                        ItemId, UserId, CustomDataKey, AudioStreamIndex, IsFavorite,
                        LastPlayedDate, Likes, PlayCount, PlaybackPositionTicks,
                        Played, Rating, SubtitleStreamIndex, RetentionDate
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, insert_data)

                print(f"Inserted: UserID={target_user_id}, ItemID={target_item_id}")

            except sqlite3.IntegrityError as e:
                print(f"[WARN] Duplicate or invalid insert for UserID={target_user_id}, ItemID={target_item_id}: {e}")
            except Exception as e:
                print(f"[ERROR] Insert failed for UserID={target_user_id}, ItemID={target_item_id}: {e}")

        # Commit and close
        target_conn.commit()
        print("✅ Data transfer complete.")

    except sqlite3.Error as e:
        print(f"[DB ERROR] {e}")
        sys.exit(1)

    finally:
        source_conn.close()
        target_conn.close()


if __name__ == "__main__":
    main()
