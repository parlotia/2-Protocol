# DAY6 测试步骤文档

## 测试环境准备

### 1. 检查Python环境和依赖

```bash
# 激活虚拟环境
source /netdevops/.venv/bin/activate

# 检查Python版本
python3 --version

# 检查必需的Python包
pip list | grep -E "sqlalchemy|pysnmp|bokeh|numpy|influxdb"

# 如果缺少influxdb，安装它
pip install influxdb
```

### 2. 检查网络设备SNMP配置

```bash
# 测试SNMP连通性（设备IP根据实际情况修改）
snmpwalk -v 2c -c qytangro 10.10.1.200 1.3.6.1.2.1.1.1.0

# 应该返回系统描述信息
# 如果失败，检查：
# 1. 设备IP是否正确
# 2. SNMP团体字是否正确
# 3. 网络是否可达
# 4. 设备是否启用了SNMP
```

### 3. 检查Docker环境

```bash
# 检查Docker是否运行
systemctl status docker

# 检查docker-compose是否安装
docker-compose --version
```

---

## 第一阶段：数据库创建测试

### 测试1.1：创建SQLite数据库

```bash
cd /netdevops/homework/2.Protocol/DAY6/code

# 运行数据库创建脚本
python3 day6_1_create_db.py
```

**预期输出：**
```
[+] 数据库创建成功: /netdevops/homework/2.Protocol/DAY6/code/sqlalchemy_interface_sqlite3.db
```

**验证步骤：**
```bash
# 检查数据库文件是否生成
ls -lh sqlalchemy_interface_sqlite3.db

# 使用Python验证表结构
python3 << 'EOF'
from day6_1_create_db import InternfaceMonitor, engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"数据库表: {tables}")

if 'interface_monitor' in tables:
    columns = inspector.get_columns('interface_monitor')
    print("\ninterface_monitor 表结构:")
    for col in columns:
        print(f"  - {col['name']}: {col['type']}")
    print("\n✅ 数据库表创建成功")
else:
    print("\n❌ 数据库表创建失败")
EOF
```

---

## 第二阶段：SNMP采集测试

### 测试2.1：手动运行SNMP采集（SQLite）

```bash
cd /netdevops/homework/2.Protocol/DAY6/code

# 运行采集脚本
python3 day6_2_write_sqlite.py
```

**预期输出：**
```
======================================================================
SNMP接口数据采集开始 - 2026-04-20 10:30:00
======================================================================
[+] 10.10.1.200 GigabitEthernet1               IN=  3094684762  OUT=   143150469
[+] 10.10.1.200 GigabitEthernet2               IN=    19457420  OUT=    12672982
[+] 10.10.1.201 GigabitEthernet1               IN=  2495193047  OUT=     1225680
[*] 共写入 6 条记录
======================================================================
```

**可能的问题：**

❌ **问题1：SNMP连接超时**
```
[!] 10.10.1.200 采集失败: SNMP Error: No response from remote host
```
**解决方案：**
- 检查设备IP和团体字配置
- 检查防火墙是否放行UDP 161端口
- 确认设备SNMP服务已启用

❌ **问题2：没有采集到接口数据**
```
[!] 没有采集到数据
```
**解决方案：**
- 检查设备是否有UP状态的接口
- 使用snmpwalk手动测试OID

**验证数据写入：**
```bash
python3 << 'EOF'
from day6_1_create_db import InternfaceMonitor, engine
from sqlalchemy.orm import sessionmaker

Session = sessionmaker(bind=engine)
session = Session()

# 查询所有记录
records = session.query(InternfaceMonitor).all()
print(f"数据库中共有 {len(records)} 条记录\n")

# 显示最近的5条记录
recent = session.query(InternfaceMonitor).order_by(
    InternfaceMonitor.record_datetime.desc()
).limit(5).all()

print("最近5条记录:")
for r in recent:
    print(f"  {r.device_ip} | {r.interface_name} | "
          f"IN={r.in_bytes} | OUT={r.out_bytes} | "
          f"{r.record_datetime}")

session.close()
EOF
```

### 测试2.2：测试SNMP GETBULK工具

```bash
cd /netdevops/homework/2.Protocol/DAY6/code

# 运行SNMP GETBULK测试
python3 -m tools.day6_snmp_getbulk
```

**预期输出：**
```
=== 测试SNMP GETBULK采集接口数据 ===
获取接口名称 (ifDescr):
  1.3.6.1.2.1.2.2.1.2.1 = GigabitEthernet0/0
  1.3.6.1.2.1.2.2.1.2.2 = GigabitEthernet0/1
  ...
```

---

## 第三阶段：Bokeh可视化测试

### 测试3.1：生成Bokeh图表

**前提条件：** 数据库中至少有10分钟的数据（至少2个时间点）

