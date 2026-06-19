# 推送代码到 GitHub 指南

本仓库已经初始化为本地 git 仓库，所有代码已经分批 commit。
**你只需要做最后一步：在 GitHub 上创建空仓库 + 推上来。**

## 1. 在 GitHub 创建空仓库

1. 打开 https://github.com/new
2. **Repository name**: `sqd` (或者 `lingmou-quant` / 你喜欢的名字)
3. **Description**: `灵眸量化 - 本地化一站式行情+策略+实盘看板`
4. **Public / Private**: 选 Public（开源）或 Private（私有）都可以
5. ⚠️ **不要勾选** "Add a README file" / "Add .gitignore" / "Choose a license"
   （我们本地已经有 README 和 .gitignore，避免冲突）
6. 点 **Create repository**

## 2. 推送方式（三选一）

### 方式 A: GitHub Desktop (最简单, 推荐)

1. 下载安装: https://desktop.github.com/
2. 登录你的 GitHub 账号
3. File → Add Local Repository → 选 `C:\Users\Administrator\.openclaw\workspace\sqd`
4. 点 "Publish repository" 按钮
5. 完成 ✅

### 方式 B: HTTPS + Personal Access Token (PAT)

```powershell
# 1. 创建 PAT: https://github.com/settings/tokens/new
#    - 选 Fine-grained token 或 Classic (勾 repo 权限)
#    - 复制生成的 token (ghp_xxxx...)

# 2. 添加远程
cd C:\Users\Administrator\.openclaw\workspace\sqd
git remote add origin https://github.com/<你的用户名>/sqd.git

# 3. 推送
git push -u origin main
# 第一次会要求输入:
#   Username: <你的 GitHub 用户名>
#   Password: <粘贴 PAT>
```

### 方式 C: SSH Key (适合经常 push)

```powershell
# 1. 生成 SSH 密钥
ssh-keygen -t ed25519 -C "292289308@qq.com"
# 一路回车

# 2. 复制公钥
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub" | Set-Clipboard

# 3. 添加到 GitHub: https://github.com/settings/keys
#    点 "New SSH key", 粘贴, 命名, 保存

# 4. 推送
cd C:\Users\Administrator\.openclaw\workspace\sqd
git remote add origin git@github.com:<你的用户名>/sqd.git
git push -u origin main
```

## 3. 推送后

- 在 GitHub 仓库页面刷新，应该能看到所有文件
- README.md 会自动渲染成项目首页
- /docs 文件夹里的 .md 也会渲染

## 4. 常见问题

### Q: 推送时报错 "Repository not found"
A: 检查远程 URL 拼写，用户名大小写敏感

### Q: 推送时报错 "Permission denied"
A: 用方式 A 或 B, 方式 C 需先配 SSH key

### Q: 想换用户名/邮箱 commit author
```powershell
cd C:\Users\Administrator\.openclaw\workspace\sqd
git config user.name "你的GitHub用户名"
git config user.email "292289308@qq.com"
# 修改所有 commit 的 author (可选)
git rebase -i --root
# 把每个 pick 改成 r, 然后改作者
```

### Q: 想改 remote URL
```powershell
git remote set-url origin <新URL>
```
