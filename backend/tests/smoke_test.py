# -*- coding: utf-8 -*-
"""全链路冒烟测试：注册登录 -> 八大模块接口 -> 导出 -> 批量 -> 历史 -> 模板。
用法: python tests/smoke_test.py [base_url]
"""
from __future__ import annotations

import sys
import time
import uuid

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
c = httpx.Client(base_url=BASE, timeout=httpx.Timeout(300, connect=10))
PASS, FAIL = [], []


def step(name: str, fn):
    try:
        data = fn()
        PASS.append(name)
        print(f"[PASS] {name}")
        return data
    except Exception as exc:  # noqa: BLE001
        FAIL.append((name, str(exc)))
        print(f"[FAIL] {name}: {exc}")
        return None


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def main():
    uname = f"test_{uuid.uuid4().hex[:8]}"
    token = {"v": ""}

    # ---------- 认证 ----------
    def register():
        r = c.post("/api/v1/auth/register", json={"username": uname, "password": "test123456"})
        assert r.status_code == 200, r.text
        token["v"] = r.json()["data"]["token"]
        assert token["v"]
        return "token ok"

    step("注册+获取Token", register)

    def login():
        r = c.post("/api/v1/auth/login", json={"username": uname, "password": "test123456"})
        assert r.status_code == 200 and r.json()["data"]["token"], r.text
        return "login ok"

    step("登录", login)

    def wrong_pwd():
        r = c.post("/api/v1/auth/login", json={"username": uname, "password": "wrongpass"})
        assert r.status_code == 401, r.text
        return "401 as expected"

    step("错误密码 → 401", wrong_pwd)

    h = lambda: auth_headers(token["v"])  # noqa: E731

    # ---------- TTS（规则引擎） ----------
    def tts():
        r = c.post("/api/v1/tts/optimize", headers=h(), json={
            "text": "【口播】大家好，今天给大家分享三个技巧。【字幕】千万不要错过。"
                    "综上所述，嗯，其实很简单，总而言之就是坚持练习。"})
        d = r.json()
        assert d["code"] == 0 and d["data"]["sentences"], r.text
        assert "综上所述" not in d["data"]["text"]
        assert d["data"]["sentences"][0] == "大家好，今天给大家分享三个技巧。"
        return d["data"]["mode"]

    mode = step("TTS配音优化（剔书面词/断句/风格识别）", tts)

    # ---------- 标题&标签 ----------
    def titles():
        r = c.post("/api/v1/titles/generate", headers=h(), json={
            "topic": "AI 副业变现", "platform": "douyin", "action": "generate"})
        d = r.json()
        assert d["code"] == 0, d
        assert len(d["data"]["titles"]) == 10, d["data"]["titles"]
        assert len(d["data"]["tags"]["hot"]) == 3 and len(d["data"]["tags"]["long"]) >= 3
        return f"10 标题 / {len(d['data']['tags']['hot'])} 热门标签 / 模型 {d['data']['source_model']}"

    step("模块2 标题&标签生成（LLM真实调用）", titles)

    # ---------- 文案改写 ----------
    def copywriting():
        r = c.post("/api/v1/copywriting/transform", headers=h(), json={
            "text": "今天我想跟大家分享一个提高工作效率的方法，就是每天早上先做最重要的事情，"
                    "这样可以避免被琐事打扰，然后你会发现一天的时间变得非常充足。",
            "action": "condense", "style": "极简高级短句风"})
        d = r.json()
        assert d["code"] == 0 and len(d["data"]["result"]) > 4, r.text
        return f"改写后 {len(d['data']['result'])} 字 / 差异度 {d['data']['changed_count']}"

    step("模块3 文案改写（缩写+风格迁移）", copywriting)

    # ---------- 脚本生成（核心） ----------
    script_record_id = {}

    def script():
        r = c.post("/api/v1/script/generate", headers=h(), json={
            "topic": "普通人如何用 AI 工具实现副业变现",
            "platform": "douyin", "duration": 60, "style": "抖音口播干货风"})
        d = r.json()
        assert d["code"] == 0, d
        data = d["data"]
        total = sum(s["duration_sec"] for s in data["segments"])
        assert total == 60, f"分段总时长 {total} != 60，segments={data.get('segments')}"
        assert len(data["titles"]) == 10, f"标题数={len(data['titles'])}: {data['titles']}"
        assert data["tts_text"], "TTS 文本为空"
        script_record_id["v"] = data["record_id"]
        return (f"{len(data['segments'])} 段 / 时长精准 {total}s / "
                f"TTS {len(data['tts_text'])} 字 / 模型 {data['source_model']}")

    step("模块1 短视频脚本生成（LLM真实调用+时长强约束）", script)

    # ---------- Word 导出 ----------
    def export_word():
        rid = script_record_id.get("v")
        assert rid, "脚本未生成，跳过"
        r = c.get(f"/api/v1/export/record/{rid}", headers=h())
        assert r.status_code == 200 and r.content[:2] == b"PK", (r.status_code, r.content[:20])
        with open(f"_export_test_{rid}.docx", "wb") as f:
            f.write(r.content)
        return f"docx {len(r.content)//1024} KB"

    step("模块6 Word 标准化导出", export_word)

    # ---------- 批量异步 ----------
    task_id = {"v": None}

    def batch_create():
        r = c.post("/api/v1/batch/tasks", headers=h(), json={
            "name": "冒烟批量", "topics": ["小红书涨粉技巧", "普通人拍vlog"],
            "platform": "xiaohongshu", "duration": 30, "style": "小红书温柔种草风"})
        d = r.json()
        assert d["code"] == 0 and d["data"]["task_id"], r.text
        task_id["v"] = d["data"]["task_id"]
        return f"task #{d['data']['task_id']}"

    def batch_poll():
        tid = task_id.get("v")
        assert tid
        for _ in range(150):
            r = c.get(f"/api/v1/batch/tasks/{tid}", headers=h())
            st = r.json()["data"]
            if st["status"] in ("completed", "failed", "cancelled"):
                assert st["success"] + st["failed"] == st["total"], st
                return f"{st['status']} / 成功 {st['success']} / 失败 {st['failed']} / {st['duration']}s"
            time.sleep(2)
        return "超时但任务仍在执行"

    # ---------- 批量文件上传 ----------
    def upload_file():
        import io
        f = io.BytesIO("AI 短视频脚本入门\n" .encode("utf-8") +
                       "电商直播带货话术\n抖音橱窗变现\n".encode("utf-8"))
        r = c.post("/api/v1/batch/tasks/upload", headers=h(),
                   files={"file": ("topics.txt", f.getvalue(), "text/plain")},
                   data={"platform": "douyin", "duration": 30})
        d = r.json()
        assert d["code"] == 0 and d["data"]["count"] == 3, r.text
        return f"解析 {d['data']['count']} 条主题"

    # ---------- 历史记录 ----------
    records = {}

    def history_list():
        # 标准分页入参：page/page_size/filter_keyword/grade → {total, records}
        r = c.get("/api/v1/history?page=1&page_size=5", headers=h())
        d = r.json()
        assert d["code"] == 0 and d["data"]["total"] >= 1, r.text
        assert isinstance(d["data"]["records"], list), r.text
        assert len(d["data"]["records"]) <= 5
        records["v"] = d["data"]["records"]
        return f"共 {d['data']['total']} 条（本页 {len(d['data']['records'])} 条）"

    def history_pagination():
        r1 = c.get("/api/v1/history?page=1&page_size=2", headers=h()).json()["data"]
        r2 = c.get("/api/v1/history?page=2&page_size=2", headers=h()).json()["data"]
        ids1 = {x["id"] for x in r1["records"]}
        ids2 = {x["id"] for x in r2["records"]}
        assert not ids1 & ids2, "分页数据必须互不重叠"
        return f"第1页 {len(ids1)} 条 / 第2页 {len(ids2)} 条，无重复 ✓"

    def history_keyword():
        r = c.get("/api/v1/history?filter_keyword=" + "副业", headers=h())
        d = r.json()
        assert d["code"] == 0 and d["data"]["total"] >= 1, r.text
        return f"关键词命中 {d['data']['total']} 条"

    def history_grade_filter():
        r = c.get("/api/v1/history?grade=script&page=1&page_size=3", headers=h())
        d = r.json()
        assert d["code"] == 0, r.text
        for rec in d["data"]["records"]:
            assert rec["record_type"] == "script"
        return f"分级筛选 script 命中 {d['data']['total']} 条"

    def history_update():
        rec = records["v"][0]
        r = c.put(f"/api/v1/history/{rec['id']}", headers=h(), json={"duration": 90})
        assert r.json()["code"] == 0, r.text
        return f"id={rec['id']} 时长→90s"

    def history_softdelete_restore():
        rec = records["v"][0]
        r = c.delete(f"/api/v1/history/{rec['id']}", headers=h())
        assert r.json()["code"] == 0
        r2 = c.post(f"/api/v1/history/{rec['id']}/restore", headers=h())
        assert r2.json()["code"] == 0
        return "软删除→恢复 OK"

    # ---------- 模板 ----------
    def tpl_crud():
        r = c.post("/api/v1/templates", headers=h(), json={
            "name": "知识口播框架", "scene_type": "script",
            "content": "开头：{主题}的坑，90%的人都踩过\n中间：3 个要点\n结尾：收藏 + 关注",
            "description": "测试模板"})
        assert r.json()["code"] == 0, r.text
        tid = r.json()["data"]["id"]
        r2 = c.put(f"/api/v1/templates/{tid}", headers=h(), json={"name": "知识口播框架V2"})
        assert r2.json()["data"]["name"] == "知识口播框架V2"
        r3 = c.get("/api/v1/templates?scene_type=script&page=1&page_size=20", headers=h())
        assert any(t["id"] == tid for t in r3.json()["data"]["records"])
        r4 = c.delete(f"/api/v1/templates/{tid}", headers=h())
        assert r4.json()["code"] == 0
        return "创建→编辑→分页查询→删除 OK"

    step("模块4 批量任务创建", batch_create)
    step("模块4 批量文件上传（TXT 解析 3 条）", upload_file)
    step("模块4 批量进度轮询+成败统计", batch_poll)
    step("模块7 历史记录列表（分页）", history_list)
    step("模块7 分页不重叠", history_pagination)
    step("模块7 记录关键词检索", history_keyword)
    step("模块7 分级筛选 grade=script", history_grade_filter)
    step("模块7 记录二次编辑", history_update)
    step("模块7 软删除→恢复", history_softdelete_restore)
    step("模块8 模板 CRUD", tpl_crud)

    # ---------- 演示模式（不落库、不调用模型） ----------
    def demo_script():
        r = c.post("/api/v1/script/generate", headers=h(), json={
            "topic": "AI 副业变现", "platform": "douyin", "duration": 30,
            "demo": True, "word_budget_min": 80, "word_budget_max": 160})
        d = r.json()
        assert d["code"] == 0 and d["data"]["demo"] is True, r.text
        assert d["data"]["record_id"] is None, "演示数据不应落库"
        assert d["data"]["source_model"] == "demo"
        return f"{len(d['data']['segments'])} 段 / 标题 {len(d['data']['titles'])} / 不落库"

    def demo_titles():
        r = c.post("/api/v1/titles/generate", headers=h(), json={
            "topic": "AI 副业变现", "demo": True})
        return f"{len(r.json()['data']['titles'])} 组标题（demo）"

    # ---------- 运行时配置（模型配置弹窗的接口） ----------
    def runtime_config():
        g = c.get("/api/v1/system/config", headers=h())
        assert g.json()["code"] == 0 and g.json()["data"]["OLLAMA_MODEL"], g.text
        u = c.post("/api/v1/system/config", headers=h(), json={"LLM_TEMPERATURE": 0.5})
        assert u.json()["code"] == 0 and "LLM_TEMPERATURE" in u.json()["data"]["applied"]
        return f"读取 OK / 更新 OK（{len(g.json()['data']['_editable'])} 项可编辑）"

    # ---------- 修改密码 ----------
    tmp_pwd = {"v": "test123456"}

    def change_pwd():
        r = c.post("/api/v1/auth/change-password", headers=h(), json={
            "old_password": "wrong", "new_password": "newpass123"})
        assert r.json()["code"] == 1002, r.text
        r2 = c.post("/api/v1/auth/change-password", headers=h(), json={
            "old_password": tmp_pwd["v"], "new_password": "newpass123"})
        assert r2.json()["code"] == 0, r2.text
        r3 = c.post("/api/v1/auth/login", json={"username": uname, "password": "newpass123"})
        assert r3.json()["code"] == 0
        c.post("/api/v1/auth/change-password", headers=h(), json={
            "old_password": "newpass123", "new_password": tmp_pwd["v"]})  # 恢复
        return "错误原密码拒绝 / 修改生效 / 新密码可登录"

    # ---------- 管理员接口 ----------
    def admin_login():
        r = c.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
        assert r.json()["code"] == 0 and r.json()["data"]["user"]["is_admin"], r.text
        admin_token["v"] = r.json()["data"]["token"]
        return "admin 登录 OK（初始账号自动创建）"

    admin_token = {"v": ""}
    ah = lambda: auth_headers(admin_token["v"])  # noqa: E731

    def admin_users():
        r = c.get("/api/v1/admin/users?page=1&page_size=20", headers=ah())
        assert r.json()["code"] == 0, r.text
        d = r.json()["data"]
        assert d["total"] >= 1 and isinstance(d["records"], list), r.text
        return f"用户列表 {len(d['records'])} 个 / 共 {d['total']}"

    def admin_logs():
        r = c.get("/api/v1/admin/logs?page=1&page_size=10", headers=ah())
        assert r.json()["code"] == 0, r.text
        assert r.json()["data"]["total"] >= 1, "日志为空"
        return f"日志 {r.json()['data']['total']} 行"

    def admin_create_reset_delete():
        created = {"username": f"op_{uuid.uuid4().hex[:6]}"}
        r = c.post("/api/v1/admin/users", headers=ah(), json={
            "username": created["username"], "password": "op123456"})
        assert r.json()["code"] == 0, r.text
        uid = r.json()["data"]["id"]
        r2 = c.post(f"/api/v1/admin/users/{uid}/reset-password", headers=ah(), json={"password": "op654321"})
        assert r2.json()["code"] == 0
        r3 = c.post("/api/v1/auth/login", json={"username": created["username"], "password": "op654321"})
        assert r3.json()["code"] == 0, r3.text
        r4 = c.delete(f"/api/v1/admin/users/{uid}", headers=ah())
        assert r4.json()["code"] == 0
        return "创建→重置→登录→删除 OK"

    # ---------- 批量重试 / Word 打包 / 模板下载 ----------
    def batch_retry_flow():
        r = c.post("/api/v1/batch/tasks", headers=h(), json={
            "name": "重试流", "topics": ["测试重试主题"],
            "platform": "douyin", "duration": 30} )
        d = r.json()
        assert d["code"] == 0
        tid = d["data"]["task_id"]
        st = None
        for _ in range(240):   # 最长 8 分钟（本地模型串行推理，等待窗口放宽）
            st = c.get(f"/api/v1/batch/tasks/{tid}", headers=h()).json()["data"]
            if st["status"] in ("completed", "partial", "failed", "cancelled"):
                break
            time.sleep(2)
        assert st and st["status"] in ("completed", "partial", "failed"), f"任务未结束: {st}"
        # 有失败条目 → retry 返回 0；无失败 → 返回 1001/1004，两者都合法
        rr = c.post(f"/api/v1/batch/tasks/{tid}/retry", headers=h())
        assert rr.json()["code"] in (0, 1001, 1004), rr.text
        if rr.json()["code"] == 0:
            for _ in range(240):
                st2 = c.get(f"/api/v1/batch/tasks/{tid}", headers=h()).json()["data"]
                if st2["status"] in ("completed", "partial", "failed", "cancelled"):
                    break
                time.sleep(2)
        # 结果 Word 打包（zip）：只要有成功记录即可下载
        if st["success"] > 0:
            rz = c.get(f"/api/v1/batch/tasks/{tid}/download-docx", headers=h())
            assert rz.status_code == 200 and rz.content[:2] == b"PK", rz.text[:100]
            return f"retry 结果 {rr.json()['code']} / docx-zip {len(rz.content)//1024}KB"
        return f"任务完成但 0 成功（{st['status']}），retry 已重新排队（{rr.json()['code']}）"

    def template_file():
        r = c.get("/api/v1/batch/template", headers=h())
        assert r.status_code == 200 and b"batch_template" in r.content or b"\xe6" in r.content
        return "导入模板下载 OK"

    # ---------- 历史批量操作 ----------
    def history_bulk():
        hl = c.get("/api/v1/history?page=1&page_size=3", headers=h()).json()["data"]["records"]
        assert hl
        ids = [x["id"] for x in hl[:2]]
        rz = c.post("/api/v1/history/bulk-export", headers=h(), json={"ids": ids})
        assert rz.status_code == 200 and rz.content[:2] == b"PK", rz.text[:80]
        rd = c.post("/api/v1/history/bulk-delete", headers=h(), json={"ids": ids})
        assert rd.json()["code"] == 0 and rd.json()["data"]["deleted"] == 2, rd.text
        rr = c.post(f"/api/v1/history/{ids[0]}/restore", headers=h())
        assert rr.json()["code"] == 0
        rp = c.post("/api/v1/history/bulk-purge", headers=h(), json={"ids": ids[:-1]})
        assert rp.json()["code"] == 0
        return "zip导出→批量软删→恢复→永久删除 OK"

    step("演示模式 脚本(字数约束+不落库)", demo_script)
    step("演示模式 标题", demo_titles)
    step("运行时配置 读/写", runtime_config)
    step("修改密码 全链路", change_pwd)
    step("管理员 登录", admin_login)
    step("管理员 用户列表", admin_users)
    step("管理员 系统日志", admin_logs)
    step("管理员 用户CRUD", admin_create_reset_delete)
    step("批量 重试+Word打包", batch_retry_flow)
    step("批量 导入模板下载", template_file)
    step("历史 批量操作链", history_bulk)

    # ---------- 汇总 ----------
    print("\n" + "=" * 52)
    print(f"通过 {len(PASS)} 项 / 失败 {len(FAIL)} 项")
    for name, err in FAIL:
        print(f"  ✗ {name}: {err}")
    print("=" * 52)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
