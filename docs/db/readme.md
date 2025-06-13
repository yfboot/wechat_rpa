# 微信自动发送群消息工具数据库设计文档

## 一、数据库表清单

本数据库共包含8个表：
1. **articles** - 文章信息表
2. **group_list** - 微信群组信息表
3. **message_templates** - 消息模板表
4. **send_tasks** - 消息发送任务表
5. **task_articles** - 任务文章关联表
6. **send_logs** - 消息发送日志表
7. **system_config** - 系统配置表
8. **keywords** - 关键词表

## 二、表关系图

```
+-------------+       +---------------+       +-------------------+       +-------------+
| articles    |       | task_articles |       | send_tasks        |       | group_list  |
+-------------+       +---------------+       +-------------------+       +-------------+
| id          |<----->| id            |       | id                |------>| id          |
| title       |       | task_id       |<----->| group_id          |       | name        |
| source      |       | article_id    |       | template_id       |------>| description |
| publish_time|       | position      |       | custom_message    |       | is_active   |
| url         |       | create_time   |       | schedule_time     |       | create_time |
| summary     |       +---------------+       | is_auto_send      |       | update_time |
| tags        |                               | status            |       +-------------+
| views       |                               | error_message     |
| crawl_time  |                               | create_time       |
| keywords    |                               | update_time       |
+-------------+                               +-------------------+
                                                       |
                                                       |
                                                       v
+-------------+       +-------------------+    +---------------+
| keywords    |       | message_templates |    | send_logs     |
+-------------+       +-------------------+    +---------------+
| id          |       | id                |    | id            |
| keyword     |       | name              |    | task_id       |
| category    |       | content           |    | send_time     |
| is_active   |       | description       |    | status        |
| create_time |       | is_active         |    | message       |
| update_time |       | create_time       |    | error_message |
|             |       | update_time       |    | create_time   |
+-------------+       | update_time       |    +---------------+
                      +-------------------+
+----------------+
| system_config  |
+----------------+
| id             |
| config_key     |
| config_value   |
| description    |
| create_time    |
| update_time    |
+----------------+
```

## 三、表字段详细设计

### 1. 文章表（articles）

| 字段名 | 类型 | 长度 | 允许为空 | 默认值 | 主键 | 索引 | 说明 |
|--------|------|------|----------|--------|------|------|------|
| id | INT | - | 否 | - | 是 | 主键 | 文章ID，自增主键 |
| title | VARCHAR | 255 | 否 | - | 否 | 全文索引 | 文章标题 |
| source | VARCHAR | 100 | 否 | - | 否 | 普通索引 | 文章来源，如公众号名称 |
| publish_time | DATETIME | - | 否 | - | 否 | 普通索引 | 文章发布时间 |
| url | VARCHAR | 512 | 否 | - | 否 | - | 文章链接 |
| summary | TEXT | - | 是 | NULL | 否 | 全文索引 | 文章概述 |
| tags | VARCHAR | 100 | 是 | NULL | 否 | 普通索引 | 文章标签，逗号分隔 |
| views | INT | - | 是 | 0 | 否 | - | 阅读量 |
| crawl_time | DATETIME | - | 否 | - | 否 | - | 爬取时间 |
| keywords | VARCHAR | 255 | 是 | NULL | 否 | - | 匹配到的关键词，逗号分隔 |

### 2. 群组表（group_list）

| 字段名 | 类型 | 长度 | 允许为空 | 默认值 | 主键 | 索引 | 说明 |
|--------|------|------|----------|--------|------|------|------|
| id | INT | - | 否 | - | 是 | 主键 | 群组ID，自增主键 |
| name | VARCHAR | 100 | 否 | - | 否 | 唯一索引 | 微信群名称 |
| description | VARCHAR | 255 | 是 | NULL | 否 | - | 群组描述 |
| is_active | TINYINT | 1 | 是 | 1 | 否 | - | 是否激活，1-激活，0-禁用 |
| create_time | DATETIME | - | 是 | CURRENT_TIMESTAMP | 否 | - | 创建时间 |
| update_time | DATETIME | - | 是 | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 否 | - | 更新时间 |

