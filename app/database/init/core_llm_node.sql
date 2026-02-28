-- =====================================================
-- LLM节点表初始化数据
-- 说明: 此脚本仅包含INSERT语句，用于初始化数据
--       表结构由SQLAlchemy的create_all()自动创建
-- =====================================================

-- 插入LLM节点配置数据
-- 使用INSERT IGNORE避免重复插入
INSERT IGNORE INTO `core_llm_node` (`id`, `name`, `description`, `service_module`, `function_name`, `model_name`, `parameter`, `provider_id`, `is_stream`, `create_time`, `update_time`) VALUES
-- chatflow 模块节点 (ainvoke 使用 glm-4.7-flashx)
(1, 'test_llm_node', 'llm调用测试node结点', 'test', '测试llm_node结点', 'glm-4.7-flashx', '{"top_p": 0.1, "max_tokens": 8192, "temperature": 0.01}', 4, 1, '2026-02-27 10:10:50', '2026-02-27 10:10:50');

-- (11, 'image_understanding', '图像理解', 'chatflow', 'image_understanding', 'glm-4v-flash', '{"top_p": 0.1, "max_tokens": 8192, "temperature": 0.01}', 4, 1, '2026-02-27 10:10:50', '2026-02-27 10:10:50');