```bash
cd /netdevops/homework/2.Protocol/DAY6/code

# 方法1：等待Crond运行10分钟后
python3 day6_3_show_sqlite.py

# 方法2：手动插入测试数据（用于快速测试）
python3 << 'EOF'
from day6_1_create_db import InternfaceMonitor, engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import random

Session = sessionmaker(bind=engine)
session = Session()

# 生成10分钟的模拟数据（每分钟一条）
base_time = datetime.now() - timedelta(minutes=10)
devices = [
    ('10.10.1.200', 'GigabitEthernet1'),
    ('10.10.1.201', 'GigabitEthernet1')
]

for device_ip, iface in devices:
    in_bytes = 1000000000
    out_bytes = 500000000
    
    for i in range(11):  # 11个时间点
        record = InternfaceMonitor(
            device_ip=device_ip,
            interface_name=iface,
            in_bytes=in_bytes + random.randint(100000, 500000) * i,
            out_bytes=out_bytes + random.randint(50000, 200000) * i,
            record_datetime=base_time + timedelta(minutes=i)
        )
        session.add(record)

session.commit()
print(f"[+] 已插入 {len(devices) * 11} 条测试数据")
session.close()
EOF

# 然后生成图表
python3 day6_3_show_sqlite.py
```

**预期输出：**
```
======================================================================
接口速率分析 - 2026-04-20 10:45:00
======================================================================
[*] 10.10.1.200:GigabitEthernet1: 10 个有效速率点
[*] 10.10.1.201:GigabitEthernet1: 10 个有效速率点
[*] 生成图表: /netdevops/homework/2.Protocol/DAY6/outputs/interface_rx_speed.html
[*] 生成图表: /netdevops/homework/2.Protocol/DAY6/outputs/interface_tx_speed.html
======================================================================
```

**验证图表文件：**
```bash
# 检查生成的HTML文件
ls -lh ../outputs/*.html

# 在浏览器中打开（如果有图形界面）
# 或者复制到本地电脑查看
```

### 测试3.2：测试Bokeh工具函数

```bash
cd /netdevops/homework/2.Protocol/DAY6/code

# 运行Bokeh工具测试
python3 -m tools.day6_bokeh_line
```

**预期：** 自动生成一个测试折线图HTML文件

---

## 第四阶段：InfluxDB集成测试

### 测试4.1：启动Docker容器

```bash
cd /netdevops/homework/2.Protocol/DAY6

# 启动InfluxDB和Grafana
docker-compose up -d

# 检查容器状态
docker-compose ps

# 预期输出：
# NAME                STATUS         PORTS
# day6_qyt-influx_1   Up (healthy)   0.0.0.0:8086->8086/tcp
# day6_qyt-grafana_1  Up             0.0.0.0:3000->3000/tcp
```

**查看日志：**
```bash
# 查看InfluxDB日志
docker-compose logs qyt-influx

# 查看Grafana日志
docker-compose logs qyt-grafana
```

### 测试4.2：验证InfluxDB服务

```bash
# 检查InfluxDB HTTP API
curl http://localhost:8086/ping

# 应该返回 204 No Content

# 检查数据库是否创建
curl -G http://localhost:8086/query --data-urlencode "q=SHOW DATABASES" \
  -u admin:Cisc0123

# 预期输出包含 "qytdb"
```

### 测试4.3：手动写入InfluxDB

```bash
cd /netdevops/homework/2.Protocol/DAY6/code

# 运行InfluxDB写入脚本
python3 day6_4_write_influxdb.py
```

**预期输出：**
```
======================================================================
SNMP接口数据采集(InfluxDB) - 2026-04-20 11:00:00
======================================================================
[+] 10.10.1.200 GigabitEthernet1               IN=  3094684762  OUT=   143150469
[+] 10.10.1.200 GigabitEthernet2               IN=    19457420  OUT=    12672982
[+] 10.10.1.201 GigabitEthernet1               IN=  2495193047  OUT=     1225680
[*] 成功写入 6 条数据到 InfluxDB
======================================================================
```

**验证数据：**
```bash
# 查询InfluxDB中的数据
curl -G http://localhost:8086/query --data-urlencode "q=SELECT * FROM interface_monitor LIMIT 5" \
  -u qytdbuser:Cisc0123 -database qytdb

# 应该返回JSON格式的查询结果
```

---

## 第五阶段：Grafana Dashboard测试

### 测试5.1：访问Grafana

1. 打开浏览器访问：`http://localhost:3000`
2. 首次登录：
   - 用户名：`admin`
   - 密码：`admin`
   - 系统会提示修改密码（可跳过或设置为 `Cisc0123`）

### 测试5.2：配置InfluxDB数据源

