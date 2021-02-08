import paramiko
import time
#pylint:disable=unused-variable

class ConfigCisco:

  def __init__(self, hostname, username, password, command="show cdp neighbor | begin Device"):
    self.hostname = hostname
    self.username = username
    self.password = password
    self.command = command

  def show_cmd_ssh(self):
    try:
      conn = paramiko.SSHClient()
      conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      conn.connect(hostname=self.hostname, username=self.username, password=self.password, allow_agent=False, look_for_keys=False)
      stdin, stdout, stderr = conn.exec_command(self.command)
      stdout = stdout.readlines()
      return stdout
    except paramiko.ssh_exception.AuthenticationException:
      return False
    except paramiko.ssh_exception.NoValidConnectionsError:
      return False

  def create_device_dict(self, results):
    """ Takes unformatted output of show cdp neighbor
    and returns a dictionary in format {remote_device: [local_port, remote_port]}.
    This can be used to configure interface descriptions later."""

    updated_results = []
    devices = {}
    for result in results:
      # get rid of extra spacing and carriage returns
      updated_results.append(result.strip(' ').strip('\n').strip('\r'))

    # get rid of output table header
    updated_results.pop(0)

    # add devices to devices dictionary
    for num in range(len(updated_results)-2):
      if num % 2 == 0:
        devices[updated_results[num]] = [updated_results[num+1][:10], updated_results[num+1][-10:]]

    return devices
  
  def configure_interfaces(self, device_dict):
    try:
      conn = paramiko.SSHClient()
      conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
      conn.connect(hostname=self.hostname, username=self.username, password=self.password, allow_agent=False, look_for_keys=False)
    except paramiko.ssh_exception.AuthenticationException:
      return False
    except paramiko.ssh_exception.NoValidConnectionsError:
      return False

    rtcon = conn.invoke_shell()
    time.sleep(1)

    list_of_commands = ["terminal length 0", "configure terminal"]
    for data in device_dict.keys():
      list_of_commands.append(f"interface {device_dict[data][0]}")
      list_of_commands.append(f"description connected to {data} on {device_dict[data][1]}")
      list_of_commands.append("write mem")
    
    for command in list_of_commands:
      rtcon.send(command + '\n')
      time.sleep(1)

config_class = ConfigCisco("200.0.0.1", "nms", "cisco")

results = config_class.show_cmd_ssh()

if results:
  device_dict = config_class.create_device_dict(results)
  config_class.configure_interfaces(device_dict)
else:
  print("Check connection to device and re-try!")