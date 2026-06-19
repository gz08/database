# 学生管理系统

## 一、项目简介

本项目为数据库课程大作业，基于 **openGauss + Python + Streamlit** 开发，主题为 **学生管理系统**。

系统面向学校教学管理场景，主要实现学生、教师/教务、系统管理员三类角色下的信息管理、课程管理、选课管理、成绩管理、查询与权限控制等功能。



---

## 二、项目背景与作业要求对应关系

### 1. 题目要求

课程大作业允许自定义题目，示例包括：

- 药店管理系统
- 学籍信息管理系统
- 图书管理系统
- 超市商品销售管理系统
- 医疗信息管理系统

本项目选择的自定义题目为：

**学生管理系统**

---

### 2. 开发技术要求

根据课程要求，系统应基于 **华为 openGauss** 建立数据库应用系统。

本项目采用技术栈：

- 数据库：openGauss
- 后端语言：Python
- 前端界面：Streamlit
- 部署方式：本地 Docker 中运行 openGauss，Python 本地连接数据库

---





## 三、系统角色设计

本系统包含 3 类角色：

### 1. 系统管理员

负责系统级管理，主要包括：

- 管理教师/教务账号
- 管理学生账号
- 分配用户角色
- 重置密码
- 启用/禁用账号
- 查看系统整体数据

### 2. 教师/教务

负责教学业务管理，主要包括：

- 查看学生信息（仅查看，不做新增/删除/修改）
- 管理课程信息
- 查看选课记录
- 录入与修改成绩
- 查询学生与课程相关信息

### 3. 学生

负责个人业务操作，主要包括：

- 登录系统
- 查看个人信息
- 查看课程列表
- 选课/退课
- 查询个人成绩

---

## 四、系统核心功能

### 1. 用户登录与身份识别

- 用户名密码登录
- 根据角色进入不同页面
- 保存登录状态
- 权限控制

### 2. 用户与权限管理

- 系统管理员创建账号
- 分配角色（管理员/教师/学生）
- 禁用或启用账号
- 重置密码

### 3. 学生信息管理

权限口径：
- 管理员负责新增、修改、删除
- 教师/教务仅查看学生信息

- 新增学生信息
- 修改学生信息
- 删除学生信息
- 查询学生信息
- 支持按学号、姓名等条件查询

### 4. 课程信息管理

- 新增课程
- 修改课程
- 删除课程
- 查询课程
- 支持按课程编号、课程名称查询

### 5. 选课管理

- 学生选课
- 学生退课
- 查看学生已选课程
- 查看某门课程选课名单

### 6. 成绩管理

- 教师/教务录入成绩
- 教师/教务修改成绩
- 学生查询个人成绩
- 按课程或学生维度查询成绩

### 7. 查询功能

- 精确查询
- 模糊查询（如 `LIKE`）
- 多表关联查询
- 简单统计查询

> 注意：课程要求中明确提到查询功能若仅实现精确查询，分数会受影响，因此本项目必须包含模糊查询功能。

---

## 五、数据库设计概览

系统最小核心数据表包括：

- `roles`：角色表
- `users`：用户表
- `students`：学生表
- `teachers`：教师表
- `courses`：课程表
- `enrollments`：选课表
- `grades`：成绩表

这些表共同支撑：

- 登录认证
- 权限控制
- 学生管理
- 课程管理
- 选课管理
- 成绩管理

---

## 六、项目结构

```text
student_management_system/
├─ app.py
├─ README.md
├─ AGENTS.md
├─ requirements.txt
├─ core/
│  ├─ db.py
│  ├─ auth.py
│  ├─ models.py
│  ├─ services.py
│  └─ utils.py
├─ pages/
│  ├─ pages_admin.py
│  ├─ pages_teacher.py
│  └─ pages_student.py
├─ sql/
│  ├─ schema.sql
│  └─ seed.sql
├─ scripts/
│  └─ init_db.py
└─ docs/
   ├─ design.md
   └─ TASKS.md
```

