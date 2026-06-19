# 贡献指南

感谢你考虑为灵眸量化 (SmartQuant Dashboard) 贡献代码！

## 提交流程

1. Fork 仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/)：

- `feat: 新增 K 线 5 分钟周期`
- `fix: 修复回测引擎日期过滤 bug`
- `docs: 更新 API 文档`
- `test: 增加回测引擎单测`
- `refactor: 重构 watchlist 模块`
- `chore: 升级依赖`

## 代码规范

### Python (后端)
- 风格: PEP 8 + Black (line length 100)
- 类型注解: 必须
- 测试: pytest，覆盖率 > 60%
- Docstring: 关键函数必须有

### Vue 3 (前端)
- Composition API + `<script setup lang="ts">`
- 命名: 组件 PascalCase，变量 camelCase
- 状态: Pinia store

## 报告 Bug

用 [GitHub Issues](https://github.com/xxx/sqd/issues) 提交，需包含：
- 复现步骤
- 期望行为
- 实际行为
- 截图（如果是 UI 问题）
- 环境（OS / Python 版本 / 浏览器版本）

## 功能建议

同样在 Issues 提出，标签 `enhancement`。

## 联系方式

- 邮件: TBD
- 微信群: TBD
- Discord: TBD
