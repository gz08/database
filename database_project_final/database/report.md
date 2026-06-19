# 学生管理系统报告

## 1. 核心数据表字段

### ROLES

- id (PK)
- role_name (UK)

### USERS

- id (PK)
- username (UK)
- password_hash
- role_id (FK)
- is_active
- created_at
- updated_at

### STUDENTS

- id (PK)
- user_id (FK)
- student_no (UK)
- full_name
- gender
- grade_year
- major
- phone
- email

### TEACHERS

- id (PK)
- user_id (FK)
- teacher_no (UK)
- full_name
- department
- phone
- email

### COURSES

- id (PK)
- course_code (UK)
- course_name
- credits
- teacher_id (FK)
- capacity
- semester

### ENROLLMENTS

- id (PK)
- student_id (FK)
- course_id (FK)
- status
- enrolled_at

### GRADES

- id (PK)
- enrollment_id (FK)
- teacher_id (FK)
- score
- remarks
- graded_at

## 2. 角色权限说明

### admin（系统管理员）

- 管理账号
- 分配角色
- 重置密码
- 启用/禁用账号
- 查看全局数据
- 负责学生信息新增/删除/修改

### teacher（教师/教务）

- 仅查看学生信息（不提供学生信息 CRUD）
- 查看选课信息
- 管理课程
- 录入与修改成绩

### student（学生）

- 查看个人信息
- 查看课程
- 选课/退课
- 查看个人成绩

## 3. ER 图文字描述（无符号）

1. 系统有 7 个核心实体（表）：roles、users、students、teachers、courses、enrollments、grades。
2. roles 用来定义角色类型，包含 admin、teacher、student。
3. users 是统一账号表，每个用户都必须关联一个角色；一个角色可以被多个用户使用。
4. students 是学生业务信息表，每条学生记录必须对应一个用户账号；一个用户最多对应一条学生记录。
5. teachers 是教师业务信息表，每条教师记录必须对应一个用户账号；一个用户最多对应一条教师记录。
6. courses 是课程表，一门课程可以指定一位教师，也可以暂时不指定教师；一位教师可以负责多门课程。
7. enrollments 是选课关系表，每条记录表示某个学生选择了某门课程；一个学生可以有多条选课记录，一门课程也可以被多个学生选择。
8. enrollments 里限制同一学生和同一课程只能有一条选课关系，用于防止重复选课。
9. grades 是成绩表，每条成绩必须对应一条选课记录；一条选课记录最多对应一条成绩。
10. grades 还可以记录是哪位教师录入的成绩；一位教师可以录入多条成绩。
11. admin 在这个模型里是角色，不是单独实体表；管理员账号存放在 users 中，通过 role_id 指向 roles 里的 admin。
