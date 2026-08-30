# API 接口简要说明

统一响应：`{ "code": 0, "message": "success", "data": {...} }`，`code=0` 为成功。
通用错误码：1001 参数错误(422) / 1002 鉴权失败(401) / 1003 权限不足(403) / 1004 资源不存在(404) /
2001 模型不可用(502) / 2002 模型输出不合规(502) / 5000 服务端异常(500)。
所有业务接口需 `Authorization: Bearer <token>`。

## 认证
| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | /api/v1/auth/register | 注册（API 层保留，UI 仅登录） |
| POST | /api/v1/auth/login | 登录 → token + user(含 is_admin) |
| POST | /api/v1/auth/change-password | 修改密码 {old_password, new_password} |
| GET | /api/v1/auth/me | 当前用户信息 |

## 标准分页约定（四条列表接口统一）
入参：`page`(1 起) / `page_size` / `filter_keyword`(关键词) / `grade`(分级筛选)；
返回：`{ "total": int, "records": [...] }`。筛选条件变更时前端页码重置为 1。

| 接口 | 入参补充说明 | grade 取值 |
| --- | --- | --- |
| GET /api/v1/history | + platform, date_from, date_to | script / titles / copywriting |
| GET /api/v1/batch/tasks | 任务名关键词 | pending/running/completed/partial/failed/cancelled |
| GET /api/v1/templates | （兼容 scene_type） | script / style / prompt |
| GET /api/v1/admin/users | 仅管理员 | admin / normal |
| GET /api/v1/admin/logs | 仅管理员 | INFO / WARNING / ERROR |

## 内容生成
| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | /api/v1/script/generate | 脚本套装（demo 参数=演示数据不落库；word_budget_min/max 字数约束） |
| POST | /api/v1/titles/generate | 10 标题 + 3+3+6 标签；action=polish 二次润色 |
| POST | /api/v1/copywriting/transform | action: rewrite/expand/condense/style_transfer/polish/proofread/dedupe |
| POST | /api/v1/tts/optimize | 规则引擎秒回：{text,sentences,mode,total_chars,est_duration_sec} |

## 批量异步
| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | /api/v1/batch/tasks | JSON 入参 {name, topics[], platform, duration, style} → task_id |
| POST | /api/v1/batch/tasks/upload | multipart 文件（txt/csv/xlsx），每行一个主题，上限 50 |
| GET | /api/v1/batch/tasks/{id} | 进度：total/success/failed/items[](条目级错误) |
| POST | /api/v1/batch/tasks/{id}/retry | 重试失败条目 |
| POST | /api/v1/batch/tasks/{id}/cancel | 终止 |
| GET | /api/v1/batch/tasks/{id}/download | 结果 Excel |
| GET | /api/v1/batch/tasks/{id}/download-docx | 结果 Word 打包（zip） |
| GET | /api/v1/batch/template | 导入模板下载 |

## 历史 / 模板 / 导出
| 方法 | 路径 | 说明 |
| --- | --- | --- |
| PUT/DELETE | /api/v1/history/{id} | 二次编辑 / 软删除；DELETE /{id}/hard 永久删除；POST /{id}/restore 恢复 |
| POST | /api/v1/history/bulk-delete / bulk-purge / bulk-export | 批量软删 / 永久删 / 打包导出 {ids:[]} |
| GET/POST/PUT/DELETE | /api/v1/templates、/templates/{id} | 模板 CRUD |
| POST | /api/v1/export/script | 前端套装直出 Word（无需落库） |
| GET | /api/v1/export/record/{id} | 历史记录导出 Word |
| GET | /api/v1/system/status | 模型链健康（ollama/cloud/mock + active_provider + db） |
| GET/POST | /api/v1/system/config | 运行时配置读取（Key 脱敏）/ 热更新（立即生效，不重启） |

## 在线调试
服务启动后访问 `http://127.0.0.1:8000/docs`（Swagger UI，可在线执行）。