---

## 七、代码分层与依赖（协作开发必看）

一句话：`app.py` 负责入口和角色分流；`pages/` 负责界面；`core/` 负责认证、业务和数据库访问；`sql/` 放数据库脚本；`scripts/` 负责初始化执行。

### 1. 根目录

- `app.py`：系统入口，处理登录态，按角色把请求分发到不同页面。

### 2. `core/`（后端核心层）

- `core/db.py`：数据库连接、执行 SQL、事务提交回滚。
- `core/models.py`：所有表的 CRUD 和查询（直接写 SQL 的地方）。
- `core/services.py`：业务规则层（校验、选课规则、成绩规则、权限辅助逻辑）。
- `core/auth.py`：登录校验、密码哈希、用户认证相关逻辑。
- `core/utils.py`：通用工具（会话状态、通用校验、通用渲染辅助）。

### 3. `pages/`（页面层）

- `pages/pages_admin.py`：管理员页面（账号管理、学生管理、全局查看）。
- `pages/pages_teacher.py`：教师页面（查看学生、课程管理、成绩管理）。
- `pages/pages_student.py`：学生页面（个人信息、选课退课、成绩查询）。

### 4. `sql/` 与 `scripts/`

- `sql/schema.sql`：建表、约束、索引定义。
- `sql/seed.sql`：初始角色、测试账号、测试业务数据。
- `scripts/init_db.py`：按顺序执行 `schema.sql` 和 `seed.sql`。

### 5. 依赖关系（从上到下）

```text
app.py
  -> pages/pages_admin.py | pages/pages_teacher.py | pages/pages_student.py
  -> core/auth.py

pages/*
  -> core/services.py
  -> core/models.py
  -> core/utils.py

core/services.py
  -> core/models.py

core/auth.py
  -> core/models.py

core/models.py
  -> core/db.py
  -> openGauss
```

---

## 八、运行命令（PowerShell）

### 1. 安装依赖

```powershell
python -m pip install streamlit psycopg2-binary
```

### 2. 配置数据库连接（当前项目默认连接参数）

```powershell
$env:DB_HOST="127.0.0.1"
$env:DB_PORT="15432"
$env:DB_NAME="postgres"
$env:DB_USER="db_user"
$env:DB_PASSWORD="DbUser@123"
```

### 3. 初始化数据库（建表 + 导入种子数据）

```powershell
python scripts/init_db.py
```

### 4. 启动系统

```powershell
streamlit run app.py
```

先打开powersell
输入：
wsl -d openEuler-24.03
su - omm
gsql -d postgres -p 15432 -r
然后
ALTER SYSTEM SET listen_addresses = '*';
\q
gs_ctl restart
gsql -d postgres -p 15432 -r
CREATE USER db_user WITH PASSWORD 'DbUser@123';
ALTER ROLE db_user WITH LOGIN;
GRANT ALL PRIVILEGES ON DATABASE postgres TO db_user;
GRANT CREATE, CONNECT ON DATABASE postgres TO db_user;
\q
上面步骤开机后需要运行的：
wsl -d openEuler-24.03
su - omm
gs_ctl start
开新一个powersell，之后操作步骤：
cd C:\Users\19879\Desktop\database_project_final\database
$env:DB_HOST="127.0.0.1"
$env:DB_PORT="5432"
$env:DB_NAME="postgres"
$env:DB_USER="db_user"
$env:DB_PASSWORD="DbUser@123"
python scripts/init_db.py
streamlit run app.py

账号+密码：
admin_demo	admin123	管理员
teacher_demo	teacher123	教师
student_demo	student123	学生
grade1_demo	student123	学生（Grade 1）
grade2_mid_demo	student123	学生（Grade 2，中等）
grade2_risk_demo	student123	学生（Grade 2，风险）