### 3. 消息模板表（message_templates）

| 字段名 | 类型 | 长度 | 允许为空 | 默认值 | 主键 | 索引 | 说明 |
|--------|------|------|----------|--------|------|------|------|
| id | INT | - | 否 | - | 是 | 主键 | 模板ID，自增主键 |
| name | VARCHAR | 100 | 否 | - | 否 | 唯一索引 | 模板名称 |
| content | TEXT | - | 否 | - | 否 | - | 模板内容，支持变量 |
| description | VARCHAR | 255 | 是 | NULL | 否 | - | 模板描述 |
| is_active | TINYINT | 1 | 是 | 1 | 否 | - | 是否激活，1-激活，0-禁用 |
| create_time | DATETIME | - | 是 | CURRENT_TIMESTAMP | 否 | - | 创建时间 |
| update_time | DATETIME | - | 是 | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 否 | - | 更新时间 |

### 4. 发送任务表（send_tasks）

| 字段名 | 类型 | 长度 | 允许为空 | 默认值 | 主键 | 索引 | 说明 |
|--------|------|------|----------|--------|------|------|------|
| id | INT | - | 否 | - | 是 | 主键 | 任务ID，自增主键 |
| group_id | INT | - | 否 | - | 否 | 外键，普通索引 | 群组ID，关联group_list表 |
| template_id | INT | - | 是 | NULL | 否 | 外键，普通索引 | 模板ID，关联message_templates表 |
| custom_message | TEXT | - | 是 | NULL | 否 | - | 自定义消息，当不使用模板时使用 |
| schedule_time | DATETIME | - | 是 | NULL | 否 | 普通索引 | 计划发送时间，NULL表示立即发送 |
| is_auto_send | TINYINT | 1 | 是 | 1 | 否 | - | 是否自动发送，1-自动发送，0-手动发送 |
| status | ENUM | - | 是 | 'pending' | 否 | 普通索引 | 任务状态，取值：pending,processing,completed,failed |
| error_message | VARCHAR | 255 | 是 | NULL | 否 | - | 错误信息，任务失败时记录 |
| create_time | DATETIME | - | 是 | CURRENT_TIMESTAMP | 否 | - | 创建时间 |
| update_time | DATETIME | - | 是 | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 否 | - | 更新时间 |

### 5. 任务文章关联表（task_articles）

| 字段名 | 类型 | 长度 | 允许为空 | 默认值 | 主键 | 索引 | 说明 |
|--------|------|------|----------|--------|------|------|------|
| id | INT | - | 否 | - | 是 | 主键 | 关联ID，自增主键 |
| task_id | INT | - | 否 | - | 否 | 外键，普通索引 | 任务ID，关联send_tasks表 |
| article_id | INT | - | 否 | - | 否 | 外键，普通索引 | 文章ID，关联articles表 |
| position | INT | - | 是 | 0 | 否 | - | 文章在消息中的顺序位置 |
| create_time | DATETIME | - | 是 | CURRENT_TIMESTAMP | 否 | - | 创建时间 |

**特殊索引：**
- `UNIQUE KEY idx_task_article (task_id, article_id)` - 任务-文章唯一索引，防止重复关联

### 6. 发送日志表（send_logs）

| 字段名 | 类型 | 长度 | 允许为空 | 默认值 | 主键 | 索引 | 说明 |
|--------|------|------|----------|--------|------|------|------|
| id | INT | - | 否 | - | 是 | 主键 | 日志ID，自增主键 |
| task_id | INT | - | 否 | - | 否 | 外键，普通索引 | 任务ID，关联send_tasks表 |
| send_time | DATETIME | - | 是 | CURRENT_TIMESTAMP | 否 | 普通索引 | 发送时间 |
| status | ENUM | - | 否 | - | 否 | 普通索引 | 发送状态，取值：success,failed |
| message | TEXT | - | 是 | NULL | 否 | - | 实际发送的消息内容 |
| error_message | VARCHAR | 255 | 是 | NULL | 否 | - | 错误信息，发送失败时记录 |
| create_time | DATETIME | - | 是 | CURRENT_TIMESTAMP | 否 | - | 创建时间 |

