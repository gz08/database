# 学生管理系统 完整说明文档
## 一、项目简介
本项目为数据库课程大作业，基于 **Python + Streamlit + openGauss（兼容PostgreSQL）** 开发B/S架构学生管理系统，面向学校教学管理场景，实现多角色权限隔离的教务管理能力。
- 核心角色：管理员、教师/教务、学生（三角色权限严格隔离）
- 登录方式：账号密码登录 + 人脸识别免密登录
- 核心功能：选课管理、多维度成绩管理、Excel批量导入导出、AI教学/学习分析、电子成绩单、全链路操作审计日志
- 技术栈细节：
  - 前端：Streamlit自定义美化虚化背景UI，自适应多终端
  - 数据库：openEuler WSL内置openGauss数据库（兼容PostgreSQL）
  - 特色能力：本地人脸特征存储、操作日志自动入库、课程权重自动核算、大模型学情分析

## 二、系统角色与核心功能
### 1. 系统管理员
- 全局数据仪表盘，账号统计
- 账号全生命周期管理：增删改、密码重置、启用/禁用；支持Excel批量导入导出
- 学生档案单条/批量管理，自动生成学生账号
- 操作审计日志管理：多条件筛选、单条删除、一键清空日志
- 全系统数据权限控制

### 2. 教师/教务
- 自有课程管理：创建、编辑、删除（有成绩的课程不可删除）
- 学生选课记录查看，出勤/实验/考试分项成绩录入
- 成绩批量导入（支持进度条+错误导出），自动按权重计算总分
- AI生成班级专属教学方案，定位薄弱学生
- 学生信息查看（仅查看，无增删改权限）
- 课程/成绩多维度查询（精确+模糊查询、多表关联查询、简单统计查询）

### 3. 学生
- 同年级课程选课/退课（有成绩的课程不可退课）
- 个人信息查看、人脸注册（本地摄像头采集）、人脸核验后自助修改密码
- 个人成绩查询、多维度成绩分析
- AI个性化7天学习计划生成
- 带电子印章的HTML格式成绩单导出

## 三、目录结构
```
database_project_final/
├── app.py                # 程序入口、登录页、角色路由
├── core/                 # 核心底层模块
│   ├── db.py             # 数据库连接、自动创建operation_log日志表
│   ├── auth.py           # 密码加密、登录校验
│   ├── face_auth.py      # 摄像头人脸采集、特征比对
│   ├── ai_agent.py       # 智匠大模型学情分析接口
│   ├── models.py         # 全表CRUD、日志读写函数
│   ├── services.py       # 业务校验、权限控制
│   └── utils.py          # UI工具、会话管理、日志封装
├── pages/                # 角色页面
│   ├── pages_admin.py    # 管理员后台（含审计日志）
│   ├── pages_teacher.py  # 教师课程/成绩管理
│   ├── pages_student.py  # 学生选课、成绩单、人脸注册
│   ├── ai_teaching.py    # 教师AI教学方案
│   └── ai_tutor.py       # 学生AI学习计划
├── scripts/
│   └── init_db.py        # 数据库初始化脚本（执行建表+种子数据）
├── sql/
│   ├── schema.sql        # 建表、约束、索引定义
│   └── seed.sql          # 初始角色、测试账号、测试业务数据
├── static/               # 背景图、公章静态资源
├── face_data/embeddings/ # 人脸特征pkl存储目录
├── requirements.txt      # Python依赖清单
├── README.md             # 项目说明文档
├── AGENTS.md             # AI代理相关说明
└── docs/
    ├── design.md         # 设计文档
    └── TASKS.md          # 任务文档
```

## 四、代码分层与依赖关系
### 分层说明
- `app.py`：系统入口，处理登录态，按角色分发请求到对应页面
- `pages/`：页面层，负责各角色前端界面渲染
- `core/`：后端核心层，负责认证、业务规则、数据库交互
- `sql/`：数据库脚本层，存储建表和种子数据脚本
- `scripts/`：工具脚本层，负责数据库初始化

