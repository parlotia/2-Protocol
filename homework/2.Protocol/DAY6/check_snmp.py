#!/usr/bin/env python3
"""
SSH登录路由器检查SNMP配置
"""
import paramiko

def check_snmp_config(host, username, password):
    """检查路由器SNMP配置"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # 建立SSH连接
        print(f"[+] 正在连接 {host}...")
        ssh.connect(
            hostname=host,
            username=username,
            password=password,
            timeout=10,
            look_for_keys=False,
            allow_agent=False
        )
        print(f"[+] 连接成功！")
        
        # 执行查看SNMP配置命令
        commands = [
            'show running-config | include snmp-server',
            'show snmp community',
            'show ip interface brief'
        ]
        
        for cmd in commands:
            print(f"\n{'='*60}")
            print(f"命令: {cmd}")
            print(f"{'='*60}")
            
            stdin, stdout, stderr = ssh.exec_command(cmd)
            output = stdout.read().decode('utf-8', errors='ignore')
            print(output)
        
        return True
        
    except Exception as e:
        print(f"[!] 连接失败: {e}")
        return False
    
    finally:
        ssh.close()


def configure_snmp(host, username, password):
    """配置路由器SNMP"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"\n[+] 正在连接 {host} 配置SNMP...")
        ssh.connect(
            hostname=host,
            username=username,
            password=password,
            timeout=10,
            look_for_keys=False,
            allow_agent=False
        )
        
        # 使用invoke_shell进行配置
        chan = ssh.invoke_shell()
        
        # 等待提示符
        import time
        time.sleep(1)
        output = chan.recv(65535).decode('utf-8', errors='ignore')
        print(output)
        
        # 发送配置命令
        snmp_commands = [
            'configure terminal',
            'snmp-server community qytangro RO',
            'snmp-server community qytangrw RW',
            'end',
            'write memory',
            'show running-config | include snmp-server community'
        ]
        
        for cmd in snmp_commands:
            print(f"\n[+] 发送命令: {cmd}")
            chan.send(cmd + '\n')
            time.sleep(2)
            output = chan.recv(65535).decode('utf-8', errors='ignore')
            print(output)
        
        print(f"\n[+] SNMP配置完成！")
        return True
        
    except Exception as e:
        print(f"[!] 配置失败: {e}")
        return False
    
    finally:
        ssh.close()


if __name__ == "__main__":
    ROUTER_IP = '10.10.1.200'
    USERNAME = 'admin'
    PASSWORD = 'Cisc0123'
    
    # 先检查当前配置
    print("=" * 60)
    print("检查路由器SNMP配置")
    print("=" * 60)
    check_snmp_config(ROUTER_IP, USERNAME, PASSWORD)
    
    # 询问是否需要配置
    print("\n" + "=" * 60)
    response = input("是否需要配置SNMP? (y/n): ").strip().lower()
    
    if response == 'y':
        configure_snmp(ROUTER_IP, USERNAME, PASSWORD)
        
        # 配置第二台路由器
        ROUTER_IP2 = '10.10.1.201'
        print(f"\n\n{'='*60}")
        print(f"配置第二台路由器 {ROUTER_IP2}")
        print(f"{'='*60}")
        response2 = input(f"是否配置 {ROUTER_IP2}? (y/n): ").strip().lower()
        if response2 == 'y':
            configure_snmp(ROUTER_IP2, USERNAME, PASSWORD)