1. 点击左侧菜单 ⚙️ **Configuration** → **Data Sources**
2. 点击 **Add data source**
3. 选择 **InfluxDB**
4. 配置参数：
   ```
   Name: InfluxDB
   URL: http://qyt-influx:8086
   Database: qytdb
   User: qytdbuser
   Password: Cisc0123
   ```
5. 点击 **Save & Test**
6. **预期：** 显示绿色提示 "Data source is working"

### 测试5.3：导入Dashboard

**方法1：使用JSON文件导入**
1. 点击左侧 ➕ **Create** → **Import**
2. 点击 **Upload .json file**
3. 选择 `/netdevops/homework/2.Protocol/DAY6/Dashboard_Speed.json`
4. 在底部选择数据源：**InfluxDB**
5. 点击 **Import**
6. **预期：** 显示两个图表面板（RX和TX）

**方法2：手动创建面板**
1. 点击 ➕ **Create** → **Dashboard** → **Add new panel**
2. 配置Query：
   ```sql
   SELECT non_negative_derivative(mean("in_bytes"), 1s) * 8 
   FROM "interface_monitor" 
   WHERE $timeFilter 
   GROUP BY time($__interval), "device_ip", "interface_name"
   ```
3. 设置：
   - Alias: `[[tag_device_ip]]--[[tag_interface_name]]`
   - Unit: `bits/sec(SI)`
   - Title: `接口入向速率 (RX)`
4. 点击 **Apply**
5. 重复创建出向速率面板

### 测试5.4：验证Dashboard显示

1. **时间范围设置：** 右上角选择 `Last 15 minutes` 或 `Last 1 hour`
2. **刷新间隔：** 设置为 `5s` 或 `10s`（自动刷新）
3. **预期效果：**
   - 图表显示多条曲线（每个设备每个接口一条）
   - 图例格式：`10.10.1.200--GigabitEthernet1`
   - Y轴单位：bps（bits per second）
   - 鼠标悬停显示详细数值

---

## 第六阶段：Crond定时任务测试

### 测试6.1：配置Crond

```bash
# 编辑crontab
sudo vim /etc/crontab

# 添加以下两行：
# 每分钟执行一次 SNMP 采集写入 SQLite
* * * * * root /netdevops/.venv/bin/python3.11 /netdevops/homework/2.Protocol/DAY6/code/day6_2_write_sqlite.py >> /tmp/day6_sqlite.log 2>&1

# 每分钟执行一次 SNMP 采集写入 InfluxDB
* * * * * root /netdevops/.venv/bin/python3.11 /netdevops/homework/2.Protocol/DAY6/code/day6_4_write_influxdb.py >> /tmp/day6_influx.log 2>&1
```

**保存后重启Crond：**
```bash
sudo systemctl restart crond
sudo systemctl status crond
```

### 测试6.2：验证Crond执行

```bash
# 等待2-3分钟后查看日志
tail -f /tmp/day6_sqlite.log
tail -f /tmp/day6_influx.log

# 应该看到每分钟都有新的采集记录

# 检查日志文件更新时间
ls -lh /tmp/day6_*.log

# 检查crond是否真的在运行
ps aux | grep crond
```

### 测试6.3：验证数据持续写入

```bash
# 等待10分钟后，检查SQLite数据量
cd /netdevops/homework/2.Protocol/DAY6/code
python3 << 'EOF'
from day6_1_create_db import InternfaceMonitor, engine
from sqlalchemy.orm import sessionmaker

Session = sessionmaker(bind=engine)
session = Session()

total = session.query(InternfaceMonitor).count()
print(f"SQLite数据库总记录数: {total}")

# 检查时间分布
from sqlalchemy import func
time_range = session.query(
    func.min(InternfaceMonitor.record_datetime),
    func.max(InternfaceMonitor.record_datetime)
).first()

print(f"最早记录: {time_range[0]}")
print(f"最新记录: {time_range[1]}")

session.close()
EOF

# 检查InfluxDB数据量
curl -G http://localhost:8086/query \
  --data-urlencode "q=SELECT COUNT(*) FROM interface_monitor" \
  -u qytdbuser:Cisc0123 -database qytdb
```

---

## 第七阶段：完整集成测试

### 测试7.1：端到端测试流程

```bash
# 1. 清空数据库重新开始（可选）
cd /netdevops/homework/2.Protocol/DAY6/code
python3 day6_1_create_db.py

# 2. 重启Docker容器
cd ..
docker-compose restart

# 3. 确保Crond正在运行
sudo systemctl status crond

# 4. 等待15分钟让系统收集数据

# 5. 生成Bokeh图表
cd code
python3 day6_3_show_sqlite.py

# 6. 检查Grafana Dashboard
# 访问 http://localhost:3000
# 确认图表有数据显示
```

### 测试7.2：性能测试