### 依赖关系（从上到下）
```
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

## 五、前置环境要求
1. Windows系统，预装WSL，镜像版本：`openEuler-24.03`
2. Python 3.9及以上版本
3. WSL内已部署openGauss数据库
4. 摄像头（人脸识别功能必备）

## 六、openGauss数据库部署与配置
### 6.1 首次部署数据库（仅第一次安装执行）
打开Windows PowerShell，按以下步骤执行：
```powershell
# 进入openEuler WSL系统
wsl -d openEuler-24.03
# 切换数据库管理员omm
su - omm
# 登录gsql客户端
gsql -d postgres -p 15432 -r
# 允许外部本地连接数据库
ALTER SYSTEM SET listen_addresses = '*';
# 退出客户端，重启数据库服务
\q
gs_ctl restart
# 重启完成后再次登录创建业务账号
gsql -d postgres -p 15432 -r
# 执行账号创建与授权SQL
CREATE USER db_user WITH PASSWORD 'DbUser@123';
ALTER ROLE db_user WITH LOGIN;
GRANT ALL PRIVILEGES ON DATABASE postgres TO db_user;
GRANT CREATE, CONNECT ON DATABASE postgres TO db_user;
# 退出gsql
\q
exit
```

### 6.2 电脑重启后启动数据库（每次开机必执行）
新建PowerShell窗口执行以下命令，**启动成功后保留此窗口不关闭**：
```powershell
wsl -d openEuler-24.03
su - omm
gs_ctl start
```

## 七、项目启动流程（Windows PowerShell）
### 7.1 进入项目目录
```powershell
cd C:\Users\19879\Desktop\database_project_final\database
```

### 7.2 配置数据库环境变量（当前终端生效）
```powershell
$env:DB_HOST="127.0.0.1"
$env:DB_PORT="5432"
$env:DB_NAME="postgres"
$env:DB_USER="db_user"
$env:DB_PASSWORD="DbUser@123"
```

### 7.3 安装Python依赖
```powershell
pip install -r requirements.txt
```
**requirements.txt 依赖清单**：
```
streamlit
psycopg2-binary
opencv-python
insightface
numpy
pandas
openpyxl
requests
```

### 7.4 创建本地资源文件夹（缺失会导致页面报错）
```powershell
mkdir static
mkdir face_data\embeddings
```
static文件夹需放入以下文件：
1. 数据库大作业背景图（去水印）.png
2. 公章.png

### 7.5 初始化数据库（建表 + 导入种子数据）
```powershell
python scripts/init_db.py
```

### 7.6 启动系统服务
```powershell
streamlit run app.py
```
启动成功后自动打开浏览器，访问地址：http://localhost:8501

## 八、数据库表结构说明
共8张核心业务表，`operation_log`操作审计日志为核心必备表：
1. `roles`：角色表（admin/teacher/student）
2. `users`：登录账号表（SHA256加密密码）
3. `teachers`：教师档案表
4. `students`：学生档案表
5. `courses`：课程表（含出勤/实验/考试权重配置，权重合计强制100%）
6. `enrollments`：选课记录表（学生-课程唯一关联）
7. `grades`：分项成绩表（自动加权计算总分）
8. `operation_log`：操作审计日志表（所有增删改操作自动记录）

> 补充：core/db.py程序启动时会自动执行`init_operation_log()`创建日志表；全新数据库建议手动执行完整建表SQL，避免启动报错。

## 九、完整建表SQL（手动初始化备用）
可在WSL gsql中执行，包含所有业务表及审计日志表：
```sql
-- 1. 角色表
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(20) NOT NULL UNIQUE,
    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO roles (role_name) VALUES ('admin'), ('teacher'), ('student')
ON CONFLICT (role_name) DO NOTHING;

