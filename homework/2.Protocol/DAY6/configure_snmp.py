#!/usr/bin/env python3
"""
自动配置路由器SNMP
"""
import paramiko
import time

def configure_snmp(host, username, password):
    """配置路由器SNMP"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"\n{'='*60}")
        print(f"正在配置路由器: {host}")
        print(f"{'='*60}")
        
        # 建立SSH连接
        ssh.connect(
            hostname=host,
            username=username,
            password=password,
            timeout=10,
            look_for_keys=False,
            allow_agent=False
        )
        print(f"[+] SSH连接成功")
        
        # 使用invoke_shell进行交互式配置
        chan = ssh.invoke_shell()
        time.sleep(1)
        
        # 清空初始输出
        if chan.recv_ready():
            chan.recv(65535)
        
        # SNMP配置命令列表
        commands = [
            ('enable', 'Password:'),
            ('Cisc0123', '#'),
            ('configure terminal', '(config)#'),
            ('snmp-server community qytangro RO', '(config)#'),
            ('snmp-server community qytangrw RW', '(config)#'),
            ('snmp-server location Beijing', '(config)#'),
            ('snmp-server contact Admin', '(config)#'),
            ('end', '#'),
            ('write memory', '#'),
        ]
        
        for cmd, expect in commands:
            print(f"[+] 发送: {cmd}")
            chan.send(cmd + '\n')
            time.sleep(2)
            
            # 读取输出
            output = ''
            while chan.recv_ready():
                output += chan.recv(65535).decode('utf-8', errors='ignore')
                time.sleep(0.5)
            
            if output:
                print(f"    响应: {output[-100:]}")  # 只显示最后100字符
        
        # 验证配置
        print(f"\n[+] 验证SNMP配置...")
        chan.send('show running-config | include snmp-server community\n')
        time.sleep(2)
        
        output = ''
        while chan.recv_ready():
            output += chan.recv(65535).decode('utf-8', errors='ignore')
            time.sleep(0.5)
        
        print(output)
        
        print(f"\n[+] {host} SNMP配置完成！")
        return True
        
    except Exception as e:
        print(f"[!] 配置失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        ssh.close()


if __name__ == "__main__":
    # 配置两台路由器
    routers = [
        {'ip': '10.10.1.200', 'username': 'admin', 'password': 'Cisc0123'},
        {'ip': '10.10.1.201', 'username': 'admin', 'password': 'Cisc0123'},
    ]
    
    for router in routers:
        configure_snmp(router['ip'], router['username'], router['password'])
        time.sleep(1)
    
    print("\n" + "="*60)
    print("所有路由器SNMP配置完成！")
    print("="*60)
