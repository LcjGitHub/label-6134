import os
import random
import sqlite3
from pathlib import Path

from datetime import date, datetime

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = Path(os.environ.get("GIFT_DB_PATH", str(DATA_DIR / "gift.db")))


def generate_verification_code() -> str:
    return f"{random.randint(0, 999999):06d}"

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
        "verification_code": row["verification_code"] if "verification_code" in row.keys() else None,
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


def row_to_flow_history(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "gift_id": row["gift_id"],
        "action_type": row["action_type"],
        "operator_nickname": row["operator_nickname"],
        "operated_at": row["operated_at"],
        "description": row["description"],
    }


def add_flow_history(conn: sqlite3.Connection, gift_id: int, action_type: str, operator_nickname: str, description: str) -> None:
    conn.execute(
        """
        INSERT INTO gift_flow_history (gift_id, action_type, operator_nickname, operated_at, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        (gift_id, action_type, operator_nickname, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), description),
    )


def row_to_location(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "sort_order": row["sort_order"],
    }


def row_to_announcement(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "content": row["content"],
        "publisher_nickname": row["publisher_nickname"],
        "publish_time": row["publish_time"],
        "is_pinned": bool(row["is_pinned"]),
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

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                publisher_nickname TEXT NOT NULL DEFAULT '',
                publish_time TEXT NOT NULL,
                is_pinned INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS gift_flow_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gift_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                operator_nickname TEXT NOT NULL DEFAULT '',
                operated_at TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (gift_id) REFERENCES gifts(id) ON DELETE CASCADE
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

        if "verification_code" not in existing_cols:
            conn.execute("ALTER TABLE gifts ADD COLUMN verification_code TEXT DEFAULT NULL")
            gift_rows = conn.execute(
                "SELECT id, is_taken FROM gifts WHERE verification_code IS NULL"
            ).fetchall()
            for r in gift_rows:
                if not bool(r["is_taken"]):
                    code = generate_verification_code()
                    conn.execute(
                        "UPDATE gifts SET verification_code = ? WHERE id = ?",
                        (code, r["id"]),
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
            for gift in seed_gifts:
                is_taken = gift[4]
                verification_code = None if is_taken else generate_verification_code()
                conn.execute(
                    """
                    INSERT INTO gifts
                        (item_name, description, gift_date, recipient_nickname, is_taken, category_id, donor_nickname, donor_phone, location, verification_code)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (*gift, verification_code),
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

        announcement_count = conn.execute("SELECT COUNT(*) FROM announcements").fetchone()[0]
        if announcement_count == 0:
            seed_announcements = [
                (
                    "社区旧物赠送平台正式上线",
                    "各位邻居大家好！社区旧物赠送流转平台已正式启用。您可以在此登记家中闲置物品，供有需要的邻居免费领取。让我们一起践行低碳环保，共建温馨社区！",
                    "物业管理员小王",
                    "2026-03-01 09:00:00",
                    1,
                ),
                (
                    "本周六社区跳蚤市场活动通知",
                    "本周六（3月15日）上午9:00-12:00，社区中心广场将举办跳蚤市场活动，欢迎各位居民带上家中闲置物品前来参与。现场将设置免费领取区和交换区，期待您的到来！",
                    "社区活动中心",
                    "2026-03-10 14:30:00",
                    1,
                ),
                (
                    "关于规范物品领取的温馨提示",
                    "近期发现个别邻居领取物品后未及时更新状态，请大家在领取物品后及时标记为「已取走」，以便物品赠送人了解情况。感谢您的配合与支持！",
                    "志愿者李阿姨",
                    "2026-03-08 10:15:00",
                    0,
                ),
                (
                    "春季衣物捐赠活动持续进行中",
                    "春季衣物捐赠活动仍在进行，如有干净整洁的换季衣物需要捐赠，可送至物业前台。所有衣物将统一整理后捐赠给有需要的家庭。",
                    "物业管理员小王",
                    "2026-03-05 16:00:00",
                    0,
                ),
                (
                    "闲置数码物品赠送提醒",
                    "目前平台上有少量闲置数码物品（键盘、鼠标等）等待领取，有需要的居民朋友可在「赠送记录」页面查看详情。先到先得哦！",
                    "热心邻居老刘",
                    "2026-03-12 11:20:00",
                    0,
                ),
            ]
            conn.executemany(
                """
                INSERT INTO announcements
                    (title, content, publisher_nickname, publish_time, is_pinned)
                VALUES (?, ?, ?, ?, ?)
                """,
                seed_announcements,
            )

        loc_count = conn.execute("SELECT COUNT(*) FROM locations").fetchone()[0]
        if loc_count == 0:
            seed_locations = [
                ("楼道口", 1),
                ("物业前台", 2),
                ("菜鸟驿站", 3),
                ("社区活动中心", 4),
                ("小区大门岗亭", 5),
            ]
            conn.executemany(
                "INSERT INTO locations (name, sort_order) VALUES (?, ?)",
                seed_locations,
            )

        conn.commit()
    finally:
        conn.close()