```bash
# 测试SNMP采集耗时
cd /netdevops/homework/2.Protocol/DAY6/code
time python3 day6_2_write_sqlite.py

# 预期：单次采集应该在5-15秒内完成

# 测试数据库查询性能
time python3 day6_3_show_sqlite.py

# 预期：图表生成应该在3-5秒内完成
```

---

## 故障排查指南

### 问题1：Crond没有执行

```bash
# 检查crond服务状态
sudo systemctl status crond

# 检查crond日志
sudo journalctl -u crond -f

# 检查脚本是否有执行权限
ls -l /netdevops/homework/2.Protocol/DAY6/code/*.py

# 手动测试脚本能否运行
/netdevops/.venv/bin/python3.11 /netdevops/homework/2.Protocol/DAY6/code/day6_2_write_sqlite.py
```

### 问题2：Grafana无法连接InfluxDB

```bash
# 检查容器网络
docker-compose ps

# 测试容器间网络连通性
docker exec day6_qyt-grafana_1 wget -qO- http://qyt-influx:8086/ping

# 检查InfluxDB是否在容器内监听
docker exec day6_qyt-influx_1 influx -execute "SHOW DATABASES" -username admin -password Cisc0123
```

### 问题3：Bokeh图表没有数据

```bash
# 检查数据库中是否有足够的数据点
python3 << 'EOF'
from day6_1_create_db import InternfaceMonitor, engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

Session = sessionmaker(bind=engine)
session = Session()

cutoff = datetime.now() - timedelta(minutes=10)
count = session.query(InternfaceMonitor).filter(
    InternfaceMonitor.record_datetime >= cutoff
).count()

print(f"最近10分钟数据点: {count}")
if count < 2:
    print("❌ 数据点不足，需要等待Crond运行更多次数")
else:
    print("✅ 数据点充足")

session.close()
EOF
```

### 问题4：SNMP采集返回空数据

```bash
# 手动测试SNMP
snmpwalk -v 2c -c qytangro 10.10.1.200 1.3.6.1.2.1.2.2.1.2

# 检查设备接口状态
snmpwalk -v 2c -c qytangro 10.10.1.200 1.3.6.1.2.1.2.2.1.8

# 1 = up, 2 = down

# 如果所有接口都是down，不会有数据返回
```

---

## 测试检查清单

完成以下检查项，确认DAY6作业全部正常：

- [ ] Python依赖包已安装（sqlalchemy, pysnmp, bokeh, numpy, influxdb）
- [ ] SQLite数据库创建成功
- [ ] SNMP采集脚本能正常连接设备
- [ ] SQLite数据写入成功（至少2个设备）
- [ ] 数据库中有10分钟以上的数据
- [ ] Bokeh图表生成成功（RX和TX两个HTML文件）
- [ ] Docker容器正常运行（InfluxDB + Grafana）
- [ ] InfluxDB数据源配置成功
- [ ] Grafana Dashboard导入成功
- [ ] Grafana图表显示实时数据
- [ ] Crond定时任务正常执行
- [ ] 日志文件持续更新

---

## 快速测试命令汇总

```bash
# 一键测试所有组件
cd /netdevops/homework/2.Protocol/DAY6

# 1. 创建数据库
cd code && python3 day6_1_create_db.py && cd ..

# 2. 测试SNMP采集
cd code && python3 day6_2_write_sqlite.py && cd ..

# 3. 启动Docker
docker-compose up -d

# 4. 测试InfluxDB写入
cd code && python3 day6_4_write_influxdb.py && cd ..

# 5. 生成Bokeh图表（需要有10分钟数据）
cd code && python3 day6_3_show_sqlite.py

# 6. 查看所有输出文件
ls -lh outputs/

# 7. 访问Grafana
echo "访问 http://localhost:3000 查看Dashboard"
```

---

## 附录：常用查询命令

```bash
# 查看SQLite表结构
sqlite3 code/sqlalchemy_interface_sqlite3.db ".schema interface_monitor"

# 查看SQLite数据
sqlite3 code/sqlalchemy_interface_sqlite3.db "SELECT * FROM interface_monitor ORDER BY record_datetime DESC LIMIT 10;"

# 查看InfluxDB测量
curl -G http://localhost:8086/query --data-urlencode "q=SHOW MEASUREMENTS" \
  -u qytdbuser:Cisc0123 -database qytdb

# 查看InfluxDB tag keys
curl -G http://localhost:8086/query --data-urlencode "q=SHOW TAG KEYS FROM interface_monitor" \
  -u qytdbuser:Cisc0123 -database qytdb

# 查看InfluxDB field keys
curl -G http://localhost:8086/query --data-urlencode "q=SHOW FIELD KEYS FROM interface_monitor" \
  -u qytdbuser:Cisc0123 -database qytdb
```
