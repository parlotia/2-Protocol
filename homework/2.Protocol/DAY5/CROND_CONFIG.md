# DAY5 - Crond 调度 SNMP 采集配置说明

## 配置步骤

### 1. 编辑 Crontab

```bash
# 使用 root 用户编辑
sudo vim /etc/crontab
```

### 2. 添加定时任务

在文件末尾添加以下行（每分钟执行一次）：

```bash
# 每分钟执行SNMP采集，写入InfluxDB
* * * * * root /usr/bin/python3 /netdevops/homework/2.Protocol/DAY5/write_influxdb.py >> /tmp/snmp_influx.log 2>&1
```

### 3. 重启 Crond 服务

```bash
sudo systemctl restart crond
```

### 4. 验证配置

```bash
# 查看 crontab 配置
cat /etc/crontab | grep write_influxdb

# 查看执行日志
tail -f /var/log/cron

# 查看脚本输出日志
tail -f /tmp/snmp_influx.log
```

## 脚本说明

### 关键配置

1. **Python 模块路径**（已添加到脚本中）：
   ```python
   BASE_DIR = Path(__file__).resolve().parent.parent / 'DAY4'
   sys.path.insert(0, str(BASE_DIR))
   ```

2. **InfluxDB 连接信息**：
   - 主机: localhost
   - 端口: 8086
   - 数据库: qytdb
   - 用户: qytdbuser
   - 密码: Cisc0123

3. **采集设备**：
   - 10.10.1.200 (qytangro)
   - 10.10.1.201 (qytangro)

### 数据格式

写入 InfluxDB 的数据：
- **measurement**: `router_monitor`
- **tags**: 
  - `device_ip`: 设备IP
- **fields**:
  - `cpu_percent`: CPU利用率
  - `mem_use`: 已用内存(字节)
  - `mem_free`: 空闲内存(字节)
  - `mem_percent`: 内存利用率(%)

## 测试方法

### 手动执行测试

```bash
cd /netdevops/homework/2.Protocol/DAY5
python3 write_influxdb.py
```

### 查看采集结果

```bash
# 查看日志
tail -f /tmp/snmp_influx.log

# 查询InfluxDB数据（需要先启动InfluxDB容器）
docker exec -it qyt-influx influx -database qytdb -username qytdbuser -password Cisc0123 -execute "SELECT * FROM router_monitor ORDER BY time DESC LIMIT 10"
```

## 常见问题

### 1. 权限问题
确保脚本有执行权限：
```bash
chmod +x /netdevops/homework/2.Protocol/DAY5/write_influxdb.py
```

### 2. Python 路径问题
如果 Crond 找不到 Python，使用完整路径：
```bash
which python3
# 输出: /usr/bin/python3
```

### 3. InfluxDB 未启动
确保 InfluxDB 容器正在运行：
```bash
cd /netdevops/homework/2.Protocol/DAY5
docker compose -f influxdb_grafana.yml up -d qyt-influx
docker ps | grep influx
```

### 4. SNMP 采集失败
- 检查路由器是否可达
- 检查 SNMP community 是否正确
- 检查防火墙设置

## 停止定时任务

```bash
# 编辑 crontab，删除或注释掉相关行
sudo vim /etc/crontab

# 重启服务
sudo systemctl restart crond
```
