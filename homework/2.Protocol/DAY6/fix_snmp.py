#!/usr/bin/env python3
"""
使用paramiko交互式配置SNMP
"""
import paramiko
import time

def config_snmp_interactive():
    """交互式配置SNMP"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("连接路由器 10.10.1.200...")
        ssh.connect('10.10.1.200', username='admin', password='Cisc0123', 
                   timeout=10, look_for_keys=False, allow_agent=False)
        
        # 创建交互式shell
        shell = ssh.invoke_shell()
        time.sleep(1)
        
        # 清空缓冲区
        if shell.recv_ready():
            shell.recv(65535)
        
        # 发送命令
        commands = [
            'enable',
            'Cisc0123',
            'configure terminal',
            'snmp-server community qytangro RO',
            'snmp-server community qytangrw RW',
            'end',
            'write memory',
            'show running-config | include snmp-server'
        ]
        
        for cmd in commands:
            print(f"\n>>> {cmd}")
            shell.send(cmd + '\n')
            time.sleep(3)
            
            # 读取输出
            output = ''
            while shell.recv_ready():
                chunk = shell.recv(65535).decode('utf-8', errors='ignore')
                output += chunk
                time.sleep(0.5)
            
            # 打印最后200个字符
            if output:
                print(output[-300:])
        
        print("\n配置完成！")
        
    except Exception as e:
        print(f"错误: {e}")
    finally:
        ssh.close()

if __name__ == '__main__':
    config_snmp_interactive()
