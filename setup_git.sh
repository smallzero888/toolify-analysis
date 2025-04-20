#!/bin/bash

# 确保脚本在错误时停止
set -e

echo "🚀 开始设置 Git 仓库..."

# 初始化 Git 仓库
git init

# 创建 .gitignore
echo "创建 .gitignore 文件..."
cat > .gitignore << EOL
# Python
__pycache__/
*.py[cod]
*$py.class
.Python
env/
build/
dist/
*.egg-info/
.env
toolify_env/
venv/
.idea/
.vscode/
output/
toolify_data/
*.log
chromedriver*
*.xlsx
*.xls
EOL

# 添加所有文件
echo "添加文件到 Git..."
git add .

# 创建首次提交
echo "创建首次提交..."
git commit -m "Initial commit: Toolify AI product analysis tool"

# 提示用户添加远程仓库
echo "
✅ 本地仓库已设置完成！

接下来请执行以下步骤：

1. 在 GitHub 上创建新仓库：https://github.com/new
   - 仓库名：toolify-analysis
   - 描述：Toolify AI product analysis tool
   - 选择 Public
   - 不要初始化仓库

2. 然后运行以下命令（替换 YOUR_USERNAME 为你的 GitHub 用户名）：

   git remote add origin https://github.com/YOUR_USERNAME/toolify-analysis.git
   git push -u origin main

"