### 7. 系统配置表（system_config）

| 字段名 | 类型 | 长度 | 允许为空 | 默认值 | 主键 | 索引 | 说明 |
|--------|------|------|----------|--------|------|------|------|
| id | INT | - | 否 | - | 是 | 主键 | 配置ID，自增主键 |
| config_key | VARCHAR | 50 | 否 | - | 否 | 唯一索引 | 配置键名 |
| config_value | TEXT | - | 否 | - | 否 | - | 配置值 |
| description | VARCHAR | 255 | 是 | NULL | 否 | - | 配置描述 |
| create_time | DATETIME | - | 是 | CURRENT_TIMESTAMP | 否 | - | 创建时间 |
| update_time | DATETIME | - | 是 | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 否 | - | 更新时间 |

### 8. 关键词表（keywords）

| 字段名 | 类型 | 长度 | 允许为空 | 默认值 | 主键 | 索引 | 说明 |
|--------|------|------|----------|--------|------|------|------|
| id | INT | - | 否 | - | 是 | 主键 | 关键词ID，自增主键 |
| keyword | VARCHAR | 50 | 否 | - | 否 | 唯一索引 | 关键词 |
| category | VARCHAR | 50 | 是 | NULL | 否 | - | 关键词分类 |
| is_active | TINYINT | 1 | 是 | 1 | 否 | - | 是否激活，1-激活，0-禁用 |
| create_time | DATETIME | - | 是 | CURRENT_TIMESTAMP | 否 | - | 创建时间 |
| update_time | DATETIME | - | 是 | CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 否 | - | 更新时间 |

## 四、表关系说明

1. **articles** 和 **task_articles** 之间：一对多关系，一篇文章可以被多个任务引用
2. **task_articles** 和 **send_tasks** 之间：多对一关系，一个任务可以包含多篇文章
3. **send_tasks** 和 **group_list** 之间：多对一关系，一个群组可以有多个发送任务
4. **send_tasks** 和 **message_templates** 之间：多对一关系，一个模板可以用于多个任务
5. **send_tasks** 和 **send_logs** 之间：一对多关系，一个任务可以有多条日志记录

## 五、外键约束说明

### 5.1 发送任务表（send_tasks）外键约束
- `FOREIGN KEY (group_id) REFERENCES group_list(id) ON DELETE CASCADE`
  - 当群组被删除时，相关的发送任务也会被删除
- `FOREIGN KEY (template_id) REFERENCES message_templates(id) ON DELETE SET NULL`
  - 当消息模板被删除时，相关任务的模板ID设为NULL

### 5.2 任务文章关联表（task_articles）外键约束
- `FOREIGN KEY (task_id) REFERENCES send_tasks(id) ON DELETE CASCADE`
  - 当任务被删除时，相关的文章关联记录也会被删除
- `FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE`
  - 当文章被删除时，相关的关联记录也会被删除

### 5.3 发送日志表（send_logs）外键约束
- `FOREIGN KEY (task_id) REFERENCES send_tasks(id) ON DELETE CASCADE`
  - 当任务被删除时，相关的日志记录也会被删除

## 六、索引设计说明

### 6.1 性能优化索引
- **articles表**：为发布时间、来源、标签创建索引，提升查询性能
- **send_tasks表**：为群组ID、模板ID、状态、计划时间创建索引
- **send_logs表**：为任务ID、发送时间、状态创建索引

### 6.2 全文搜索索引
- **articles表**：对标题和概述字段创建全文索引，支持内容搜索

### 6.3 唯一性约束索引
- **group_list表**：群名唯一索引，防止重复群组
- **message_templates表**：模板名称唯一索引
- **system_config表**：配置键名唯一索引
- **keywords表**：关键词唯一索引
- **task_articles表**：任务-文章唯一索引，防止重复关联

## 七、数据库配置

- **字符集**：utf8mb4
- **排序规则**：utf8mb4_unicode_ci
- **存储引擎**：InnoDB
- **数据库名**：rpa_news_helper

