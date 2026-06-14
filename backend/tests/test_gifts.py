import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from db import init_db, get_db


@pytest.fixture()
def tmp_db_path(tmp_path):
    db_file = str(tmp_path / "test_gift.db")
    os.environ["GIFT_DB_PATH"] = db_file
    import db as db_mod
    db_mod.DB_PATH = db_file
    init_db()
    yield db_file
    os.environ.pop("GIFT_DB_PATH", None)


@pytest.fixture()
def client(tmp_db_path):
    from app import app
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _insert_gift(conn, item_name="测试物品", donor_phone="13800138000", is_taken=0):
    conn.execute(
        """INSERT INTO gifts
           (item_name, description, gift_date, recipient_nickname, is_taken, category_id, donor_nickname, donor_phone, location)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (item_name, "描述", "2026-06-01", "接收人", is_taken, None, "赠送人", donor_phone, "物业前台"),
    )
    conn.commit()
    row = conn.execute("SELECT last_insert_rowid()").fetchone()
    return row[0]


class TestListGifts:

    def test_list_all_gifts(self, client, tmp_db_path):
        resp = client.get("/api/gifts")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_filter_by_item_name(self, client, tmp_db_path):
        conn = get_db()
        _insert_gift(conn, item_name="儿童绘本一套", donor_phone="13900139001")
        _insert_gift(conn, item_name="电热水壶", donor_phone="13900139002")
        conn.close()

        resp = client.get("/api/gifts?item_name=绘本")
        assert resp.status_code == 200
        data = resp.get_json()
        assert all("绘本" in g["item_name"] for g in data)
        assert any(g["item_name"] == "儿童绘本一套" for g in data)
        assert not any(g["item_name"] == "电热水壶" for g in data)

    def test_filter_by_item_name_no_match(self, client, tmp_db_path):
        resp = client.get("/api/gifts?item_name=不存在的物品")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data == []


class TestCreateGift:

    def test_create_success(self, client, tmp_db_path):
        payload = {
            "item_name": "全新测试物品",
            "donor_phone": "13900139099",
            "gift_date": "2026-06-14",
            "donor_nickname": "测试赠送人",
            "location": "测试地点",
        }
        resp = client.post("/api/gifts", json=payload)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["item_name"] == "全新测试物品"
        assert data["donor_phone"] == "13900139099"

    def test_create_phone_empty(self, client, tmp_db_path):
        payload = {
            "item_name": "测试物品",
            "donor_phone": "",
        }
        resp = client.post("/api/gifts", json=payload)
        assert resp.status_code == 400
        data = resp.get_json()
        assert "联系电话不能为空" in data["error"]

    def test_create_phone_invalid_length(self, client, tmp_db_path):
        payload = {
            "item_name": "测试物品",
            "donor_phone": "12345",
        }
        resp = client.post("/api/gifts", json=payload)
        assert resp.status_code == 400
        data = resp.get_json()
        assert "联系电话必须为11位数字" in data["error"]

    def test_create_phone_non_digits(self, client, tmp_db_path):
        payload = {
            "item_name": "测试物品",
            "donor_phone": "13800abcde",
        }
        resp = client.post("/api/gifts", json=payload)
        assert resp.status_code == 400
        data = resp.get_json()
        assert "联系电话必须为11位数字" in data["error"]

    def test_create_item_name_empty(self, client, tmp_db_path):
        payload = {
            "item_name": "",
            "donor_phone": "13800138000",
        }
        resp = client.post("/api/gifts", json=payload)
        assert resp.status_code == 400
        data = resp.get_json()
        assert "物品名不能为空" in data["error"]


class TestMarkGiftTaken:

    def test_mark_taken_success(self, client, tmp_db_path):
        conn = get_db()
        gift_id = _insert_gift(conn, item_name="待取走物品", donor_phone="13800001111", is_taken=0)
        conn.close()

        resp = client.put(f"/api/gifts/{gift_id}/mark-taken")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["is_taken"] is True
        assert data["id"] == gift_id

    def test_mark_taken_duplicate(self, client, tmp_db_path):
        conn = get_db()
        gift_id = _insert_gift(conn, item_name="已取走物品", donor_phone="13800002222", is_taken=1)
        conn.close()

        resp = client.put(f"/api/gifts/{gift_id}/mark-taken")
        assert resp.status_code == 400
        data = resp.get_json()
        assert "已标记为取走" in data["error"]

    def test_mark_taken_not_found(self, client, tmp_db_path):
        resp = client.put("/api/gifts/99999/mark-taken")
        assert resp.status_code == 404
        data = resp.get_json()
        assert "记录不存在" in data["error"]

    def test_mark_taken_idempotent_check(self, client, tmp_db_path):
        conn = get_db()
        gift_id = _insert_gift(conn, item_name="幂等测试物品", donor_phone="13800003333", is_taken=0)
        conn.close()

        resp1 = client.put(f"/api/gifts/{gift_id}/mark-taken")
        assert resp1.status_code == 200

        resp2 = client.put(f"/api/gifts/{gift_id}/mark-taken")
        assert resp2.status_code == 400
        assert "已标记为取走" in resp2.get_json()["error"]