-- 2. 用户账号表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(64) NOT NULL,
    role_id INT NOT NULL REFERENCES roles(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 教师档案表
CREATE TABLE IF NOT EXISTS teachers (
    id SERIAL PRIMARY KEY,
    user_id INT NULL UNIQUE REFERENCES users(id),
    teacher_no VARCHAR(30) NOT NULL UNIQUE,
    full_name VARCHAR(50) NOT NULL,
    department VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 学生档案表
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    user_id INT NULL UNIQUE REFERENCES users(id),
    student_no VARCHAR(30) NOT NULL UNIQUE,
    full_name VARCHAR(50) NOT NULL,
    gender VARCHAR(10) NOT NULL CHECK (gender IN ('M','F','Other')),
    grade_year INT NOT NULL CHECK (grade_year BETWEEN 1 AND 8),
    major VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NULL,
    email VARCHAR(100) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. 课程表
CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    course_code VARCHAR(30) NOT NULL UNIQUE,
    course_name VARCHAR(100) NOT NULL,
    course_outline VARCHAR(100) NULL,
    credits NUMERIC(3,1) NOT NULL CHECK (credits > 0 AND credits <=10),
    teacher_id INT NULL REFERENCES teachers(id),
    capacity INT NOT NULL CHECK (capacity > 0),
    semester VARCHAR(30) NOT NULL,
    target_grade_year INT NOT NULL CHECK (target_grade_year BETWEEN 1 AND 8),
    attendance_weight NUMERIC(5,2) NOT NULL DEFAULT 10.0,
    experiment_weight NUMERIC(5,2) NOT NULL DEFAULT 30.0,
    exam_weight NUMERIC(5,2) NOT NULL DEFAULT 60.0,
    CONSTRAINT weight_total CHECK ((attendance_weight + experiment_weight + exam_weight) = 100.00),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. 选课记录表
CREATE TABLE IF NOT EXISTS enrollments (
    id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(id),
    course_id INT NOT NULL REFERENCES courses(id),
    status VARCHAR(20) NOT NULL CHECK (status IN ('enrolled','dropped')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, course_id)
);

-- 7. 成绩表
CREATE TABLE IF NOT EXISTS grades (
    id SERIAL PRIMARY KEY,
    enrollment_id INT NOT NULL UNIQUE REFERENCES enrollments(id),
    teacher_id INT NULL REFERENCES teachers(id),
    attendance_score NUMERIC(5,2) NOT NULL CHECK (attendance_score BETWEEN 0 AND 100),
    experiment_score NUMERIC(5,2) NOT NULL CHECK (experiment_score BETWEEN 0 AND 100),
    exam_score NUMERIC(5,2) NOT NULL CHECK (exam_score BETWEEN 0 AND 100),
    score NUMERIC(5,2) NOT NULL,
    remarks TEXT NULL,
    graded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. 操作审计日志表（核心表，所有操作自动入库）
CREATE TABLE IF NOT EXISTS operation_log (
    id SERIAL PRIMARY KEY,
    operator_username VARCHAR(50) NOT NULL,
    operator_role VARCHAR(20) NOT NULL,
    operate_type VARCHAR(50) NOT NULL,
    operate_content TEXT NOT NULL,
    target_type VARCHAR(30),
    target_id INT,
    operate_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    client_ip VARCHAR(50)
);

-- 测试管理员账号 密码 Admin@123
INSERT INTO users(username,password_hash,role_id,is_active)
VALUES (
    'admin',
    '240be518fabd2724bfb5f231c5d8da0905d3adf8fe6eed12e17a317f186148',
    (SELECT id FROM roles WHERE role_name='admin'),
    TRUE
) ON CONFLICT(username) DO NOTHING;
```

## 十、测试账号信息
| 用户名          | 密码        | 角色                | 说明                     |
|-----------------|-------------|---------------------|--------------------------|
| admin_demo      | admin123    | 管理员              | 系统全权限管理           |
| teacher_demo    | teacher123  | 教师                | 课程/成绩管理            |
| student_demo    | student123  | 学生                | 基础学生账号             |
| grade1_demo     | student123  | 学生                | 一年级学生               |
| grade2_mid_demo | student123  | 学生                | 二年级（中等成绩）       |
| grade2_risk_demo| student123  | 学生                | 二年级（成绩风险）       |

## 十一、常见报错排查
1. **数据库连接失败**
   - 检查WSL窗口中`gs_ctl start`是否正常运行
   - 核对PowerShell环境变量中的端口、账号、密码是否正确
   - 确认openGauss已执行`ALTER SYSTEM SET listen_addresses = '*'`并重启

2. **人脸功能报错**
   - 关闭其他占用摄像头的软件，重装opencv、insightface依赖
   - 检查`face_data/embeddings`文件夹是否存在

3. **页面背景空白**
   - 检查static目录是否包含指定的背景图和公章图片

4. **操作日志报错`relation operation_log not exist`**
   - 执行`python scripts/init_db.py`脚本，或手动运行完整建表SQL

5. **批量导入失败**
   - 确保Excel表头严格匹配系统要求，分数范围0-100，课程权重合计100%
