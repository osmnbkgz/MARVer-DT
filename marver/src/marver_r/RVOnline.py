from PyQt5.QtWidgets import *
from src.marver_r.GuiLog import GuiLog
from src.marver_r.GuiConfig import GuiConfig
from bin.UI_MARVer import Ui_MainWindow
from include.marver_r.Exceptions import *
import os, json, signal
import subprocess
from threading import Thread
import re

counter = 0
deneme = str()
parameters = str()


class RVOnline():
    def __init__(self, ui: Ui_MainWindow = None, logger: GuiLog = None):
        self.__ui = ui
        self.__logger = logger
        self.__pIds = []
        self.messageCounter = 0

    def runCommand(self, command, type: bool = False) -> bool:
        global messageCounter, counter, deneme, parameters
        process = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True, text=True, preexec_fn=os.setsid)
        self.__pIds.append(process.pid)
        message = {}
        colorTh = Thread(target=self.__logger.changeColor)
        colorTh.start()
        output_lines = []
        while True:
            try:
                output = process.stdout.readline()

                if output == '' and process.poll() is not None:
                    break

                output_lines.append(output)

                if output.strip() == '---':
                    output_string = ''.join(output_lines)
                    output_lines.clear()
                    output_string = output_string.replace("content:", "").replace("\\n", " ").strip().replace("   ",
                                                                                                              " ").replace(
                        "    ", " ")
                    output_string = output_string.replace('"', '').replace("\\", "").replace("\n", " ").replace("---",
                                                                                                                "")
                    property_index = output_string.find("property:")
                    if property_index != -1:
                        output_string = output_string[:property_index]

                    topic_match = re.search(r'topic: (\w+)', output_string)

                    if topic_match:
                        topic = topic_match.group(1)
                        topic_pattern = re.escape("topic: " + topic)
                        output_string = re.sub(topic_pattern, "", output_string)
                        output_string = output_string.strip()
                        output_string = re.sub(r'\s+', ' ', output_string)

                if output and type:
                    if "topic" in output:
                        message["topic"] = output.split(":")[1].strip().replace('"', '')
                    elif "content" in output:
                        message["content"] = output_string
                    elif "time" in output:
                        message["time"] = float(output.replace("time:", "").strip())
                    elif "status" in output:
                        message["status"] = json.loads(output[output.find('{'):output.rfind('}') + 1])
                    elif "---" == output.strip():
                        self.__logger.printMonitorResult(
                            message=f"E >> TIME: {message.get('time', '')}  CONTENT: {message.get('content', '')}",
                            color="red")
                        self.messageCounter += 1
                        print("Message count:", self.messageCounter)
                        self.__logger.setColorTimer()

            except Exception as e:
                print(e)
        rc = process.poll()
        return rc == 0

    def startSocketConnection(self, rv: str = "online", property: str = "property", port: int = 7777,
                              type: str = "discrete"):
        try:
            self.__logger.printLog(message="Socket communication is started successfully", color="blue")
            os.system(
                command=f"~/marver/3rdparty/rosmonitoring/oracle/TLOracle/oracle.py --{rv} --property {property} --port {port} --{type}")
        except Exception:
            self.__logger.printLog(message="An error occurred in startSocketConnection()", color="red")

    def startMonitor(self):
        try:
            self.__logger.printLog(message="The monitor is initialized successfully", color="blue")
            os.system(command="ros2 launch monitor run.launch.py")
        except Exception:
            self.__logger.printLog(message="An error is occurred in startMonitor()", color="red")

    def startInstrumentation(self, pkg: str = "", launchFile: str = ""):
        try:
            self.__logger.printLog(message="The instrumentation is initialized successfully", color="blue")
            os.system(command=f"ros2 launch {pkg} {launchFile}_instrumented.launch.py")
        except Exception:
            self.__logger.printLog(message="An error is occurred in startInstrumentation()", color="red")

    def startLiveStreamLogging(self, monitorName: str = ""):
        try:
            self.__logger.printLog(message="Runtime verification setup is READY", color="black")
            self.__logger.printMonitorResult(message="In case of any violation, an error message will appear ",
                                             color="blue")
            self.runCommand(command=f"ros2 topic echo /{monitorName}/monitor_error", type=True)
        except Exception:
            self.__logger.printLog(message="An error is occurred in startLiveStreamLogging()", color="red")

    def stopAllProcess(self):
        try:
            from src.marver_r.GuiMonitor import configFile
            node_name = str(configFile['nodes'][0]['node']['name'])
            os.system(f"pkill -f {node_name}")

            while self.__pIds:
                try:
                    os.killpg(os.getpgid(self.__pIds.pop()), signal.SIGTERM)
                except ProcessLookupError:
                    pass
            self.__logger.printLog(message="All process are ended successfully", color="blue")
        except Exception as e:
            print(f"Error stopping processes: {e}")