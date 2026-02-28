-- =====================================================
-- LLM提供商信息表初始化数据
-- 说明: 此脚本仅包含INSERT语句，用于初始化数据
--       表结构由SQLAlchemy的create_all()自动创建
-- =====================================================

-- 插入LLM提供商配置数据
-- 使用INSERT IGNORE避免重复插入
INSERT IGNORE INTO `core_llm_provider` (`id`, `name`, `tag`, `api_key`, `api_base`, `create_time`, `update_time`) VALUES
(1, '火山引擎 ', 'volcengine', '94cb30d9-260b-4ff4-bbce-94f70bf70282', 'https://ark.cn-beijing.volces.com/api/v3', '2025-06-02 16:10:50', '2025-06-02 16:10:52'),
(2, 'DeepSeek', 'deepseek', 'sk-5c57ec89cbe8470ea823ae2afbcd0d3c', 'https://api.deepseek.com/v1', '2025-06-02 16:11:21', '2025-06-02 16:11:26'),
(3, 'Moonshot AI', 'moonshot', 'sk-kwx1PRDTtS4XbxW13u5sq8f19LzQEJEoCTSNuOu2gFT77RxS', 'https://api.moonshot.cn/v1', '2025-06-02 16:12:11', '2025-06-02 16:12:13'),
(4, '智谱AI', 'glm', '8f35caac9ab0a68779ecef4b1673b7fd.bGenP7A79YafJWye', 'https://open.bigmodel.cn/api/paas/v4/', '2025-06-02 16:12:26', '2025-06-02 16:12:29');
