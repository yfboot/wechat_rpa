-- 创建数据库
CREATE DATABASE IF NOT EXISTS rpa_news_helper
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE rpa_news_helper;

-- 文章表
CREATE TABLE articles (
                          id INT AUTO_INCREMENT PRIMARY KEY COMMENT '文章ID，自增主键',
                          title VARCHAR(255) NOT NULL COMMENT '文章标题',
                          source VARCHAR(100) NOT NULL COMMENT '文章来源，如公众号名称',
                          publish_time DATETIME NOT NULL COMMENT '文章发布时间',
                          url VARCHAR(512) NOT NULL COMMENT '文章链接',
                          summary TEXT COMMENT '文章概述',
                          tags VARCHAR(100) DEFAULT NULL COMMENT '文章标签，逗号分隔',
                          views INT DEFAULT 0 COMMENT '阅读量',
                          crawl_time DATETIME NOT NULL COMMENT '爬取时间',
                          keywords VARCHAR(255) DEFAULT NULL COMMENT '匹配到的关键词，逗号分隔',
                          INDEX idx_publish_time (publish_time),
                          INDEX idx_source (source),
                          INDEX idx_tags (tags),
                          FULLTEXT INDEX idx_content (title, summary) COMMENT '全文索引，用于内容搜索'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文章信息表';

-- 群组表
CREATE TABLE group_list (
                        id INT AUTO_INCREMENT PRIMARY KEY COMMENT '群组ID，自增主键',
                        name VARCHAR(100) NOT NULL COMMENT '微信群名称',
                        description VARCHAR(255) DEFAULT NULL COMMENT '群组描述',
                        is_active TINYINT(1) DEFAULT 1 COMMENT '是否激活，1-激活，0-禁用',
                        create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                        update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                        UNIQUE KEY idx_name (name) COMMENT '群名唯一索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='微信群组信息表';

-- 消息模板表
CREATE TABLE message_templates (
                                   id INT AUTO_INCREMENT PRIMARY KEY COMMENT '模板ID，自增主键',
                                   name VARCHAR(100) NOT NULL COMMENT '模板名称',
                                   content TEXT NOT NULL COMMENT '模板内容，支持变量',
                                   description VARCHAR(255) DEFAULT NULL COMMENT '模板描述',
                                   is_active TINYINT(1) DEFAULT 1 COMMENT '是否激活，1-激活，0-禁用',
                                   create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                                   update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                                   UNIQUE KEY idx_template_name (name) COMMENT '模板名称唯一索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息模板表';

-- 发送任务表
CREATE TABLE send_tasks (
                            id INT AUTO_INCREMENT PRIMARY KEY COMMENT '任务ID，自增主键',
                            group_id INT NOT NULL COMMENT '群组ID，关联groups表',
                            template_id INT DEFAULT NULL COMMENT '模板ID，关联message_templates表',
                            custom_message TEXT DEFAULT NULL COMMENT '自定义消息，当不使用模板时使用',
                            schedule_time DATETIME DEFAULT NULL COMMENT '计划发送时间，NULL表示立即发送',
                            is_auto_send TINYINT(1) DEFAULT 1 COMMENT '是否自动发送，1-自动发送，0-手动发送',
                            status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending' COMMENT '任务状态',
                            error_message VARCHAR(255) DEFAULT NULL COMMENT '错误信息，任务失败时记录',
                            create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                            update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                            INDEX idx_group_id (group_id),
                            INDEX idx_template_id (template_id),
                            INDEX idx_status (status),
                            INDEX idx_schedule_time (schedule_time),
                            FOREIGN KEY (group_id) REFERENCES group_list(id) ON DELETE CASCADE,
                            FOREIGN KEY (template_id) REFERENCES message_templates(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息发送任务表';

-- 任务文章关联表
CREATE TABLE task_articles (
                               id INT AUTO_INCREMENT PRIMARY KEY COMMENT '关联ID，自增主键',
                               task_id INT NOT NULL COMMENT '任务ID，关联send_tasks表',
                               article_id INT NOT NULL COMMENT '文章ID，关联articles表',
                               position INT DEFAULT 0 COMMENT '文章在消息中的顺序位置',
                               create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                               UNIQUE KEY idx_task_article (task_id, article_id) COMMENT '任务-文章唯一索引',
                               INDEX idx_task_id (task_id),
                               INDEX idx_article_id (article_id),
                               FOREIGN KEY (task_id) REFERENCES send_tasks(id) ON DELETE CASCADE,
                               FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务文章关联表';

-- 发送日志表
CREATE TABLE send_logs (
                           id INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID，自增主键',
                           task_id INT NOT NULL COMMENT '任务ID，关联send_tasks表',
                           send_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '发送时间',
                           status ENUM('success', 'failed') NOT NULL COMMENT '发送状态',
                           message TEXT DEFAULT NULL COMMENT '实际发送的消息内容',
                           error_message VARCHAR(255) DEFAULT NULL COMMENT '错误信息，发送失败时记录',
                           create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                           INDEX idx_task_id (task_id),
                           INDEX idx_send_time (send_time),
                           INDEX idx_status (status),
                           FOREIGN KEY (task_id) REFERENCES send_tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息发送日志表';

-- 系统配置表
CREATE TABLE system_config (
                               id INT AUTO_INCREMENT PRIMARY KEY COMMENT '配置ID，自增主键',
                               config_key VARCHAR(50) NOT NULL COMMENT '配置键名',
                               config_value TEXT NOT NULL COMMENT '配置值',
                               description VARCHAR(255) DEFAULT NULL COMMENT '配置描述',
                               create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                               update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                               UNIQUE KEY idx_config_key (config_key) COMMENT '配置键名唯一索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- 关键词表
CREATE TABLE keywords (
                          id INT AUTO_INCREMENT PRIMARY KEY COMMENT '关键词ID，自增主键',
                          keyword VARCHAR(50) NOT NULL COMMENT '关键词',
                          category VARCHAR(50) DEFAULT NULL COMMENT '关键词分类',
                          is_active TINYINT(1) DEFAULT 1 COMMENT '是否激活，1-激活，0-禁用',
                          create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                          update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                          UNIQUE KEY idx_keyword (keyword) COMMENT '关键词唯一索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='关键词表';

-- 初始数据导入
-- 导入系统配置
INSERT INTO system_config (config_key, config_value, description) VALUES
                                                        ('wechat_path', 'D:\\app\\WeChat\\WeChat.exe', '微信安装路径'),
                                                        ('search_shortcut', '["ctrl", "f"]', '微信搜索快捷键'),
                                                        ('search_method_priority', '[1, 2, 3]', '群聊搜索方式优先级'),
                                                        ('calibration_timeout', '10', '校准等待时间(秒)'),
                                                        ('auto_send', 'true', '是否自动发送消息');

-- 导入默认消息模板
INSERT INTO message_templates (name, content, description) VALUES
    ('资讯速递模板', '📰 今日资讯速递 ({date}) 📰\n\n{content}\n\n📌 点击文章标题链接可直接阅读原文\n\n--这是rpa自动发送的消息\n消息发送时间: {time}', '用于每日资讯推送的标准模板');