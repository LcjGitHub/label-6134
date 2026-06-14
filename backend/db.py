import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = Path(os.environ.get("GIFT_DB_PATH", str(DATA_DIR / "gift.db")))

RESERVATION_STATUS_PENDING = "pending"
RESERVATION_STATUS_CONFIRMED = "confirmed"
RESERVATION_STATUS_CANCELLED = "cancelled"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_category(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "sort_order": row["sort_order"],
    }


def row_to_gift(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "item_name": row["item_name"],
        "description": row["description"],
        "gift_date": row["gift_date"],
        "recipient_nickname": row["recipient_nickname"],
        "is_taken": bool(row["is_taken"]),
        "category_id": row["category_id"],
        "category_name": row["category_name"],
        "donor_nickname": row["donor_nickname"],
        "donor_phone": row["donor_phone"],
        "location": row["location"],
    }


def row_to_reservation(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "gift_id": row["gift_id"],
        "gift_item_name": row["gift_item_name"],
        "reserver_nickname": row["reserver_nickname"],
        "reserve_time": row["reserve_time"],
        "status": row["status"],
    }


def row_to_note(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "gift_id": row["gift_id"],
        "content": row["content"],
        "created_at": row["created_at"],
    }


def row_to_volunteer(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "phone": row["phone"],
        "service_time": row["service_time"],
        "skill_category": row["skill_category"],
        "register_date": row["register_date"],
        "is_active": bool(row["is_active"]),
    }


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_db()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS gifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                gift_date TEXT NOT NULL,
                recipient_nickname TEXT NOT NULL DEFAULT '',
                is_taken INTEGER NOT NULL DEFAULT 0,
                category_id INTEGER DEFAULT NULL,
                donor_nickname TEXT NOT NULL DEFAULT '',
                donor_phone TEXT NOT NULL DEFAULT '',
                location TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gift_id INTEGER NOT NULL,
                reserver_nickname TEXT NOT NULL,
                reserve_time TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                FOREIGN KEY (gift_id) REFERENCES gifts(id) ON DELETE CASCADE
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS gift_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gift_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (gift_id) REFERENCES gifts(id) ON DELETE CASCADE
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS volunteers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                service_time TEXT NOT NULL DEFAULT '',
                skill_category TEXT NOT NULL DEFAULT '',
                register_date TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        cur = conn.execute("PRAGMA table_info(gifts)")
        existing_cols = {row["name"] for row in cur.fetchall()}
        if "donor_nickname" not in existing_cols:
            conn.execute("ALTER TABLE gifts ADD COLUMN donor_nickname TEXT NOT NULL DEFAULT ''")
        if "donor_phone" not in existing_cols:
            conn.execute("ALTER TABLE gifts ADD COLUMN donor_phone TEXT NOT NULL DEFAULT ''")
            donor_infos = [
                ("儿童绘本一套", "爱心妈妈李女士", "13800138001"),
                ("电热水壶", "201室张先生", "13800138002"),
                ("折叠晾衣架", "阳光大姐王阿姨", "13800138003"),
                ("冬季厚棉被", "退休教师陈奶奶", "13800138004"),
                ("闲置键盘", "IT工程师老刘", "13800138005"),
            ]
            for item_name, nickname, phone in donor_infos:
                conn.execute(
                    "UPDATE gifts SET donor_nickname = ?, donor_phone = ? WHERE item_name = ? AND (donor_nickname = '' OR donor_phone = '')",
                    (nickname, phone, item_name),
                )
            conn.commit()

        if "location" not in existing_cols:
            conn.execute("ALTER TABLE gifts ADD COLUMN location TEXT NOT NULL DEFAULT ''")
            location_infos = [
                ("儿童绘本一套", "物业前台"),
                ("电热水壶", "菜鸟驿站"),
                ("折叠晾衣架", "楼道口"),
                ("冬季厚棉被", "物业前台"),
                ("闲置键盘", "菜鸟驿站"),
            ]
            for item_name, loc in location_infos:
                conn.execute(
                    "UPDATE gifts SET location = ? WHERE item_name = ? AND location = ''",
                    (loc, item_name),
                )
            conn.commit()

        cat_count = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        if cat_count == 0:
            seed_categories = [
                ("图书文具", 1),
                ("家居用品", 2),
                ("服饰衣物", 3),
                ("数码电子", 4),
                ("母婴玩具", 5),
            ]
            conn.executemany(
                "INSERT INTO categories (name, sort_order) VALUES (?, ?)",
                seed_categories,
            )
            conn.commit()

        cat_rows = conn.execute(
            "SELECT id, name FROM categories ORDER BY sort_order, id"
        ).fetchall()
        cat_map = {r["name"]: r["id"] for r in cat_rows}

        gift_count = conn.execute("SELECT COUNT(*) FROM gifts").fetchone()[0]
        if gift_count == 0:
            seed_gifts = [
                ("儿童绘本一套", "3-6 岁适用，共 12 本，品相良好", "2026-03-01", "小明妈妈", 1, cat_map.get("图书文具"), "爱心妈妈李女士", "13800138001", "物业前台"),
                ("电热水壶", "1.5L，使用约 1 年，功能正常", "2026-03-05", "邻居阿华", 0, cat_map.get("家居用品"), "201室张先生", "13800138002", "菜鸟驿站"),
                ("折叠晾衣架", "可收纳，适合小户型阳台", "2026-03-08", "302 室小李", 1, cat_map.get("家居用品"), "阳光大姐王阿姨", "13800138003", "楼道口"),
                ("冬季厚棉被", "8 斤重，已清洗晾晒", "2026-03-10", "社区志愿者", 0, cat_map.get("家居用品"), "退休教师陈奶奶", "13800138004", "物业前台"),
                ("闲置键盘", "机械键盘青轴，部分键帽有磨损", "2026-03-12", "程序员小王", 0, cat_map.get("数码电子"), "IT工程师老刘", "13800138005", "菜鸟驿站"),
            ]
            conn.executemany(
                """
                INSERT INTO gifts
                    (item_name, description, gift_date, recipient_nickname, is_taken, category_id, donor_nickname, donor_phone, location)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                seed_gifts,
            )
            conn.commit()

        gift_rows = conn.execute("SELECT id, item_name FROM gifts ORDER BY id").fetchall()
        gift_map = {r["item_name"]: r["id"] for r in gift_rows}

        resv_count = conn.execute("SELECT COUNT(*) FROM reservations").fetchone()[0]
        if resv_count == 0:
            seed_reservations = [
                (gift_map.get("电热水壶"), "张阿姨", "2026-03-06 10:30:00", RESERVATION_STATUS_PENDING),
                (gift_map.get("冬季厚棉被"), "501室王姐", "2026-03-11 14:20:00", RESERVATION_STATUS_CONFIRMED),
                (gift_map.get("闲置键盘"), "学生小李", "2026-03-13 09:15:00", RESERVATION_STATUS_CANCELLED),
                (gift_map.get("折叠晾衣架"), "社区赵叔", "2026-03-09 15:00:00", RESERVATION_STATUS_PENDING),
            ]
            conn.executemany(
                """
                INSERT INTO reservations
                    (gift_id, reserver_nickname, reserve_time, status)
                VALUES (?, ?, ?, ?)
                """,
                seed_reservations,
            )

        note_count = conn.execute("SELECT COUNT(*) FROM gift_notes").fetchone()[0]
        if note_count == 0:
            seed_notes = [
                (gift_map.get("儿童绘本一套"), "物品已清洗消毒，可放心使用", "2026-03-01 09:00:00"),
                (gift_map.get("儿童绘本一套"), "接收人已确认取走，孩子很喜欢", "2026-03-02 14:30:00"),
                (gift_map.get("电热水壶"), "底座稍有磨损，但不影响使用", "2026-03-05 11:00:00"),
                (gift_map.get("折叠晾衣架"), "已预约社区赵叔本周末上门领取", "2026-03-08 16:00:00"),
                (gift_map.get("折叠晾衣架"), "赵叔已取走，表示感谢", "2026-03-10 10:00:00"),
                (gift_map.get("冬季厚棉被"), "棉被已重新晾晒，保暖性好", "2026-03-10 08:30:00"),
                (gift_map.get("闲置键盘"), "赠送人说明可免费维修更换键帽", "2026-03-12 15:00:00"),
            ]
            conn.executemany(
                """
                INSERT INTO gift_notes
                    (gift_id, content, created_at)
                VALUES (?, ?, ?)
                """,
                seed_notes,
            )

        volunteer_count = conn.execute("SELECT COUNT(*) FROM volunteers").fetchone()[0]
        if volunteer_count == 0:
            seed_volunteers = [
                ("张建国", "13900139001", "工作日晚上、周六全天", "家电维修、技术支持", "2026-01-15", 1),
                ("李美玲", "13900139002", "周末全天", "儿童辅导、活动组织", "2026-02-10", 1),
                ("王大伟", "13900139003", "周六下午、周日上午", "物资搬运、场地布置", "2026-02-20", 1),
                ("陈丽华", "13900139004", "工作日上午", "医疗咨询、健康讲座", "2026-03-01", 0),
                ("刘志强", "13900139005", "周末全天、工作日晚间", "法律咨询、纠纷调解", "2026-03-08", 1),
            ]
            conn.executemany(
                """
                INSERT INTO volunteers
                    (name, phone, service_time, skill_category, register_date, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                seed_volunteers,
            )
        conn.commit()
    finally:
        conn.close()
